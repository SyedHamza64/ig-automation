from fastapi import APIRouter, Depends, HTTPException, Query
import logging
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.auth import require_admin
from app.models.account import Account
from app.services.cdp import navigate
import asyncio
from urllib.parse import urlparse
from app.services.ig_probe import check_login_state
from fastapi import Body
from app.services.actions import ensure_profile_ws, CDPClient
from app.services.ig_login import login_once

router = APIRouter()
log = logging.getLogger(__name__)

def _normalize_url(u: str) -> str:
    if "://" not in u:
        return "https://" + u
    return u

@router.post("/visit", dependencies=[Depends(require_admin)])
async def visit(profile_id: int = Query(...), url: str = Query(...), db: Session = Depends(get_db)):
    p = db.query(Account).get(profile_id)
    if not p:
        raise HTTPException(status_code=404, detail="account not found")
    if not p.last_ws_puppeteer:
        raise HTTPException(status_code=400, detail="account has no stored WS; open it first")

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
    p = db.query(Account).get(profile_id)
    if not p:
        raise HTTPException(status_code=404, detail="account not found")
    if not p.last_ws_puppeteer:
        raise HTTPException(status_code=400, detail="account has no stored WS; open it first")

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
    p = db.query(Account).get(profile_id)
    if not p:
        raise HTTPException(status_code=404, detail="account not found")

    # Ensure a running browser profile and get a valid WS URL (auto-opens if needed)
    try:
        ws_url = await ensure_profile_ws(db, profile_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"failed to open profile: {e}")

    # Efficient flow: if already on Instagram, don't re-navigate; otherwise, go once
    try:
        async with CDPClient(ws_url) as cdp:
            sid = await cdp.get_page_session()
            try:
                current_url = await cdp.eval(sid, "location.href")
            except Exception:
                current_url = None
            log.info("check_login: ws ok; current_url=%s", current_url)
            if not (isinstance(current_url, str) and "instagram.com" in current_url):
                log.info("check_login: navigating to instagram.com")
                await cdp.goto(sid, "https://www.instagram.com/", wait="domcontent")
                await asyncio.sleep(0.6)
    except Exception as e:
        log.warning("check_login: navigation/setup issue: %s", e)

    try:
        info = await asyncio.wait_for(check_login_state(ws_url), timeout=12)
        log.info("check_login: result=%s", info)
        return {"profile_id": p.id, "login": info}
    except Exception as e:
        log.error("check_login: probe failed: %s", e)
        raise HTTPException(status_code=502, detail=f"login-state failed: {e}")