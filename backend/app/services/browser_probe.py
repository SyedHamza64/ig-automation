import asyncio
import json
import logging
from typing import Dict, Any
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

logger = logging.getLogger(__name__)

async def _probe_once(ws_url: str) -> Dict[str, Any]:
    """Connect directly to Chrome DevTools Protocol via WebSocket without Playwright."""
    logger.info(f"Starting direct CDP probe with WS URL: {ws_url}")
    
    try:
        # Connect directly to the CDP WebSocket endpoint
        async with websockets.connect(ws_url) as websocket:
            logger.info("Successfully connected to CDP WebSocket")
            
            # Get browser version and user agent
            version_response = await send_cdp_command(websocket, "Browser.getVersion")
            user_agent = version_response.get("result", {}).get("userAgent", "Unknown")
            logger.info(f"Retrieved user agent: {user_agent}")
            
            # Get available targets
            targets_response = await send_cdp_command(websocket, "Target.getTargets")
            targets = targets_response.get("result", {}).get("targetInfos", [])
            
            if not targets:
                raise Exception("No targets found in browser")
            
            # Find the first page target (not background pages)
            page_target = None
            for target in targets:
                if target.get("type") == "page" and not target.get("url", "").startswith("chrome-"):
                    page_target = target
                    break
            
            if not page_target:
                # If no page target found, use the first available target
                page_target = targets[0]
            
            target_id = page_target["targetId"]
            page_title = page_target.get("title", "Unknown")
            page_url = page_target.get("url", "Unknown")
            
            logger.info(f"Using target: {target_id} (type: {page_target.get('type')}, title: {page_title}, url: {page_url})")
            
            return {
                "user_agent": user_agent,
                "page_title": page_title,
                "page_url": page_url,
            }
            
    except (ConnectionClosed, WebSocketException) as e:
        logger.error(f"WebSocket connection failed: {e}")
        raise Exception(f"CDP WebSocket connection failed: {e}")
    except Exception as e:
        logger.error(f"CDP probe failed: {e}")
        raise Exception(f"CDP probe failed: {e}")

async def send_cdp_command(websocket, method: str, params: dict = None) -> dict:
    """Send a CDP command and wait for response"""
    command_id = int(asyncio.get_event_loop().time() * 1000)  # Simple unique ID
    message = {
        "id": command_id,
        "method": method,
        "params": params or {}
    }
    
    await websocket.send(json.dumps(message))
    logger.debug(f"Sent CDP command: {method}")
    
    # Wait for response
    while True:
        response = await websocket.recv()
        data = json.loads(response)
        
        # Check if this is the response to our command
        if data.get("id") == command_id:
            if "error" in data:
                raise Exception(f"CDP command {method} failed: {data['error']}")
            logger.debug(f"Received CDP response for {method}")
            return data
        
        # Ignore other messages (events, etc.)
        continue

async def probe_cdp(ws_url: str, timeout_sec: float = 7.0) -> Dict[str, Any]:
    """Enforce a global timeout so the API never hangs indefinitely"""
    logger.info(f"Starting probe with {timeout_sec}s timeout")
    return await asyncio.wait_for(_probe_once(ws_url), timeout=timeout_sec)
