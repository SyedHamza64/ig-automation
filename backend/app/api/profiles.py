import asyncio
import traceback
import logging
import socket
import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import requests
from app.core.config import settings
from pydantic import BaseModel

from app.db.session import get_db
from app.models.profile import Profile
from app.models.account import Account
from app.services import adspower_client
from app.services.browser_probe import probe_cdp
from app.api.auth import require_admin
from app.services.actions import ensure_profile_ws, CDPClient

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/attach", dependencies=[Depends(require_admin)])
def attach_profile(account_id: int, adspower_profile_id: str, db: Session = Depends(get_db)):
    acc = db.query(Account).get(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="account not found")

    # ensure this AdsPower profile isn't already attached
    existing = db.query(Profile).filter(Profile.adspower_profile_id == adspower_profile_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="adspower_profile_id already attached")

    p = Profile(account_id=account_id, adspower_profile_id=adspower_profile_id, health="unknown")
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"id": p.id, "account_id": p.account_id, "adspower_profile_id": p.adspower_profile_id, "health": p.health}

@router.post("/{profile_db_id}/open", dependencies=[Depends(require_admin)])
async def open_profile(profile_db_id: int, db: Session = Depends(get_db)):
    p = db.query(Profile).get(profile_db_id)
    if not p:
        raise HTTPException(status_code=404, detail="profile not found")

    res = await adspower_client.open_profile(p.adspower_profile_id)

    # Heuristic: AdsPower often returns JSON with {"code":0, "data":{...}} on success.
    ok = False
    pupp_ws = None
    sel_ws = None

    if isinstance(res, dict):
        code = res.get("code")
        ok = (code == 0) or str(res.get("status_code", 200)).startswith("2")
        ws = (res.get("data") or {}).get("ws") if "data" in res else None
        if isinstance(ws, dict):
            pupp_ws = ws.get("puppeteer")
            sel_ws = ws.get("selenium")
    if ok:
        p.last_opened_at = datetime.now(timezone.utc)
        p.health = "ok"
        if pupp_ws: p.last_ws_puppeteer = pupp_ws
        if sel_ws:  p.last_ws_selenium  = sel_ws
        db.add(p); db.commit(); db.refresh(p)
        # --- QoL fallback: if AdsPower open gave no WS, fetch active info ---
        if not pupp_ws:
            try:
                url = f"{settings.ADSPOWER_BASE_URL}/api/v1/browser/active?user_id={p.adspower_profile_id}"
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    ws = data.get("data", {}).get("ws")
                    if ws:
                        p.last_ws_puppeteer = ws.get("puppeteer")
                        p.last_ws_selenium = ws.get("selenium")
                        db.add(p); db.commit(); db.refresh(p)
            except Exception as e:
                logger.warning(f"WS auto-refresh failed: {e}")
        # --- end QoL fallback ---

    return {"profile_db_id": profile_db_id, "ok": ok, "result": res}

@router.post("/{profile_db_id}/close", dependencies=[Depends(require_admin)])
async def close_profile(profile_db_id: int, db: Session = Depends(get_db)):
    p = db.query(Profile).get(profile_db_id)
    if not p:
        raise HTTPException(status_code=404, detail="profile not found")

    res = await adspower_client.close_profile(p.adspower_profile_id)
    return {"profile_db_id": profile_db_id, "result": res}

@router.get("/{profile_id}/connect-info")
def get_connect_info(profile_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    profile = db.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="profile not found")

    url = f"{settings.ADSPOWER_BASE_URL}/api/v1/browser/active?user_id={profile.adspower_profile_id}"
    try:
        resp = requests.get(url, timeout=5)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AdsPower request failed: {e}")

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=f"AdsPower returned {resp.status_code}: {resp.text}")

    try:
        data = resp.json()
    except Exception:
        raise HTTPException(status_code=502, detail=f"AdsPower did not return JSON: {resp.text[:200]}")

    if data.get("code") != 0:
        raise HTTPException(status_code=400, detail=f"AdsPower error: {data.get('msg')}")

    ws = data.get("data", {}).get("ws")
    if ws:
        profile.last_ws_puppeteer = ws.get("puppeteer")
        profile.last_ws_selenium = ws.get("selenium")
        db.commit()
        db.refresh(profile)

    return {
        "profile_db_id": profile.id,
        "adspower_profile_id": profile.adspower_profile_id,
        "health": "ok",
        "last_opened_at": profile.last_opened_at,
        "ws": {
            "puppeteer": profile.last_ws_puppeteer,
            "selenium": profile.last_ws_selenium,
        },
    }




@router.get("/{profile_db_id}/probe", dependencies=[Depends(require_admin)])
async def probe_profile(profile_db_id: int, db: Session = Depends(get_db)):
    p = db.query(Profile).get(profile_db_id)
    if not p:
        raise HTTPException(status_code=404, detail="profile not found")

    async def attempt(ws: str):
        try:
            # extra safety timeout at endpoint level
            return await asyncio.wait_for(probe_cdp(ws, timeout_sec=7.0), timeout=10.0), None
        except Exception:
            return None, traceback.format_exc(limit=5)

    # Try with stored WS first
    if p.last_ws_puppeteer:
        info, err1 = await attempt(p.last_ws_puppeteer)
        if info:
            return {
                "profile_db_id": p.id,
                "ws_puppeteer": p.last_ws_puppeteer,
                "diagnostics": info,
                "refreshed": False,
            }
    else:
        err1 = "no stored ws_puppeteer"

    # Refresh WS by opening the profile once
    res = await adspower_client.open_profile(p.adspower_profile_id)
    data = res.get("data") if isinstance(res, dict) else None
    ws = data.get("ws") if isinstance(data, dict) else None
    new_ws = ws.get("puppeteer") if isinstance(ws, dict) else None
    if not new_ws:
        raise HTTPException(
            status_code=502,
            detail={"error_message": "open returned no ws", "open_response": res, "first_error": err1},
        )

    p.last_ws_puppeteer = new_ws
    p.last_ws_selenium = ws.get("selenium") if isinstance(ws, dict) else None
    p.last_opened_at = datetime.now(timezone.utc)
    p.health = "ok"
    db.add(p); db.commit(); db.refresh(p)

    # Retry with fresh WS
    info2, err2 = await attempt(p.last_ws_puppeteer)
    if info2:
        return {
            "profile_db_id": p.id,
            "ws_puppeteer": p.last_ws_puppeteer,
            "diagnostics": info2,
            "refreshed": True,
        }

    raise HTTPException(
        status_code=502,
        detail={
            "error_message": "probe failed after reopen",
            "first_error": err1,
            "second_error": err2,
            "ws_used": p.last_ws_puppeteer,
        },
    )

@router.get("/{profile_db_id}/ws-check", dependencies=[Depends(require_admin)])
def check_ws_connectivity(profile_db_id: int, db: Session = Depends(get_db)):
    """Simple connectivity check that avoids Playwright - just tests if the WS port is listening"""
    p = db.query(Profile).get(profile_db_id)
    if not p:
        raise HTTPException(status_code=404, detail="profile not found")
    
    if not p.last_ws_puppeteer:
        return {"ok": False, "error": "no stored ws_puppeteer"}
    
    try:
        # Parse the WebSocket URL to extract host and port
        # Expected format: ws://127.0.0.1:50930/devtools/browser/...
        ws_url = p.last_ws_puppeteer
        match = re.match(r'ws://([^:]+):(\d+)/', ws_url)
        if not match:
            return {"ok": False, "error": f"invalid ws URL format: {ws_url}"}
        
        host, port = match.groups()
        port = int(port)
        
        # Try a quick TCP connection to the host:port
        with socket.create_connection((host, port), timeout=2) as sock:
            return {"ok": True, "host": host, "port": port, "ws_url": ws_url}
            
    except socket.timeout:
        return {"ok": False, "error": f"connection timeout to {host}:{port}"}
    except ConnectionRefused:
        return {"ok": False, "error": f"connection refused to {host}:{port}"}
    except Exception as e:
        return {"ok": False, "error": f"connection failed: {str(e)}"}
    
class EvalRequest(BaseModel):
    expression: str

@router.post("/{profile_id}/eval")
async def eval_js(profile_id: int, body: EvalRequest, db: Session = Depends(get_db)):
    profile = db.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="profile not found")
    ws_url = getattr(profile, "last_ws_puppeteer", None) or getattr(profile, "ws_url", None)
    if not ws_url:
        raise HTTPException(status_code=400, detail="no CDP ws; open profile first")

    # Evaluate in the first page session
    async with CDPClient(ws_url) as cdp:
        session_id = await cdp.get_page_session()
        try:
            val = await cdp.eval(session_id, body.expression)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"eval error: {e}")
    return {"value": val}