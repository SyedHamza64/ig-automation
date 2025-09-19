import asyncio, json, websockets
from typing import Dict, Any, Optional

# Minimal CDP client: send/recv JSON-RPC messages over the DevTools WebSocket.

async def cdp_call(ws, method: str, params: Optional[Dict[str, Any]] = None, _id: int = 0) -> Dict[str, Any]:
    req = {"id": _id or 1, "method": method}
    if params:
        req["params"] = params
    await ws.send(json.dumps(req))
    while True:
        raw = await ws.recv()
        msg = json.loads(raw)
        if msg.get("id") == req["id"]:
            if "error" in msg:
                raise RuntimeError(f"CDP error for {method}: {msg['error']}")
            return msg.get("result", {})
        # ignore events

async def get_first_page_target(ws) -> Optional[str]:
    res = await cdp_call(ws, "Target.getTargets")
    for t in res.get("targetInfos", []):
        if t.get("type") == "page":
            return t.get("targetId")
    return None

async def attach_to_target(ws, target_id: str) -> str:
    res = await cdp_call(ws, "Target.attachToTarget", {"targetId": target_id, "flatten": True})
    return res["sessionId"]

async def session_call(ws, session_id: str, method: str, params: Optional[Dict[str, Any]] = None, _id: int = 0):
    req = {"id": _id or 2, "method": method, "sessionId": session_id}
    if params:
        req["params"] = params
    await ws.send(json.dumps(req))
    while True:
        raw = await ws.recv()
        msg = json.loads(raw)
        if msg.get("id") == req["id"]:
            if "error" in msg:
                raise RuntimeError(f"CDP error for {method}: {msg['error']}")
            return msg.get("result", {})

async def navigate(ws_url: str, url: str, timeout_ms: int = 15000) -> Dict[str, Any]:
    async with websockets.connect(ws_url, max_size=None) as ws:
        target_id = await get_first_page_target(ws)
        if not target_id:
            raise RuntimeError("No page target found")
        session_id = await attach_to_target(ws, target_id)
        # Enable Page domain and navigate
        await session_call(ws, session_id, "Page.enable")
        await session_call(ws, session_id, "Page.navigate", {"url": url})
        # Wait for load event (best-effort)
        try:
            await asyncio.wait_for(_wait_load(ws, session_id), timeout=timeout_ms/1000)
        except asyncio.TimeoutError:
            pass
        # Read title & url
        doc = await session_call(ws, session_id, "Runtime.evaluate", {
            "expression": "({ title: document.title, href: location.href })",
            "returnByValue": True,
        })
        val = (doc or {}).get("result", {}).get("value", {})
        return {"title": val.get("title"), "url": val.get("href")}

async def _wait_load(ws, session_id: str):
    # Listen for Page.loadEventFired once; simple event loop
    while True:
        raw = await ws.recv()
        msg = json.loads(raw)
        if msg.get("method") == "Page.loadEventFired" and msg.get("sessionId") == session_id:
            return
