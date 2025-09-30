import httpx
from typing import Any, Dict
from app.core.config import settings


BASE = getattr(settings, "BULKCREATE_BASE_URL", "http://127.0.0.1:4000").rstrip("/")


async def list_profiles() -> Dict[str, Any]:
    url = f"{BASE}/api/profiles"
    async with httpx.AsyncClient(timeout=15) as x:
        r = await x.get(url)
        r.raise_for_status()
        return r.json()


async def create_profile(name: str, config: Dict[str, Any] | None = None, enhanced: bool = False, anti_detection: Dict[str, Any] | None = None) -> Dict[str, Any]:
    url = f"{BASE}/api/profiles"
    payload: Dict[str, Any] = {"name": name, "config": config or {}, "enhancedMode": enhanced}
    if anti_detection is not None:
        payload["antiDetection"] = anti_detection
    async with httpx.AsyncClient(timeout=60) as x:
        r = await x.post(url, json=payload)
        r.raise_for_status()
        return r.json()


async def launch_cdp(name: str, enhanced: bool | None = None) -> Dict[str, Any]:
    url = f"{BASE}/api/profiles/launch-cdp"
    payload: Dict[str, Any] = {"name": name}
    if enhanced is not None:
        payload["enhanced"] = enhanced
    async with httpx.AsyncClient(timeout=150) as x:
        r = await x.post(url, json=payload)
        r.raise_for_status()
        return r.json()


async def close(name: str) -> Dict[str, Any]:
    url = f"{BASE}/api/profiles/close"
    async with httpx.AsyncClient(timeout=30) as x:
        r = await x.post(url, json={"name": name})
        r.raise_for_status()
        return r.json()


