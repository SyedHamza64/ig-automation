import httpx
from app.core.config import settings

BASE = settings.ADSPOWER_BASE_URL.rstrip("/")

async def status():
    # Some installs expose /status or just a base page; we’ll hit the base and report what we see.
    url = f"{BASE}"
    try:
        async with httpx.AsyncClient(timeout=5) as x:
            r = await x.get(url)
        ct = r.headers.get("content-type", "")
        body = r.text if "text" in ct else (r.content[:200].hex() if r.content else "")
        return {"ok": r.status_code < 500, "status_code": r.status_code, "content_type": ct, "body_preview": body[:500]}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# Placeholders for next step:
async def open_profile(profile_id: str):
    url = f"{BASE}/api/v1/browser/start?user_id={profile_id}"
    async with httpx.AsyncClient(timeout=30) as x:
        r = await x.get(url)
    return _maybe_json(r)

async def close_profile(profile_id: str):
    url = f"{BASE}/api/v1/browser/stop?user_id={profile_id}"
    async with httpx.AsyncClient(timeout=30) as x:
        r = await x.get(url)
    return _maybe_json(r)

def _maybe_json(r: httpx.Response):
    if "application/json" in r.headers.get("content-type", ""):
        return r.json()
    return {"status_code": r.status_code, "text": r.text[:1000]}
