import asyncio
import traceback
import logging
import socket
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import requests
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.config import settings
from app.db.session import get_db
from app.models.profile import Profile
from app.models.account import Account
from app.services import bulkcreate_client
from app.services.browser_probe import probe_cdp
from app.api.auth import require_admin
from app.services.actions import ensure_profile_ws, CDPClient

logger = logging.getLogger(__name__)

# ✅ SINGLE router for the whole module
router = APIRouter(tags=["profiles"])

# ---------- LIST (your existing working endpoint) ----------
@router.get("")
def list_profiles(
    linked: Optional[bool] = None,               # ⬅️ NEW
    db: Session = Depends(get_db),
):
    q = db.query(Profile).outerjoin(Account, Profile.account_id == Account.id)

    if linked is True:
        q = q.filter(Profile.account_id.isnot(None))
    elif linked is False:
        q = q.filter(Profile.account_id.is_(None))

    rows = q.all()
    return [
        {
            "id": p.id,
            "account_id": p.account_id,
            "account_handle": getattr(p.account, "handle", None) if p.account else None,
            "adspower_profile_id": p.adspower_profile_id,
            "bulk_profile_name": getattr(p, "bulk_profile_name", None),
            "health": p.health,
            "last_ws_puppeteer": p.last_ws_puppeteer,
        }
        for p in rows
    ]

# ---------- LOOKUP BY BULK NAME (read-only) ----------
@router.get("/by-bulk/{bulk_name}")
def get_by_bulk(bulk_name: str, db: Session = Depends(get_db)):
    name = (bulk_name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="bulk_name required")
    p: Optional[Profile] = (
        db.query(Profile)
        .outerjoin(Account, Profile.account_id == Account.id)
        .filter(Profile.bulk_profile_name == name)
        .first()
    )
    if not p:
        return {"linked": False, "bulk_profile_name": name}
    return {
        "linked": True,
        "bulk_profile_name": name,
        "profile_db_id": p.id,
        "account_id": p.account_id,
        "account_handle": getattr(p.account, "handle", None) if p.account else None,
        "health": p.health,
        "last_ws_puppeteer": p.last_ws_puppeteer,
    }

# ---------- CREATE BULK PROFILE ROW (no account) ----------
class CreateBulkIn(BaseModel):
    bulk_profile_name: str


@router.post("/create-bulk", dependencies=[Depends(require_admin)])
def create_bulk_profile(
    payload: CreateBulkIn,
    db: Session = Depends(get_db),
):
    try:
        name = (payload.bulk_profile_name or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="bulk_profile_name required")
        
        # Check if profile already exists
        existing = db.query(Profile).filter(Profile.bulk_profile_name == name).first()
        if existing:
            return {
                "id": existing.id,
                "account_id": existing.account_id,
                "bulk_profile_name": existing.bulk_profile_name,
                "health": existing.health,
                "already": True,
            }
        
        # Create new profile
        p = Profile(account_id=None, bulk_profile_name=name, health="unknown")
        db.add(p)
        db.commit()
        db.refresh(p)
        
        return {
            "id": p.id,
            "account_id": p.account_id,
            "bulk_profile_name": p.bulk_profile_name,
            "health": p.health,
            "already": False,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("create-bulk failed")
        raise HTTPException(status_code=500, detail=f"create-bulk failed: {str(e)}")

# ---------- COMPARE (new) ----------
@router.post("/compare")
def compare_profiles(
    ids: List[str] = Body(..., embed=True),  # expects {"ids": ["k14wf88c", "k14gx5jn", ...]}
    db: Session = Depends(get_db),
):
    norm_ids = [i.strip() for i in ids if i and str(i).strip()]
    if not norm_ids:
        return {"linked": [], "unlinked": []}

    rows = (
        db.query(Profile)
        .outerjoin(Account, Profile.account_id == Account.id)
        .filter(Profile.adspower_profile_id.in_(norm_ids))
        .all()
    )

    found_map = {p.adspower_profile_id: p for p in rows}
    linked: List[Dict[str, Any]] = []
    for p in rows:
        linked.append({
            "adspower_profile_id": p.adspower_profile_id,
            "profile_db_id": p.id,
            "account_id": p.account_id,
            "account_handle": getattr(p.account, "handle", None) if p.account else None,
            "health": p.health,
            "last_ws_puppeteer": p.last_ws_puppeteer,
        })

    unlinked = [i for i in norm_ids if i not in found_map]

    return {"linked": linked, "unlinked": unlinked}

# ---------- LOOKUP BY ADSPower ID ----------
@router.get("/by-adspower/{adspower_id}")
def get_by_adspower(adspower_id: str, db: Session = Depends(get_db)):
    p: Optional[Profile] = (
        db.query(Profile)
        .outerjoin(Account, Profile.account_id == Account.id)
        .filter(Profile.adspower_profile_id == adspower_id)
        .first()
    )
    if not p:
        return {"linked": False, "adspower_profile_id": adspower_id}
    return {
        "linked": True,
        "adspower_profile_id": adspower_id,
        "profile_db_id": p.id,
        "account_id": p.account_id,
        "account_handle": getattr(p.account, "handle", None) if p.account else None,
        "health": p.health,
        "last_ws_puppeteer": p.last_ws_puppeteer,
    }

# ---------- ATTACH & DETACH ----------
@router.post("/attach", dependencies=[Depends(require_admin)])
def attach_profile(
    account_id: int,
    adspower_profile_id: str,
    force: bool = False,
    db: Session = Depends(get_db),
):
    acc = db.query(Account).get(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="account not found")

    # global uniqueness of AdsPower id
    existing_by_adsp = db.query(Profile).filter(Profile.adspower_profile_id == adspower_profile_id).first()
    if existing_by_adsp and existing_by_adsp.account_id not in (None, account_id):
        raise HTTPException(status_code=409, detail=f"adspower_profile_id already attached to account_id={existing_by_adsp.account_id}")

    current = db.query(Profile).filter(Profile.account_id == account_id).first()
    if current and not force:
        raise HTTPException(
            status_code=409,
            detail=f"account_id {account_id} already linked to {current.adspower_profile_id} (profile_db_id={current.id}); pass force=true to swap",
        )

    if existing_by_adsp:
        existing_by_adsp.account_id = account_id
        db.add(existing_by_adsp); db.commit(); db.refresh(existing_by_adsp)
        if current and current.id != existing_by_adsp.id:
            current.account_id = None
            db.add(current); db.commit()
        p = existing_by_adsp
    else:
        p = Profile(account_id=account_id, adspower_profile_id=adspower_profile_id, health="unknown")
        db.add(p); db.commit(); db.refresh(p)
        if current and current.id != p.id:
            current.account_id = None
            db.add(current); db.commit()

    return {
        "id": p.id,
        "account_id": p.account_id,
        "adspower_profile_id": p.adspower_profile_id,
        "health": p.health,
        "swapped": bool(current),
    }


@router.post("/{profile_db_id}/detach", dependencies=[Depends(require_admin)])
def detach_profile(profile_db_id: int, db: Session = Depends(get_db)):
    p = db.query(Profile).get(profile_db_id)
    if not p:
        raise HTTPException(status_code=404, detail="profile not found")
    if p.account_id is None:
        return {"id": p.id, "account_id": None, "adspower_profile_id": p.adspower_profile_id, "detached": False, "reason": "already unlinked"}
    old = p.account_id
    p.account_id = None
    db.add(p); db.commit(); db.refresh(p)
    return {"id": p.id, "account_id": None, "adspower_profile_id": p.adspower_profile_id, "detached": True, "was_linked_to": old}


# ---------- OPEN ----------
@router.post("/{profile_db_id}/open", dependencies=[Depends(require_admin)])
async def open_profile(profile_db_id: int, db: Session = Depends(get_db)):
    p = db.query(Profile).get(profile_db_id)  # or db.get(Profile, profile_db_id)
    if not p:
        raise HTTPException(status_code=404, detail="profile not found")

    # Bulkcreate integration (exclusive)
    bulk_name = p.bulk_profile_name or p.adspower_profile_id
    if not bulk_name:
        raise HTTPException(status_code=400, detail="profile not linked to a bulkcreate name")

    # Try to obtain WS with retries (handles slow Chrome startup and already-running cases)
    ws: Optional[str] = None
    last_err: Optional[str] = None
    for i in range(45):  # ~90s total (45 * 2s)
        try:
            logger.info(f"Attempt {i+1}/45: calling bulkcreate_client.launch_cdp for {bulk_name}")
            res = await bulkcreate_client.launch_cdp(bulk_name)
            logger.info(f"bulkcreate response: {res}")
            ws = (res or {}).get("ws")
            if ws:
                logger.info(f"Got WS: {ws}")
                break
        except Exception as e:
            last_err = str(e)
            logger.error(f"Attempt {i+1} failed: {e}")
        await asyncio.sleep(2)
    if not ws:
        logger.error(f"No WS after 45 attempts. Last error: {last_err}")
        raise HTTPException(status_code=502, detail={"error": "no ws returned after retries", "last_error": last_err})

    p.last_opened_at = datetime.now(timezone.utc)
    p.health = "ok"
    p.last_ws_puppeteer = ws
    db.add(p); db.commit(); db.refresh(p)
    return {"profile_db_id": profile_db_id, "ok": True, "ws": ws}


# ---------- ATTACH BULK (link a bulkcreate profile name) ----------
@router.post("/attach-bulk", dependencies=[Depends(require_admin)])
def attach_bulk_profile(
    account_id: int | None = Body(None),
    bulk_profile_name: str = Body(...),
    force: bool = Body(False),
    db: Session = Depends(get_db),
):
    try:
        logger.info(f"attach-bulk called with account_id={account_id}, bulk_profile_name='{bulk_profile_name}', force={force}")
        name = (bulk_profile_name or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="bulk_profile_name required")

        # If linking to an account, update the Account model directly
        if account_id is not None:
            logger.info(f"Looking up account with id={account_id}")
            acc = db.query(Account).get(account_id)
            if not acc:
                logger.error(f"Account with id={account_id} not found")
                raise HTTPException(status_code=404, detail="account not found")

            logger.info(f"Found account: {acc.handle}, current bulk_profile_name='{acc.bulk_profile_name}'")

            # Check if account already has a profile linked
            if acc.bulk_profile_name and not force:
                logger.warning(f"Account {account_id} already linked to profile, force={force}")
                raise HTTPException(status_code=409, detail=f"account_id {account_id} already linked to profile; pass force=true to swap")

            # Check if bulk_profile_name is already used by another account
            existing_account = db.query(Account).filter(Account.bulk_profile_name == name).first()
            if existing_account and existing_account.id != account_id:
                logger.warning(f"bulk_profile_name '{name}' already attached to account_id={existing_account.id}")
                raise HTTPException(status_code=409, detail=f"bulk_profile_name '{name}' already attached to account_id={existing_account.id}")

            # Update the account with the bulk profile name
            logger.info(f"Updating account {account_id} with bulk_profile_name='{name}'")
            acc.bulk_profile_name = name
            acc.health = "unknown"
            db.add(acc)
            db.commit()
            db.refresh(acc)

            logger.info(f"Successfully linked account {account_id} to bulk profile '{name}'")
            return {
                "id": acc.id,
                "account_id": acc.id,
                "bulk_profile_name": acc.bulk_profile_name,
                "health": acc.health,
            }
        else:
            # No account specified: just return the bulk profile name
            logger.info(f"No account specified, returning bulk profile name '{name}'")
            return {
                "id": None,
                "account_id": None,
                "bulk_profile_name": name,
                "health": "unknown",
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"attach-bulk failed with error: {str(e)}")
        raise HTTPException(status_code=500, detail="attach-bulk failed; see server logs")

# ---------- CLOSE ----------
@router.post("/{profile_db_id}/close", dependencies=[Depends(require_admin)])
async def close_profile(profile_db_id: int, db: Session = Depends(get_db)):
    p = db.query(Profile).get(profile_db_id)
    if not p:
        raise HTTPException(status_code=404, detail="profile not found")
    res = await adspower_client.close_profile(p.adspower_profile_id)
    return {"profile_db_id": profile_db_id, "result": res}

# ---------- CONNECT INFO ----------
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

# ---------- PROBE ----------
@router.get("/{profile_db_id}/probe", dependencies=[Depends(require_admin)])
async def probe_profile(profile_db_id: int, db: Session = Depends(get_db)):
    p = db.query(Profile).get(profile_db_id)
    if not p:
        raise HTTPException(status_code=404, detail="profile not found")

    async def attempt(ws: str):
        try:
            return await asyncio.wait_for(probe_cdp(ws, timeout_sec=7.0), timeout=10.0), None
        except Exception:
            return None, traceback.format_exc(limit=5)

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

# ---------- WS CHECK ----------
@router.get("/{profile_db_id}/ws-check", dependencies=[Depends(require_admin)])
def check_ws_connectivity(profile_db_id: int, db: Session = Depends(get_db)):
    p = db.query(Profile).get(profile_db_id)
    if not p:
        raise HTTPException(status_code=404, detail="profile not found")
    if not p.last_ws_puppeteer:
        return {"ok": False, "error": "no stored ws_puppeteer"}

    try:
        ws_url = p.last_ws_puppeteer
        match = re.match(r'ws://([^:]+):(\d+)/', ws_url)
        if not match:
            return {"ok": False, "error": f"invalid ws URL format: {ws_url}"}
        host, port = match.groups()
        port = int(port)
        with socket.create_connection((host, port), timeout=2):
            return {"ok": True, "host": host, "port": port, "ws_url": ws_url}
    except socket.timeout:
        return {"ok": False, "error": f"connection timeout to {host}:{port}"}
    except ConnectionRefused:
        return {"ok": False, "error": f"connection refused to {host}:{port}"}
    except Exception as e:
        return {"ok": False, "error": f"connection failed: {str(e)}"}

# ---------- EVAL ----------
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

    async with CDPClient(ws_url) as cdp:
        session_id = await cdp.get_page_session()
        try:
            val = await cdp.eval(session_id, body.expression)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"eval error: {e}")
    return {"value": val}

# ---------- DELETE ----------
# app/api/profiles.py
@router.delete("/{profile_db_id}", dependencies=[Depends(require_admin)])
def delete_profile(profile_db_id: int, db: Session = Depends(get_db)):
    p = db.query(Profile).get(profile_db_id)  # or db.get(Profile, profile_db_id)
    if not p:
        raise HTTPException(status_code=404, detail="profile not found")
    db.delete(p)
    db.commit()
    return {"deleted_id": profile_db_id}

# ---------- UNLINK ----------
@router.post("/{profile_id}/unlink", dependencies=[Depends(require_admin)])
async def unlink_profile(profile_id: int, db: Session = Depends(get_db)):
    """Unlink a profile from its bulkcreate profile and account."""
    try:
        profile = db.query(Profile).get(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="profile not found")
        
        # Store the bulk profile name for logging
        bulk_name = profile.bulk_profile_name
        
        # Unlink from bulkcreate and account
        profile.bulk_profile_name = None
        profile.account_id = None
        profile.last_ws_puppeteer = None
        profile.last_ws_selenium = None
        profile.health = "unknown"
        
        db.add(profile)
        db.commit()
        db.refresh(profile)
        
        logger.info(f"Unlinked profile {profile_id} from bulkcreate profile: {bulk_name}")
        return {"profile_id": profile_id, "unlinked": True, "bulk_profile_name": bulk_name}
        
    except Exception as e:
        logger.error(f"Error unlinking profile {profile_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Delete unused profiles endpoint
@router.delete("/unused", dependencies=[Depends(require_admin)])
def delete_unused_profiles(db: Session = Depends(get_db)):
    """Delete all profiles that have no meaningful connections (no account_id, no bulk_profile_name, no adspower_profile_id)"""
    try:
        # Find profiles with no meaningful connections
        unused_profiles = db.query(Profile).filter(
            Profile.account_id.is_(None),
            Profile.bulk_profile_name.is_(None),
            Profile.adspower_profile_id.is_(None)
        ).all()
        
        if not unused_profiles:
            return {"deleted": 0, "message": "No unused profiles found"}
        
        # Get profile details before deletion
        profile_details = [
            {"id": p.id, "health": p.health, "created_at": p.created_at} 
            for p in unused_profiles
        ]
        
        # Delete the profiles
        deleted_count = 0
        for profile in unused_profiles:
            try:
                db.delete(profile)
                deleted_count += 1
            except Exception as e:
                logger.warning(f"Error deleting profile {profile.id}: {e}")
                continue
        
        db.commit()
        
        return {
            "deleted": deleted_count,
            "profiles": profile_details[:deleted_count],
            "message": f"Successfully deleted {deleted_count} unused profiles"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting unused profiles: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting unused profiles: {str(e)}")
