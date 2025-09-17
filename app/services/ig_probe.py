# app/services/ig_probe.py
import asyncio, json, websockets
from typing import Dict, Any, Optional

async def _cdp_call(ws, method: str, params: Optional[dict] = None, _id: int = 0) -> dict:
    req = {"id": _id or 1, "method": method}
    if params: req["params"] = params
    await ws.send(json.dumps(req))
    while True:
        msg = json.loads(await ws.recv())
        if msg.get("id") == req["id"]:
            if "error" in msg:
                raise RuntimeError(f"CDP error {method}: {msg['error']}")
            return msg.get("result", {})

async def _session_call(ws, sid: str, method: str, params: Optional[dict] = None, _id: int = 0) -> dict:
    req = {"id": _id or 2, "method": method, "sessionId": sid}
    if params: req["params"] = params
    await ws.send(json.dumps(req))
    while True:
        msg = json.loads(await ws.recv())
        if msg.get("id") == req["id"]:
            if "error" in msg:
                raise RuntimeError(f"CDP error {method}: {msg['error']}")
            return msg.get("result", {})

async def _get_first_page_session(ws) -> str:
    targets = await _cdp_call(ws, "Target.getTargets")
    page = next((t for t in targets.get("targetInfos", []) if t.get("type") == "page"), None)
    if not page:
        raise RuntimeError("No page target found")
    attached = await _cdp_call(ws, "Target.attachToTarget", {"targetId": page["targetId"], "flatten": True})
    return attached["sessionId"]

async def check_login_state(ws_url: str, timeout_sec: float = 10.0) -> Dict[str, Any]:
    async with websockets.connect(ws_url, max_size=None) as ws:
        sid = await _get_first_page_session(ws)
        await _session_call(ws, sid, "Runtime.enable")
        # Detect login inputs; very fast, no navigation
        js = """
(() => {
  const bySel = s => document.querySelector(s);
  const loginUsername = bySel('input[name="username"]');
  const loginPassword = bySel('input[name="password"]');
  const loginForm    = bySel('form[action*="login"]') || bySel('form button[type="submit"]');
  const loggedInNav  = bySel('nav a[href*="/accounts/"]') || bySel('svg[aria-label="Home"]');
  const title = document.title;
  const href  = location.href;

  let state = "unknown";
  if (loginUsername || loginPassword || loginForm) state = "login";
  else if (loggedInNav) state = "logged_in";
  return { state, title, href };
})();
"""
        res = await _session_call(ws, sid, "Runtime.evaluate", {"expression": js, "returnByValue": True})
        val = (res.get("result") or {}).get("value") or {}
        return {"state": val.get("state"), "title": val.get("title"), "url": val.get("href")}
