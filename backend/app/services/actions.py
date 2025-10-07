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
from ..models.account import Account

import websockets  # make sure 'websockets' is in requirements.txt
import logging
like_log = logging.getLogger("app.services.actions.like_recent")
stream_log = logging.getLogger("app.services.actions.mass_stream")



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


async def ensure_profile_ws(db: Session, profile_id: int) -> str:
    """
    Pull a usable CDP websocket URL from the account.
    Since we merged Profile into Account, profile_id is now account_id.
    """
    account: Optional[Account] = db.get(Account, profile_id)
    if not account:
        raise HTTPException(status_code=404, detail="account not found")

    # Check if account has a bulkcreate profile
    if not account.bulk_profile_name and not account.adspower_profile_id:
        raise HTTPException(status_code=400, detail="account has no linked profile")

    # For bulkcreate profiles, we need to get the WebSocket URL from the bulkcreate service
    if account.bulk_profile_name:
        # Try to get the WebSocket URL from the account's stored values
        ws_url = getattr(account, "last_ws_puppeteer", None)
        if not ws_url and getattr(account, "last_ws_selenium", None):
            ws_url = f"ws://{account.last_ws_selenium}"
        
        if not ws_url:
            # If no stored WebSocket URL, we need to launch the profile automatically
            from ..services.bulkcreate_client import launch_cdp
            import asyncio
            import requests
            
            try:
                # Launch the profile and get the WebSocket URL
                result = await launch_cdp(account.bulk_profile_name, enhanced=True)
                ws_url = result.get("ws")
                if ws_url:
                    # Store the WebSocket URL for future use
                    account.last_ws_puppeteer = ws_url
                    db.add(account)
                    db.commit()
                    # Profile auto-launched successfully
                else:
                    raise HTTPException(status_code=500, detail=f"Failed to get WebSocket URL from bulkcreate profile '{account.bulk_profile_name}'")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to auto-launch bulkcreate profile '{account.bulk_profile_name}': {str(e)}")

    # For AdsPower profiles (legacy)
    elif account.adspower_profile_id:
        ws_url = getattr(account, "last_ws_puppeteer", None)
        if not ws_url and getattr(account, "last_ws_selenium", None):
            ws_url = f"ws://{account.last_ws_selenium}"

    if not ws_url:
        raise HTTPException(status_code=400, detail="profile has no active websocket url; open it first")

    # Verify the WebSocket URL is still valid by checking if the profile is running
    try:
        import requests
        response = requests.get("http://127.0.0.1:4000/api/profiles", timeout=5)
        if response.status_code == 200:
            bulkcreate_profiles = response.json()
            if account.bulk_profile_name in bulkcreate_profiles:
                profile_info = bulkcreate_profiles[account.bulk_profile_name]
                if not profile_info.get("running", False):
                    # Profile is not running, need to launch it
                    # Profile is not running, need to launch it
                    
                    from ..services.bulkcreate_client import launch_cdp
                    
                    result = await launch_cdp(account.bulk_profile_name, enhanced=True)
                    new_ws_url = result.get("ws")
                    if new_ws_url:
                        account.last_ws_puppeteer = new_ws_url
                        db.add(account)
                        db.commit()
                        ws_url = new_ws_url
                        # Profile re-launched successfully
                    else:
                        raise HTTPException(status_code=500, detail=f"Failed to re-launch profile '{account.bulk_profile_name}'")
    except Exception as e:
        # Continue with the stored WebSocket URL anyway
        pass

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
            # Handle both string and bytes responses, and coroutine objects
            if isinstance(raw, bytes):
                raw = raw.decode('utf-8')
            elif hasattr(raw, '__await__'):
                # Handle coroutine objects
                raw = await raw
                if isinstance(raw, bytes):
                    raw = raw.decode('utf-8')
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
            # Handle both string and bytes responses, and coroutine objects
            if isinstance(raw, bytes):
                raw = raw.decode('utf-8')
            elif hasattr(raw, '__await__'):
                # Handle coroutine objects
                raw = await raw
                if isinstance(raw, bytes):
                    raw = raw.decode('utf-8')
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
            {"expression": expression, "returnByValue": True, "awaitPromise": True},
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

    async def perform_single_follow_action(self, username: str, mode: str, section: str) -> Dict[str, Any]:
        """Perform a single follow/unfollow action for limit=1 case"""
        try:
            # Get page session and navigate to the target profile
            session_id = await self.get_page_session()
            await self.goto(session_id, f"https://www.instagram.com/{username}/")
            await asyncio.sleep(2)
            
            # Open the followers/following modal
            if section == "followers":
                modal_opened = await self.eval(session_id, """
                    const followersBtn = document.querySelector('a[href*="/followers/"]');
                    if (followersBtn) {
                        followersBtn.click();
                        return true;
                    }
                    return false;
                """)
            else:  # following
                modal_opened = await self.eval(session_id, """
                    const followingBtn = document.querySelector('a[href*="/following/"]');
                    if (followingBtn) {
                        followingBtn.click();
                        return true;
                    }
                    return false;
                """)
            
            await asyncio.sleep(2)
            
            # Find the first followable user
            result = await self.eval(session_id, """
                (() => {
                    const buttons = document.querySelectorAll('button');
                    for (let btn of buttons) {
                        const text = btn.textContent?.trim();
                        if (text === 'Follow' || text === 'Unfollow') {
                            btn.click();
                            return JSON.stringify({ success: true, action: text });
                        }
                    }
                    return JSON.stringify({ success: false, error: 'no_follow_button_found' });
                })()
            """)
            
            await asyncio.sleep(1)
            
            # Parse the JSON result
            if result and isinstance(result, str):
                try:
                    import json
                    parsed_result = json.loads(result)
                    return parsed_result
                except:
                    pass
            
            return {"success": False, "error": "no_follow_button_found"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}


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


# -------------------- Streaming mass follow/unfollow --------------------

async def perform_mass_follow_stream(
    ws_url: str,
    target_username: str,
    mode: str,                  # "follow" | "unfollow"
    limit: int = 50,
    percent: int | None = None,
    max_scrolls: int = 120,     # allow more scrolling before declaring bottom
    section: str = "followers", # "followers" | "following"
    debug_dom: bool = False,
    max_duration_minutes: int = 10,
):
    """
    Robust mass follow/unfollow inside Followers/Following modal.
    - Adaptive scrolling (burst -> page -> sentinel) until real bottom.
    - Only counts an action after verifying state change.
    - Avoids re-clicking the same row by marking after verified result.
    """
    assert mode in ("follow", "unfollow")
    assert section in ("followers", "following")

    from .actions import CDPClient

    stream_log.info(f"[mass_stream] start mode={mode} section={section} target={target_username} limit={limit} max_scrolls={max_scrolls} max_duration={max_duration_minutes}m")
    effective_section = section
    if mode == "follow" and section != "followers":
        effective_section = "followers"
    if mode == "unfollow" and section != "following":
        effective_section = "following"
    async with CDPClient(ws_url) as cdp:
        sid = await cdp.get_page_session()
        stream_log.info(f"[mass_stream] got session id: {sid}")

        # 1) Go to profile
        await cdp.goto(sid, f"https://www.instagram.com/{target_username}/", wait="domcontent")
        stream_log.info(f"[mass_stream] navigated to profile: {target_username}")
        await asyncio.sleep(1.0)

        # 2) Open modal (href first, then header chip text)
        open_modal_js = r"""
        (function(){
          const sec = "__SECTION__";
          const u = "__TARGET__".replace(/^@/,'').toLowerCase();
          const hrefNeedle = "/" + u + "/" + (sec==="followers" ? "followers/" : "following/");
          let link = Array.from(document.querySelectorAll('a[href]'))
              .find(a => (a.getAttribute('href')||'').toLowerCase().includes(hrefNeedle));
          if(!link){
            const scope = document.querySelector('header') || document;
            link = Array.from(scope.querySelectorAll('a,button,span,div'))
              .find(n => {
                 const t = ((n.innerText||n.textContent)||"").toLowerCase();
                 return (sec==='followers'?/\bfollowers\b/:/\bfollowing\b/).test(t);
              });
            if(link) link = link.closest('a,button,[role="link"]') || link;
          }
          if(!link) return {ok:false, reason:"link-not-found"};
          try{ link.scrollIntoView({block:'center'}); }catch(e){}
          try{ link.click(); }catch(e){ return {ok:false, reason:"click-failed:"+e}; }
          return {ok:true};
        })();
        """.replace("__SECTION__", effective_section).replace("__TARGET__", target_username)
        opened = await cdp.eval(sid, open_modal_js)
        stream_log.info(f"[mass_stream] open modal result: {opened}")
        if not (isinstance(opened, dict) and opened.get("ok")):
            yield {"type":"done","reason":"modal_open_failed","detail":opened}
            return
        await asyncio.sleep(1.0)

        # 3) Wire helpers in the page
        helpers = r"""
    (function(){
      const modal = document.querySelector('div[role="dialog"]');
          if(!modal) return {ok:false, reason:'no-modal'};

          // Best guess scroll container (tallest scrollable descendant)
          const cand = [modal, ...modal.querySelectorAll('div,section,ul')];
          let sc=null, score=-1;
          for(const el of cand){
            const cs=getComputedStyle(el), sh=el.scrollHeight|0, ch=el.clientHeight|0;
            const scr=(cs.overflowY==='auto'||cs.overflowY==='scroll'||cs.overflow==='auto');
            const s=(scr?1:0)*1e7 + (sh-ch);
            if(sh>ch+10 && s>score){ sc=el; score=s; }
          }
          sc = sc || modal;

          // save globals
          window.__IG_MODAL__ = modal;
          window.__IG_SC__ = sc;
          window.__IG_LAST_SH__ = sc.scrollHeight|0;
          window.__IG_LAST_TOP__ = sc.scrollTop|0;
          window.__IG_STALLS__ = 0;

          // Util: visible within the window (not just sc viewport)
          const within = (el)=>{
            const r=el.getBoundingClientRect();
            const h=(innerHeight||document.documentElement.clientHeight);
            return r.top>80 && r.bottom<h-80;
          };

          // Gather candidates (unprocessed)
          window.__IG_GATHER__ = function(mode,max=10){
            const root = window.__IG_MODAL__ || document;
            const rows = Array.from(root.querySelectorAll('li, div[role], div'));
            const out=[];
            for(const r of rows){
              if(r.dataset.igDone==='1') continue;
              const btn = r.querySelector('button'); if(!btn) continue;
              const label=(btn.innerText||btn.textContent||'').trim().toLowerCase();
              if(mode==='follow' && label==='follow' && within(r)) out.push({row:r,btn,kind:'follow'});
              if(mode==='unfollow' && (label==='following'||label==='requested') && within(r)) out.push({row:r,btn,kind:'unfollow'});
              if(out.length>=max) break;
            }
            return {count:out.length};
          };

          // Click next candidate (store reference internally; return primitives only)
          window.__IG_CLICK_NEXT__ = function(mode){
            const root = window.__IG_MODAL__ || document;
            const rows = Array.from(root.querySelectorAll('li, div[role], div'));
            for(let i=0; i<rows.length; i++){
              const r = rows[i];
              if(r.dataset.igDone==='1') continue;
              const btn = r.querySelector('button'); if(!btn) continue;
              const label=(btn.innerText||btn.textContent||'').trim().toLowerCase();
              if(mode==='follow' && (label==='follow' || label==='follow back')){
                try{ r.scrollIntoView({block:'center'}); btn.click(); window.__lastRowClicked = r; return {ok:true, idx:i}; }catch(e){ return {ok:false, reason:String(e)} }
              }
              if(mode==='unfollow' && (label==='following'||label==='requested')){
                try{ r.scrollIntoView({block:'center'}); btn.click(); window.__lastRowClicked = r; return {ok:true, idx:i, unfollow:true}; }catch(e){ return {ok:false, reason:String(e)} }
              }
            }
            return {ok:false, reason:'no-visible-candidate'};
          };

          // Verify row state change; mark row as done on success
          window.__IG_VERIFY_ROW__ = function(row, mode){
            // Accept explicit row or use last clicked
            row = row || window.__lastRowClicked || null;
            if(!row) return {ok:false, reason:'no-row'};
            const btn = row.querySelector('button'); if(!btn) return {ok:false, reason:'no-btn'};
            const label=(btn.innerText||btn.textContent||'').trim().toLowerCase();
            if(mode==='follow'){
              if(label!=='follow'){ row.dataset.igDone='1'; return {ok:true, changed:true}; }
              return {ok:false, changed:false};
            }else{
              // after clicking "Following/Requested", a confirm dialog may appear
              // If button text changed away from "following"/"requested", consider done.
              if(label!=='following' && label!=='requested'){ row.dataset.igDone='1'; return {ok:true, changed:true}; }
              return {ok:false, changed:false};
            }
          };

          // Confirm unfollow in popup/menu if present
          window.__IG_CONFIRM_UNFOLLOW__ = function(){
            const roots=[...document.querySelectorAll('[role="dialog"],[role="menu"]'), document.body];
            for(const r of roots){
              const b = Array.from(r.querySelectorAll('button,[role="button"],a'))
                      .find(x => /unfollow/i.test((x.innerText||x.textContent||'')));
              if(b){ try{ b.click(); return {ok:true}; }catch(e){ return {ok:false, reason:String(e)} } }
            }
            return {ok:false, reason:'not-found'};
          };

          // Scroll strategies
          window.__IG_SCROLL_ADV__ = function(strategy){
            const sc = window.__IG_SC__; if(!sc) return {ok:false};
            const beforeTop=sc.scrollTop|0, beforeSH=sc.scrollHeight|0;

            if(strategy==='burst'){
              for(let i=0;i<5;i++){
                const dy = 180 + Math.floor(Math.random()*180);
                try{ sc.dispatchEvent(new WheelEvent('wheel',{deltaY:dy,bubbles:true,cancelable:true})); }
                catch(e){ sc.scrollTop = sc.scrollTop + dy; }
              }
            }else if(strategy==='page'){
              sc.scrollTop = sc.scrollTop + Math.floor(sc.clientHeight*0.85);
            }else{ // sentinel
              const rows = sc.querySelectorAll('li, div[role], div');
              const last = rows[rows.length-1];
              if(last){ try{ last.scrollIntoView({block:'end'});}catch(e){} }
              sc.scrollTop = sc.scrollHeight; // push to hard bottom of current page
            }

            const afterTop=sc.scrollTop|0, afterSH=sc.scrollHeight|0;
            const grew = afterSH > beforeSH + 5;
            const moved = afterTop > beforeTop + 20;

            if(grew || moved){ window.__IG_STALLS__ = 0; }
            else{ window.__IG_STALLS__ = (window.__IG_STALLS__|0) + 1; }

            window.__IG_LAST_SH__ = afterSH;
            window.__IG_LAST_TOP__ = afterTop;

            const atBottom = (afterTop + sc.clientHeight + 2 >= afterSH);
            return {ok:true, grew, moved, atBottom, stalls:window.__IG_STALLS__|0, top:afterTop, sh:afterSH};
          };

          return {ok:true, ch:sc.clientHeight|0, sh:sc.scrollHeight|0};
    })();
    """
        wired = await cdp.eval(sid, helpers)
        stream_log.debug(f"[mass_stream] modal helpers wired: {wired}")
        if not (isinstance(wired, dict) and wired.get("ok")):
            yield {"type":"done","reason":"modal_setup_failed","detail":wired}
            return

        # 4) Limits & timers
        acted = 0
        processed = 0
        scrolls = 0
        misses = 0
        start = asyncio.get_event_loop().time()
        deadline = start + max_duration_minutes*60
        if percent is not None:
            limit = max(1, int(limit * (percent/100)))

        yield {"type":"start","section":section,"mode":mode,"limit":limit}

        # 5) Main loop
        while acted < limit and scrolls < max_scrolls and asyncio.get_event_loop().time() < deadline:
            # gather visible candidates; if few, scroll pre-emptively
            vis = await cdp.eval(sid, f"(function(){{return window.__IG_GATHER__('{mode}',12);}})();")
            stream_log.debug(f"[mass_stream] gather visible candidates: {vis}")
            if isinstance(vis, dict) and vis.get("count", 0) < 2:
                s1 = await cdp.eval(sid, "(function(){return window.__IG_SCROLL_ADV__('burst');})();")
                scrolls += 1
                yield {"type":"scroll","strategy":"burst","count":scrolls,"detail":s1}
                stream_log.debug(f"[mass_stream] preemptive scroll (burst), detail={s1}")
                await asyncio.sleep(0.35 + random.random()*0.35)

            # try click next candidate
            click = await cdp.eval(sid, f"(function(){{return window.__IG_CLICK_NEXT__('{mode}');}})();")
            processed += 1
            stream_log.info(f"[mass_stream] click result: {click}")

            if isinstance(click, dict) and click.get("ok"):
                # for unfollow, confirm if needed
                if click.get("unfollow"):
                    await asyncio.sleep(0.25 + random.random()*0.35)
                    _ = await cdp.eval(sid, "(function(){return window.__IG_CONFIRM_UNFOLLOW__();})();")
                    stream_log.debug("[mass_stream] confirm unfollow attempted")
                    await asyncio.sleep(0.15 + random.random()*0.25)

                # verify state change (retry up to 3x for exact counts)
                success = False
                for _ in range(3):
                    ver = await cdp.eval(sid, f"(function(){{return window.__IG_VERIFY_ROW__(arguments[0], '{mode}');}})();")
                    if ver is None:
                        ver = await cdp.eval(sid, f"(function(){{return window.__IG_VERIFY_ROW__(window.__lastRowClicked, '{mode}');}})();")
                    stream_log.info(f"[mass_stream] verify result: {ver}")
                    if isinstance(ver, dict) and ver.get("ok") and ver.get("changed"):
                        success = True
                        break
                    await asyncio.sleep(0.4 + random.random()*0.4)

                if success:
                    acted += 1
                    misses = 0
                    yield {"type":"action","mode":mode,"acted":acted,"processed":processed}
                    stream_log.info(f"[mass_stream] action confirmed acted={acted} processed={processed}")
                    if acted >= limit:
                        yield {"type":"done","reason":"limit","acted":acted,"processed":processed,"scrolls":scrolls}
                        stream_log.info(f"[mass_stream] done reason=limit acted={acted} processed={processed} scrolls={scrolls}")
                        break
                    await asyncio.sleep(0.85 + random.random()*1.1)
                else:
                    # no change → we'll need more candidates; count as miss
                    misses += 1
                    stream_log.debug(f"[mass_stream] no change after verify; misses={misses}")
                continue

            # no visible candidate → escalate scrolling strategy
            misses += 1
            strategy = "page" if (misses % 3 == 0) else ("sentinel" if (misses % 6 == 0) else "burst")
            s2 = await cdp.eval(sid, f"(function(){{return window.__IG_SCROLL_ADV__('{strategy}');}})();")
            scrolls += 1
            yield {"type":"scroll","strategy":strategy,"count":scrolls,"detail":s2}
            stream_log.debug(f"[mass_stream] escalate scroll strategy={strategy} detail={s2}")
            await asyncio.sleep(0.45 + random.random()*0.55)

            # truly at bottom only if:
            # - we're visually at bottom, and
            # - we've done multiple escalations with no growth
            if isinstance(s2, dict) and s2.get("atBottom") and s2.get("stalls", 0) >= 8:
                yield {"type":"done","reason":"bottom_reached","acted":acted,"processed":processed,"scrolls":scrolls}
                stream_log.info(f"[mass_stream] done reason=bottom_reached acted={acted} processed={processed} scrolls={scrolls}")
                break

            # occasional dwell
            if random.random() < 0.15:
                d = 1.0 + random.random()*2.0
                await asyncio.sleep(d)
                yield {"type":"dwell","sec":round(d,2)}

        reason = "limit" if acted >= limit else ("scrolls" if scrolls >= max_scrolls else ("time" if asyncio.get_event_loop().time() >= deadline else "complete"))
        yield {"type":"done","reason":reason,"acted":acted,"processed":processed,"scrolls":scrolls}
        stream_log.info(f"[mass_stream] done reason={reason} acted={acted} processed={processed} scrolls={scrolls}")


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
    like_log.debug(f"Start: ws_url={ws_url}, usernames={usernames}, per_user={per_user}")

    # JS snippets from your verified probes
    JS_CLICK_FIRST = r"""
    (function () {
      const sel = 'a[href*="/reel/"], a[href*="/p/"], article a, div[role="link"]';
      const a = document.querySelector(sel);
      if (!a) {
        return { clicked: false, reason: "no_thumb" };
      }
      try {
        a.click();
        return { clicked: true, href: a.getAttribute("href") || null };
      } catch (e) {
        return { clicked: false, reason: String(e) };
      }
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
        like_log.debug(f"[like_recent] Got session_id={session_id}")
    
        for username in usernames:
            user_result: Dict[str, Any] = {"username": username, "results": []}
            like_log.debug(f"[like_recent] Visiting profile: {username}")
    
            # 1) Go to profile
            try:
                await cdp.goto(session_id, f"https://www.instagram.com/{username}/", wait="domcontent")
                like_log.debug(f"[like_recent] Navigated to profile {username}")
            except Exception as e:
                like_log.debug(f"[like_recent] ERROR navigating to {username}: {e}")
                results.append({**user_result, "status": "error", "error": f"nav_profile: {e}"})
                continue
            
            await asyncio.sleep(0.6 + random.random() * 0.6)
            # 🔎 dynamic wait for thumbnails to load
            thumb_found = False
            for _ in range(10):  # retry up to ~5s (10 * 0.5s)
                opened = await cdp.eval(session_id, JS_CLICK_FIRST)
                if isinstance(opened, dict) and opened.get("clicked"):
                    like_log.debug(f"[like_recent] First post clicked for {username}: {opened}")
                    thumb_found = True
                    break
                await asyncio.sleep(0.5)

            if not thumb_found:
                like_log.debug(f"[like_recent] No media found for {username}, skipping")
                results.append({**user_result, "status": "no_media"})
                continue
    
            # 2) Open first grid item (reel/post)
            opened = await cdp.eval(session_id, JS_CLICK_FIRST)
            like_log.debug(f"[like_recent] Click first post result for {username}: {opened}")
    
            if not (isinstance(opened, dict) and opened.get("clicked")):
                results.append({**user_result, "status": "no_media", "detail": opened})
                like_log.debug(f"[like_recent] No media found for {username}, skipping")
                continue
            
            await asyncio.sleep(0.6 + random.random() * 0.5)
    
            # 3) Loop N posts inside modal
            for i in range(per_user):
                try:
                    await asyncio.sleep(0.4 + random.random() * 0.4)
    
                    state = await cdp.eval(session_id, JS_DETECT_LIKE) or {"found": False}
                    like_log.debug(f"[like_recent] Post {i+1}/{per_user} state={state}")
    
                    if not state.get("found"):
                        user_result["results"].append({"index": i + 1, "status": "notfound"})
                    elif state.get("already"):
                        user_result["results"].append({"index": i + 1, "status": "already_liked"})
                    else:
                        clicked = await cdp.eval(session_id, JS_CLICK_LIKE)
                        like_log.debug(f"[like_recent] Click like result={clicked}")
                        await asyncio.sleep(0.35 + random.random() * 0.35)
    
                        verify = await cdp.eval(session_id, JS_DETECT_LIKE) or {}
                        like_log.debug(f"[like_recent] Verify after click={verify}")
    
                        if verify.get("found") and verify.get("already"):
                            user_result["results"].append({"index": i + 1, "status": "liked"})
                        else:
                            user_result["results"].append({
                                "index": i + 1,
                                "status": "error",
                                "error": "toggle_failed",
                                "clicked": clicked
                            })
    
                    # Move to next post unless last one
                    if i < per_user - 1:
                        n = await cdp.eval(session_id, JS_FIND_NEXT)
                        like_log.debug(f"[like_recent] Find next result={n}")
    
                        if not (isinstance(n, dict) and n.get("found")):
                            n2 = await cdp.eval(session_id, JS_CLICK_NEXT_OR_ARROW)
                            like_log.debug(f"[like_recent] Arrow fallback result={n2}")
                            if not (isinstance(n2, dict) and n2.get("clicked")):
                                like_log.debug(f"[like_recent] No next available, stopping early")
                                break
                        else:
                            _ = await cdp.eval(session_id, JS_CLICK_NEXT_OR_ARROW)
                            like_log.debug(f"[like_recent] Clicked next via button")
    
                except Exception as e:
                    like_log.debug(f"[like_recent] ERROR in post loop {i+1}: {e}")
                    user_result["results"].append({"index": i + 1, "status": "error", "error": str(e)})
    
                await asyncio.sleep(0.6 + random.random() * 0.7)
    
            results.append(user_result)
            like_log.debug(f"[like_recent] Finished {username}: {user_result}")
    
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
        ws_url = await ensure_profile_ws(db, profile_id)
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
