# backend/app/services/actions.py

import asyncio
import json
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from ..models.action_log import ActionLog
from ..models.account_limit import AccountLimit
from ..models.profile import Profile

import websockets  # make sure 'websockets' is in requirements.txt



# -------------------- Limits / defaults --------------------

DEFAULT_LIMITS = {
    "follow": {"per_hour": 20, "per_day": 100, "warmup": True},
    "unfollow": {"per_hour": 20, "per_day": 100},
    "like": {"per_hour": 60, "per_day": 400},
    "dm": {"per_hour": 10, "per_day": 50},
    "random_delay_ms": [800, 3000],
    "block_cooldown_minutes": 60,
}


def _now():
    return datetime.now(timezone.utc)


def get_account_limits(db: Session, account_id: int) -> Dict[str, Any]:
    row = db.execute(
        select(AccountLimit).where(AccountLimit.account_id == account_id)
    ).scalar_one_or_none()
    if row and row.limits_json:
        return {**DEFAULT_LIMITS, **row.limits_json}
    return DEFAULT_LIMITS.copy()


def ensure_profile_ws(db: Session, profile_id: int) -> str:
    """
    Pull a usable CDP websocket URL from the profile.
    Prefers last_ws_puppeteer; falls back to ws_url or ws{puppeteer,selenium}.
    """
    profile: Optional[Profile] = db.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="profile not found")

    ws_url = getattr(profile, "last_ws_puppeteer", None)
    if not ws_url and getattr(profile, "ws_url", None):
        ws_url = profile.ws_url
    if not ws_url and getattr(profile, "ws", None):
        if isinstance(profile.ws, dict):
            ws_url = profile.ws.get("puppeteer") or profile.ws.get("selenium")
        elif isinstance(profile.ws, str):
            ws_url = profile.ws

    if not ws_url:
        raise HTTPException(status_code=400, detail="profile has no active websocket url; open it first")

    return ws_url


def _count_actions_in_window(db: Session, account_id: int, action_type: str, since: datetime) -> int:
    q = select(ActionLog).where(
        and_(
            ActionLog.account_id == account_id,
            ActionLog.action_type == action_type,
            ActionLog.created_at >= since,
            ActionLog.status.in_(["running", "success"]),
        )
    )
    return len(db.execute(q).scalars().all())


def rate_limit_guard(db: Session, account_id: int, action_type: str, limits: Dict[str, Any]) -> None:
    per_hour = limits.get(action_type, {}).get("per_hour")
    per_day = limits.get(action_type, {}).get("per_day")

    now = _now()
    if per_hour:
        hour_count = _count_actions_in_window(db, account_id, action_type, now - timedelta(hours=1))
        if hour_count >= per_hour:
            raise HTTPException(status_code=429, detail=f"rate_limited_hour for {action_type}")

    if per_day:
        day_count = _count_actions_in_window(db, account_id, action_type, now - timedelta(days=1))
        if day_count >= per_day:
            raise HTTPException(status_code=429, detail=f"rate_limited_day for {action_type}")


async def random_delay(limits: Dict[str, Any]):
    lo, hi = limits.get("random_delay_ms", [800, 3000])
    ms = random.randint(int(lo), int(hi))
    await asyncio.sleep(ms / 1000.0)


# -------------------- Raw CDP client --------------------

class CDPClient:
    """
    Minimal CDP client for a single page session (good enough for follow/like/DM MVP).
    Connects to AdsPower SunBrowser's DevTools WS (CDP).
    """

    def __init__(self, ws_url: str, timeout: float = 25.0):
        self.ws_url = ws_url
        self.timeout = timeout
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._id = 0

    async def __aenter__(self):
        self._ws = await websockets.connect(self.ws_url, max_size=None)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass

    async def _send(self, method: str, params: Optional[dict] = None, session_id: Optional[str] = None) -> int:
        """Send a CDP command and return the message id."""
        self._id += 1
        msg: Dict[str, Any] = {"id": self._id, "method": method}
        if params:
            msg["params"] = params
        if session_id:
            msg["sessionId"] = session_id
        assert self._ws is not None
        await self._ws.send(json.dumps(msg))
        return self._id

    async def _recv_until_id(self, wanted_id: int, timeout: Optional[float] = None) -> dict:
        """Receive frames until we find result/error for the given id."""
        deadline = asyncio.get_event_loop().time() + (timeout or self.timeout)
        while True:
            remaining = deadline - asyncio.get_event_loop().time()
            if remaining <= 0:
                raise TimeoutError(f"Timed out waiting for id={wanted_id}")
            assert self._ws is not None
            raw = await asyncio.wait_for(self._ws.recv(), timeout=remaining)
            data = json.loads(raw)
            if isinstance(data, dict) and data.get("id") == wanted_id:
                if "error" in data:
                    raise RuntimeError(f"CDP error: {data['error']}")
                return data.get("result", {})

    async def _wait_event(self, method: str, session_id: str, timeout: Optional[float] = None) -> dict:
        """Wait for a specific event method on the given session."""
        deadline = asyncio.get_event_loop().time() + (timeout or self.timeout)
        while True:
            remaining = deadline - asyncio.get_event_loop().time()
            if remaining <= 0:
                raise TimeoutError(f"Timed out waiting for event {method}")
            assert self._ws is not None
            raw = await asyncio.wait_for(self._ws.recv(), timeout=remaining)
            data = json.loads(raw)
            if data.get("method") == method and data.get("sessionId") == session_id:
                return data.get("params", {})

    # ----- High-level helpers -----

    async def get_page_session(self) -> str:
        """
        Attach to the first 'page' target and enable Page events.
        Returns the sessionId (CDP session).
        """
        msg_id = await self._send("Target.getTargets")
        res = await self._recv_until_id(msg_id)
        targets = res.get("targetInfos") or []
        if not targets:
            # ensure discovery, then retry
            await self._send("Target.setDiscoverTargets", {"discover": True})
            await asyncio.sleep(0.3)
            msg_id = await self._send("Target.getTargets")
            res = await self._recv_until_id(msg_id)
            targets = res.get("targetInfos") or []

        page = next((t for t in targets if t.get("type") == "page"), None)
        if not page:
            raise RuntimeError("No page target found")

        msg_id = await self._send("Target.attachToTarget", {"targetId": page["targetId"], "flatten": True})
        res = await self._recv_until_id(msg_id)
        session_id = res["sessionId"]

        # Enable Page domain to receive events
        await self._recv_until_id(await self._send("Page.enable", session_id=session_id))
        return session_id

    async def goto(self, session_id: str, url: str, wait: str = "domcontent") -> None:
        await self._recv_until_id(await self._send("Page.navigate", {"url": url}, session_id=session_id))
        if wait == "load":
            await self._wait_event("Page.loadEventFired", session_id=session_id, timeout=20)
        else:
            await self._wait_event("Page.domContentEventFired", session_id=session_id, timeout=20)

    async def eval(self, session_id: str, expression: str) -> Any:
        msg_id = await self._send(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": False},
            session_id=session_id,
        )
        res = await self._recv_until_id(msg_id)
        return (res.get("result") or {}).get("value")

    async def click_follow_button(self, session_id: str) -> str:
        """
        Click the first button whose text contains 'Follow' (case-insensitive).
        Returns 'clicked' | 'notfound'.
        """
        expr = r"""
        (function () {
          const btn = Array.from(document.querySelectorAll('button'))
            .find(b => /follow/i.test(((b.innerText||'') + ' ' + (b.textContent||''))));
          if (!btn) return 'notfound';
          btn.click();
          return 'clicked';
        })();
        """
        val = await self.eval(session_id, expr)
        return val or "unknown"


# -------------------- Action executors (CDP) --------------------

async def perform_follow(ws_url: str, usernames: List[str]) -> Dict[str, Any]:
    """
    Navigate to each profile and click 'Follow' via CDP/JS.
    """
    results: List[Dict[str, Any]] = []
    async with CDPClient(ws_url) as cdp:
        session_id = await cdp.get_page_session()
        for u in usernames:
            try:
                await cdp.goto(session_id, f"https://www.instagram.com/{u}/", wait="domcontent")
                # small human-like pause
                await asyncio.sleep(0.6 + random.random() * 0.6)
                outcome = await cdp.click_follow_button(session_id)
                results.append({"username": u, "status": "followed" if outcome == "clicked" else outcome})
                # jitter between users
                await asyncio.sleep(0.8 + random.random() * 1.2)
            except Exception as e:
                results.append({"username": u, "status": "error", "error": str(e)})
    return {"results": results}

async def perform_unfollow(ws_url: str, usernames: List[str]) -> Dict[str, Any]:
    """
    Navigate to each profile and unfollow via:
      - Click 'Following' (or 'Requested') button
      - Click 'Unfollow' in the opened dialog/menu
    Returns status per username: 'unfollowed' | 'notfollowing' | 'notfound' | 'error'
    """
    results: List[Dict[str, Any]] = []
    async with CDPClient(ws_url) as cdp:
        session_id = await cdp.get_page_session()
        for u in usernames:
            try:
                # 1) go to profile
                await cdp.goto(session_id, f"https://www.instagram.com/{u}/", wait="domcontent")
                await asyncio.sleep(0.6 + random.random() * 0.6)

                # helper: check follow state text (best-effort)
                check_state_js = r"""
                (function () {
                  // finds a big action button in header area
                  const buttons = Array.from(document.querySelectorAll('header button, main button, div button'));
                  const normalize = (el) => ((el?.innerText || '') + ' ' + (el?.textContent || '')).trim().toLowerCase();
                  const match = (rx) => buttons.find(b => rx.test(normalize(b)));

                  const followBtn    = match(/^\s*follow\s*$/i);
                  const followingBtn = match(/following/i);
                  const requestedBtn = match(/requested/i);

                  if (followingBtn) return {state:'following'};
                  if (requestedBtn) return {state:'requested'};
                  if (followBtn)    return {state:'notfollowing'};
                  return {state:'unknown'};
                })();
                """
                state = await cdp.eval(session_id, check_state_js)
                state = state or {"state": "unknown"}

                if state["state"] == "notfollowing":
                    # already not following
                    results.append({"username": u, "status": "notfollowing"})
                    await asyncio.sleep(0.5 + random.random())
                    continue

                # 2) click 'Following' or 'Requested' to open the menu
                open_menu_js = r"""
                (function () {
                  const buttons = Array.from(document.querySelectorAll('header button, main button, div button'));
                  const txt = (el) => ((el?.innerText || '') + ' ' + (el?.textContent || '')).toLowerCase();
                  const target = buttons.find(b => /following|requested/.test(txt(b)));
                  if (!target) return 'notfound';
                  target.click();
                  return 'clicked';
                })();
                """
                opened = await cdp.eval(session_id, open_menu_js)

                if opened != "clicked":
                    # if we couldn't open the menu, try to click the "..." menu and then "Unfollow"
                    alt_open_js = r"""
                    (function () {
                      // Sometimes the unfollow is under a kebab/overflow; try the first '...' button nearby
                      const btn = Array.from(document.querySelectorAll('button, div[role="button"]'))
                        .find(b => /\.\.\./.test((b.innerText||'') + ' ' + (b.textContent||'')));
                      if (!btn) return 'notfound';
                      btn.click();
                      return 'clicked';
                    })();
                    """
                    opened = await cdp.eval(session_id, alt_open_js)

                # tiny wait for the dialog/menu to render
                await asyncio.sleep(0.5)


                # 3) click 'Unfollow' inside dialog/menu
                confirm_unfollow_js = r"""
                (function () {
                  // search visible dialogs/menus first
                  const roots = [
                    ...document.querySelectorAll('[role="dialog"], [role="menu"], [data-pressable-container="true"]'),
                    document.body
                  ];
                  const getText = el => ((el?.innerText || '') + ' ' + (el?.textContent || '')).toLowerCase();
                  for (const root of roots) {
                    const btn = Array.from(root.querySelectorAll('button, div[role="button"], a'))
                      .find(b => /unfollow/.test(getText(b)));
                    if (btn) { btn.click(); return 'confirmed'; }
                  }
                  return 'notfound';
                })();
                """
                confirmed = await cdp.eval(session_id, confirm_unfollow_js)

                if confirmed == "confirmed":
                    results.append({"username": u, "status": "unfollowed"})
                elif state["state"] == "notfollowing":
                    results.append({"username": u, "status": "notfollowing"})
                else:
                    results.append({"username": u, "status": confirmed})

                # small jitter before next user
                await asyncio.sleep(0.8 + random.random() * 1.2)

            except Exception as e:
                results.append({"username": u, "status": "error", "error": str(e)})

    return {"results": results}


async def perform_like(ws_url: str, post_urls: List[str]) -> Dict[str, Any]:
    """
    TODO: implement via CDP (navigate to post, click heart). Stubbed for now.
    """
    await asyncio.sleep(0.1)
    return {"results": [{"post_url": u, "status": "ok"} for u in post_urls]}






async def perform_like_recent(ws_url: str, usernames: List[str], per_user: int = 2) -> Dict[str, Any]:
    """
    For each username:
      1) Open profile
      2) Click the first grid item (reel/post)
      3) In the modal: Like if not already liked
      4) Click 'Next' (or ArrowRight) and repeat up to `per_user`
    Returns per-username results with per-post statuses.
    """
    per_user = max(1, int(per_user or 2))
    results: List[Dict[str, Any]] = []

    # JS snippets from your verified probes
    JS_CLICK_FIRST = r"""
    (function () {
      const sel = 'a[href*="/reel/"], a[href*="/p/"]';
      const a = document.querySelector(sel);
      if (!a) return { clicked: false, reason: "no_thumb" };
      a.click();
      return { clicked: true, href: a.getAttribute("href") };
    })();
    """

    JS_DETECT_LIKE = r"""
    (function () {
      const root = document.querySelector('[role="dialog"]') || document;
      const buttons = Array.from(root.querySelectorAll('button, div[role="button"]'));
      const find = () => buttons.find(b => {
        const al = (b.getAttribute('aria-label') || '').toLowerCase();
        if (al.includes('like') || al.includes('unlike')) return true;
        const svg = b.querySelector('svg');
        const svgAl = (svg?.getAttribute?.('aria-label') || '').toLowerCase();
        return svgAl.includes('like') || svgAl.includes('unlike');
      });
      const btn = find();
      if (!btn) return { found:false };
      const aria = (btn.getAttribute('aria-label') || btn.querySelector('svg')?.getAttribute('aria-label') || '').toLowerCase();
      const already = aria.includes('unlike'); // IG shows "Unlike" when it's liked
      return { found:true, aria, already };
    })();
    """

    JS_CLICK_LIKE = r"""
    (function () {
      const root = document.querySelector('[role="dialog"]') || document;
      const buttons = Array.from(root.querySelectorAll('button, div[role="button"]'));
      function findBtn() {
        for (const b of buttons) {
          const aria = (b.getAttribute('aria-label') || '').toLowerCase();
          const svgAl = (b.querySelector('svg')?.getAttribute('aria-label') || '').toLowerCase();
          if (aria.includes('like') || svgAl.includes('like')) return b;
          if (aria.includes('unlike') || svgAl.includes('unlike')) return b;
        }
        return null;
      }
      const btn = findBtn();
      if (!btn) return { clicked:false, reason:'notfound' };
      const aria = (btn.getAttribute('aria-label') || btn.querySelector('svg')?.getAttribute('aria-label') || '').toLowerCase();
      if (aria.includes('unlike')) return { clicked:false, status:'already_liked' };
      btn.click();
      return { clicked:true, status:'liked' };
    })();
    """

    JS_FIND_NEXT = r"""
    (function () {
      const root = document.querySelector('[role="dialog"]') || document;
      const candidates = [
        '[role="dialog"] button svg[aria-label="Next"]',
        '[role="dialog"] button[aria-label="Next"]',
        '[role="dialog"] div[role="button"] svg[aria-label="Next"]',
        '[role="dialog"] a[aria-label="Next"]',
        'svg[aria-label="Next"]',
        'button[aria-label="Next"]',
        'div[role="button"] svg[aria-label="Next"]'
      ];
      let el = null, sel = null;
      for (const c of candidates) {
        el = root.querySelector(c);
        if (el) { sel = c; break; }
      }
      return { found: !!el, selector: sel || null };
    })();
    """

    JS_CLICK_NEXT_OR_ARROW = r"""
    (function () {
      const root = document.querySelector('[role="dialog"]') || document;
      function findNextButton() {
        const tries = [
          '[role="dialog"] button svg[aria-label="Next"]',
          '[role="dialog"] button[aria-label="Next"]',
          '[role="dialog"] div[role="button"] svg[aria-label="Next"]',
          '[role="dialog"] a[aria-label="Next"]',
          'svg[aria-label="Next"]',
          'button[aria-label="Next"]',
          'div[role="button"] svg[aria-label="Next"]',
        ];
        for (const sel of tries) {
          const el = root.querySelector(sel);
          if (el) return el.closest('button,[role="button"],a') || el;
        }
        return null;
      }
      const btn = findNextButton();
      if (btn) {
        btn.click();
        return { clicked: true, method: 'button' };
      }
      try {
        const ev1 = new KeyboardEvent('keydown', { key: 'ArrowRight', code: 'ArrowRight', bubbles: true });
        const ev2 = new KeyboardEvent('keyup',   { key: 'ArrowRight', code: 'ArrowRight', bubbles: true });
        document.dispatchEvent(ev1);
        document.dispatchEvent(ev2);
        return { clicked: true, method: 'arrowRight' };
      } catch (e) {
        return { clicked: false, method: 'none', error: String(e) };
      }
    })();
    """

    async with CDPClient(ws_url) as cdp:
        session_id = await cdp.get_page_session()

        for username in usernames:
            user_result: Dict[str, Any] = {"username": username, "results": []}

            # 1) Go to profile
            try:
                await cdp.goto(session_id, f"https://www.instagram.com/{username}/", wait="domcontent")
            except Exception as e:
                results.append({**user_result, "status": "error", "error": f"nav_profile: {e}"})
                continue

            await asyncio.sleep(0.6 + random.random() * 0.6)

            # 2) Open first grid item (reel/post)
            opened = await cdp.eval(session_id, JS_CLICK_FIRST)
            if not (isinstance(opened, dict) and opened.get("clicked")):
                results.append({**user_result, "status": "no_media", "detail": opened})
                continue

            await asyncio.sleep(0.6 + random.random() * 0.5)

            # 3) Loop N posts inside modal
            for i in range(per_user):
                try:
                    await asyncio.sleep(0.4 + random.random() * 0.4)

                    # Detect Like/Unlike
                    state = await cdp.eval(session_id, JS_DETECT_LIKE) or {"found": False}
                    if not state.get("found"):
                        user_result["results"].append({"index": i + 1, "status": "notfound"})
                    elif state.get("already"):
                        user_result["results"].append({"index": i + 1, "status": "already_liked"})
                    else:
                        # Click Like
                        clicked = await cdp.eval(session_id, JS_CLICK_LIKE)
                        await asyncio.sleep(0.35 + random.random() * 0.35)
                        verify = await cdp.eval(session_id, JS_DETECT_LIKE) or {}
                        if verify.get("found") and verify.get("already"):
                            user_result["results"].append({"index": i + 1, "status": "liked"})
                        else:
                            user_result["results"].append({"index": i + 1, "status": "error", "error": "toggle_failed", "clicked": clicked})

                    # Move to next, unless this was the last one
                    if i < per_user - 1:
                        n = await cdp.eval(session_id, JS_FIND_NEXT)
                        if not (isinstance(n, dict) and n.get("found")):
                            # try arrow fallback directly
                            n2 = await cdp.eval(session_id, JS_CLICK_NEXT_OR_ARROW)
                            if not (isinstance(n2, dict) and n2.get("clicked")):
                                # no next available; stop early
                                break
                        else:
                            _ = await cdp.eval(session_id, JS_CLICK_NEXT_OR_ARROW)

                except Exception as e:
                    user_result["results"].append({"index": i + 1, "status": "error", "error": str(e)})

                await asyncio.sleep(0.6 + random.random() * 0.7)

            results.append(user_result)
            await asyncio.sleep(0.8 + random.random() * 1.2)

    return {"results": results}




async def perform_dm(ws_url: str, usernames: List[str], template_id: int, placeholders: Dict[str, Any] | None) -> Dict[str, Any]:
    """
    TODO: implement via CDP (open chat, send message). Stubbed for now.
    """
    await asyncio.sleep(0.1)
    return {"results": [{"username": u, "status": "ok", "template_id": template_id} for u in usernames]}


# -------------------- Orchestrator --------------------

async def run_action(db: Session, action_type: str, account_id: int, profile_id: int, payload: Dict[str, Any]) -> ActionLog:
    limits = get_account_limits(db, account_id)
    # Pre-check limits
    rate_limit_guard(db, account_id, action_type, limits)

    # Create log (running)
    log = ActionLog(
        account_id=account_id,
        profile_id=profile_id,
        action_type=action_type,
        payload=payload,
        status="running",
        started_at=_now(),
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    try:
        ws_url = ensure_profile_ws(db, profile_id)
        await random_delay(limits)

        if action_type == "follow":
            usernames = payload.get("usernames") or []
            result = await perform_follow(ws_url, usernames)
        elif action_type == "unfollow":
            usernames = payload.get("usernames") or []
            result = await perform_unfollow(ws_url, usernames)
        elif action_type == "like":
            usernames = payload.get("usernames") or []
            if usernames:
                per_user = payload.get("count") or 2
                result = await perform_like_recent(ws_url, usernames, per_user=int(per_user))
            else:
                post_urls = payload.get("post_urls") or []
                result = await perform_like(ws_url, post_urls)
        elif action_type == "dm":
            usernames = payload.get("usernames") or []
            template_id = payload.get("template_id")
            placeholders = payload.get("placeholders") or {}
            result = await perform_dm(ws_url, usernames, template_id, placeholders)
        else:
            raise HTTPException(status_code=400, detail="unsupported action_type")

        # Success
        log.status = "success"
        log.payload = {**payload, "result": result}  # keep trace
        log.finished_at = _now()
        db.commit()
        db.refresh(log)
        return log

    except HTTPException as e:
        log.status = "rate_limited" if e.status_code == 429 else "error"
        log.error_message = e.detail if isinstance(e.detail, str) else str(e.detail)
        log.finished_at = _now()
        db.commit()
        db.refresh(log)
        raise

    except Exception as e:
        log.status = "error"
        log.error_message = str(e)
        log.finished_at = _now()
        db.commit()
        db.refresh(log)
        raise
