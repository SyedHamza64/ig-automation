import httpx
from typing import Any, Dict, Optional
from app.core.config import settings

BASE = settings.ADSPOWER_BASE_URL.rstrip("/")

async def status() -> Dict[str, Any]:
    """
    Quick probe to check AdsPower service is up.
    Some installs expose /status or just a base page; we hit the base and report.
    """
    url = f"{BASE}"
    try:
        async with httpx.AsyncClient(timeout=5) as x:
            r = await x.get(url)
        ct = r.headers.get("content-type", "")
        body = r.text if "text" in ct else (r.content[:200].hex() if r.content else "")
        return {
            "ok": r.status_code < 500,
            "status_code": r.status_code,
            "content_type": ct,
            "body_preview": body[:500],
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def open_profile(profile_id: str) -> Dict[str, Any]:
    url = f"{BASE}/api/v1/browser/start?user_id={profile_id}"
    async with httpx.AsyncClient(timeout=30) as x:
        r = await x.get(url)
    return _maybe_json(r)


async def close_profile(profile_id: str) -> Dict[str, Any]:
    url = f"{BASE}/api/v1/browser/stop?user_id={profile_id}"
    async with httpx.AsyncClient(timeout=30) as x:
        r = await x.get(url)
    return _maybe_json(r)


async def get_profile_info(profile_id: str) -> Dict[str, Any]:
    """
    Query AdsPower for profile details / status.
    Adjust the endpoint to match your AdsPower API.
    """
    url = f"{BASE}/api/v1/profile/get"
    try:
        async with httpx.AsyncClient(timeout=10) as x:
            r = await x.get(url, params={"profile_id": profile_id})
        return _maybe_json(r)
    except Exception as e:
        return {"error": str(e), "profile_id": profile_id}


async def get_status() -> Dict[str, Any]:
    """
    Optional: check AdsPower /status endpoint if available.
    """
    url = f"{BASE}/status"
    try:
        async with httpx.AsyncClient(timeout=5) as x:
            r = await x.get(url)
        return _maybe_json(r)
    except Exception as e:
        return {"error": str(e)}


def _maybe_json(r: httpx.Response) -> Dict[str, Any]:
    if "application/json" in r.headers.get("content-type", ""):
        return r.json()
    return {"status_code": r.status_code, "text": r.text[:500]}
