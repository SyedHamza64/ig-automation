# app/services/ig_login.py
import asyncio, json, websockets
from typing import Optional, Dict, Any

async def _cdp(ws, method: str, params: Optional[dict] = None, _id: int = 0) -> dict:
    req = {"id": _id or 1, "method": method}
    if params: req["params"] = params
    await ws.send(json.dumps(req))
    while True:
        msg = json.loads(await ws.recv())
        if msg.get("id") == req["id"]:
            if "error" in msg:
                raise RuntimeError(f"CDP error {method}: {msg['error']}")
            return msg.get("result", {})

async def _session(ws, sid: str, method: str, params: Optional[dict] = None, _id: int = 0) -> dict:
    req = {"id": _id or 2, "method": method, "sessionId": sid}
    if params: req["params"] = params
    await ws.send(json.dumps(req))
    while True:
        msg = json.loads(await ws.recv())
        if msg.get("id") == req["id"]:
            if "error" in msg:
                raise RuntimeError(f"CDP error {method}: {msg['error']}")
            return msg.get("result", {})

async def _attach_first_page(ws) -> str:
    targets = await _cdp(ws, "Target.getTargets")
    page = next((t for t in targets.get("targetInfos", []) if t.get("type") == "page"), None)
    if not page:
        raise RuntimeError("No page target found")
    attached = await _cdp(ws, "Target.attachToTarget", {"targetId": page["targetId"], "flatten": True})
    return attached["sessionId"]

async def _eval(sid: str, ws, expr: str) -> Dict[str, Any]:
    res = await _session(ws, sid, "Runtime.evaluate", {"expression": expr, "returnByValue": True})
    return (res.get("result") or {}).get("value") or {}

async def login_once(ws_url: str, username: str, password: str, wait_ms: int = 8000) -> Dict[str, Any]:
    """
    Minimal login flow:
    - assumes we are on an Instagram login page (or will redirect there)
    - fills inputs and clicks submit
    - waits briefly, then reports location & simple DOM signals
    NOTE: Do not log credentials; we only pass them through CDP.
    """
    async with websockets.connect(ws_url, max_size=None) as ws:
        sid = await _attach_first_page(ws)
        await _session(ws, sid, "Runtime.enable")

        # Ensure we are at login page (best-effort)
        await _session(ws, sid, "Page.enable")
        await _session(ws, sid, "Page.navigate", {"url": "https://www.instagram.com/accounts/login/"})

        # Wait a moment for DOM
        await asyncio.sleep(2.0)

        # Fill fields via JS (more robust than low-level input events here)
        js_fill = f"""
(async () => {{
  const user = document.querySelector('input[name="username"]');
  const pass = document.querySelector('input[name="password"]');
  if (!user || !pass) return {{ ok:false, reason: "inputs-not-found", url: location.href }};

  user.focus();
  user.value = {json.dumps(username)};
  user.dispatchEvent(new Event('input', {{ bubbles: true }}));

  pass.focus();
  pass.value = {json.dumps(password)};
  pass.dispatchEvent(new Event('input', {{ bubbles: true }}));

  const btn = document.querySelector('form button[type="submit"]') || document.querySelector('button[type="submit"]');
  if (!btn) return {{ ok:false, reason: "submit-not-found", url: location.href }};

  btn.click();
  return {{ ok:true, url: location.href }};
}})();
"""
        fill_res = await _eval(sid, ws, js_fill)

        # Give Instagram time to process login/redirect or challenge
        await asyncio.sleep(wait_ms / 1000)

        # Read current state
        js_state = """
(() => {
  const href = location.href;
  const title = document.title;
  const twoFa = document.querySelector('input[name="verificationCode"]') || document.querySelector('input[name="security_code"]');
  const checkpoint = /challenge|two_factor/i.test(href);
  const loggedInNav = document.querySelector('nav a[href*="/accounts/"]') || document.querySelector('svg[aria-label="Home"]');
  let state = "unknown";
  if (checkpoint || twoFa) state = "checkpoint";
  else if (loggedInNav && !/login/i.test(href)) state = "logged_in";
  else if (/login/i.test(href)) state = "login";
  return { state, href, title };
})();
"""
        st = await _eval(sid, ws, js_state)

        return {
            "submitted": bool(fill_res.get("ok")),
            "after": st,
        }
