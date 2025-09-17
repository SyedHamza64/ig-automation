from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.auth import require_admin
from app.models.profile import Profile
from app.services.cdp import navigate
import asyncio
from urllib.parse import urlparse
from app.services.ig_probe import check_login_state
from fastapi import Body
from app.services.ig_login import login_once

router = APIRouter()

def _normalize_url(u: str) -> str:
    if "://" not in u:
        return "https://" + u
    return u

@router.post("/visit", dependencies=[Depends(require_admin)])
async def visit(profile_id: int = Query(...), url: str = Query(...), db: Session = Depends(get_db)):
    p = db.query(Profile).get(profile_id)
    if not p:
        raise HTTPException(status_code=404, detail="profile not found")
    if not p.last_ws_puppeteer:
        raise HTTPException(status_code=400, detail="profile has no stored WS; open it first")

    url = _normalize_url(url)
    # very basic guard
    try:
        urlparse(url)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid URL")

    try:
        info = await asyncio.wait_for(navigate(p.last_ws_puppeteer, url), timeout=20)
        return {"profile_id": p.id, "navigated_to": info}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"navigation failed: {e}")
    
@router.post("/login", dependencies=[Depends(require_admin)])
async def do_login(
    profile_id: int = Query(...),
    payload: dict = Body(...)
    , db: Session = Depends(get_db)
):
    """
    One-time helper to submit Instagram login form via CDP.
    Does NOT store credentials. Use it only to seed the AdsPower profile cookies.
    payload = { "username": "...", "password": "..." }
    """
    p = db.query(Profile).get(profile_id)
    if not p:
        raise HTTPException(status_code=404, detail="profile not found")
    if not p.last_ws_puppeteer:
        raise HTTPException(status_code=400, detail="profile has no stored WS; open it first")

    username = payload.get("username")
    password = payload.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="username/password required")

    try:
        # submit login
        res = await asyncio.wait_for(login_once(p.last_ws_puppeteer, username, password), timeout=25)
        # re-check state
        st = await asyncio.wait_for(check_login_state(p.last_ws_puppeteer), timeout=12)
        return {
            "profile_id": p.id,
            "submitted": res.get("submitted"),
            "after_submit": res.get("after"),
            "login_state": st,
            "note": "If state is 'checkpoint', complete 2FA/checkpoint manually in the AdsPower window."
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"login failed: {e}")

@router.get("/login-state", dependencies=[Depends(require_admin)])
async def login_state(profile_id: int, db: Session = Depends(get_db)):
    p = db.query(Profile).get(profile_id)
    if not p:
        raise HTTPException(status_code=404, detail="profile not found")
    if not p.last_ws_puppeteer:
        raise HTTPException(status_code=400, detail="profile has no stored WS; open it first")

    try:
        info = await asyncio.wait_for(check_login_state(p.last_ws_puppeteer), timeout=12)
        return {"profile_id": p.id, "login": info}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"login-state failed: {e}")