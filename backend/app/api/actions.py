from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db.session import SessionLocal
from ..schemas.actions import (
    FollowRequest, LikeRequest, DMRequest,
    ActionEnqueueResponse, ActionLogDTO, ActionType, 
    ActionRequest,
)
from ..models.action_log import ActionLog
from ..models.account_limit import AccountLimit
from ..models.account import Account
from ..models.profile import Profile
from .auth import require_admin
from ..services.actions import get_account_limits, run_action
from fastapi.responses import StreamingResponse
import json


router = APIRouter(prefix="/actions", tags=["actions"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/limits/{account_id}")
def get_limits(account_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    limits = get_account_limits(db, account_id)
    return {"account_id": account_id, "limits_json": limits}



@router.put("/limits/{account_id}")
def upsert_limits(account_id: int, body: dict, db: Session = Depends(get_db), _=Depends(require_admin)):
    limits_json = body.get("limits_json")
    if not isinstance(limits_json, dict):
        raise HTTPException(status_code=400, detail="limits_json must be an object")
    # ensure account exists
    acc = db.get(Account, account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="account not found")
    row = db.query(AccountLimit).filter(AccountLimit.account_id == account_id).one_or_none()
    if row:
        row.limits_json = limits_json
    else:
        row = AccountLimit(account_id=account_id, limits_json=limits_json)
        db.add(row)
    db.commit()
    return {"ok": True}

@router.get("/logs", response_model=List[ActionLogDTO])
def list_logs(
    account_id: Optional[int] = None,
    action_type: Optional[ActionType] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    q = db.query(ActionLog).order_by(ActionLog.id.desc())
    if account_id:
        q = q.filter(ActionLog.account_id == account_id)
    if action_type:
        q = q.filter(ActionLog.action_type == action_type.value)
    return [ActionLogDTO.model_validate(x) for x in q.limit(max(1, min(limit, 200))).all()]

@router.post("/follow", response_model=ActionEnqueueResponse)
async def do_follow(req: FollowRequest, db: Session = Depends(get_db), _=Depends(require_admin)):
    if not req.usernames and not req.target_id:
        raise HTTPException(status_code=400, detail="provide usernames or target_id")
    log = await run_action(db, "follow", req.account_id, req.profile_id, req.model_dump())
    return ActionEnqueueResponse(log_id=log.id, status=log.status)

@router.post("/unfollow")
async def do_unfollow(req: ActionRequest, db: Session = Depends(get_db)):
    log = await run_action(db, "unfollow", req.account_id, req.profile_id, req.model_dump())
    return {"log_id": log.id, "status": log.status}


@router.post("/like", response_model=ActionEnqueueResponse)
async def do_like(req: LikeRequest, db: Session = Depends(get_db), _=Depends(require_admin)):
    if not req.post_urls:
        raise HTTPException(status_code=400, detail="post_urls required for MVP")
    log = await run_action(db, "like", req.account_id, req.profile_id, req.model_dump())
    return ActionEnqueueResponse(log_id=log.id, status=log.status)

@router.post("/like-recent")
async def do_like_recent(req: ActionRequest, db: Session = Depends(get_db), _=Depends(require_admin)):
    if not req.usernames:
        raise HTTPException(status_code=400, detail="usernames required")
    # Log as "like" to avoid enum/migration changes
    log = await run_action(db, "like", req.account_id, req.profile_id, req.model_dump())
    return {"log_id": log.id, "status": log.status}

@router.post("/dm", response_model=ActionEnqueueResponse)
async def do_dm(req: DMRequest, db: Session = Depends(get_db), _=Depends(require_admin)):
    if not req.usernames:
        raise HTTPException(status_code=400, detail="usernames required")
    log = await run_action(db, "dm", req.account_id, req.profile_id, req.model_dump())
    return ActionEnqueueResponse(log_id=log.id, status=log.status)

from fastapi import Depends
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..models.action_log import ActionLog

@router.get("/actions/logs/{log_id}")
def get_log(log_id: int, db: Session = Depends(get_db)):
    log = db.get(ActionLog, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Not Found")
    return {
        "id": log.id,
        "status": log.status,
        "action_type": log.action_type,
        "payload": log.payload,
        "error": log.error_message,
        "created_at": log.created_at,
    }

@router.get("/actions/logs")
def list_logs(limit: int = 10, db: Session = Depends(get_db)):
    q = db.query(ActionLog).order_by(ActionLog.id.desc()).limit(limit).all()
    return [
        {
            "id": log.id,
            "status": log.status,
            "action_type": log.action_type,
            "payload": log.payload,
            "error": log.error_message,
            "created_at": log.created_at,
        }
        for log in q
    ]


# -------------------- Streaming mass follow/unfollow (SSE) --------------------
from ..services.actions import ensure_profile_ws, perform_mass_follow_stream
from ..services.warmup import perform_warmup_stream
import random
from ..core.security import decode_token
from ..models.user import User
import logging
log = logging.getLogger("app.api.actions.mass_stream")


@router.get("/mass-follow-stream")
async def mass_follow_stream(
    account_id: int,
    profile_id: int,
    username: str,
    mode: str = "follow",  # or "unfollow"
    limit: int = 50,
    percent: int | None = None,
    max_scrolls: int = 200,
    section: str = "followers",  # or "following"
    debug_dom: bool = False,
    db: Session = Depends(get_db),
    _=Depends(require_admin)
):
    try:
        ws_url = ensure_profile_ws(db, profile_id)
    except Exception as e:
        log.exception("ensure_profile_ws failed")
        async def error_gen():
            yield f"data: {json.dumps({'type':'error','message':f'ws_error: {str(e)}'})}\n\n"
            yield f"data: {json.dumps({'type':'done','reason':'error'})}\n\n"
        return StreamingResponse(error_gen(), media_type="text/event-stream")

    async def event_generator():
        try:
            start = {"type":"start","account_id":account_id,"profile_id":profile_id,"username":username,"mode":mode}
            log.info("mass-stream start %s", start)
            yield f"data: {json.dumps(start)}\n\n"
            async for ev in perform_mass_follow_stream(ws_url, username, mode, limit=limit, percent=percent, max_scrolls=max_scrolls, section=section, debug_dom=debug_dom):
                log.debug("mass-stream ev %s", ev)
                yield f"data: {json.dumps(ev)}\n\n"
        except Exception as e:
            log.exception("mass-stream crashed")
            yield f"data: {json.dumps({'type':'error','message':str(e)})}\n\n"
        finally:
            yield f"data: {json.dumps({'type':'done','reason':'closed'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# Alternate SSE endpoint that accepts a JWT via query param (for EventSource)
@router.get("/mass-follow-stream-open")
async def mass_follow_stream_open(
    account_id: int,
    profile_id: int,
    username: str,
    mode: str = "follow",
    limit: int = 50,
    percent: int | None = None,
    max_scrolls: int = 200,
    section: str = "followers",
    debug_dom: bool = False,
    token: str | None = None,
    db: Session = Depends(get_db),
):
    # Manual auth because EventSource cannot send headers
    if not token:
        async def _err_missing():
            yield f"data: {json.dumps({'type':'error','message':'missing token'})}\n\n"
            yield f"data: {json.dumps({'type':'done','reason':'error'})}\n\n"
        return StreamingResponse(_err_missing(), media_type="text/event-stream")
    try:
        payload = decode_token(token)
        if not payload or "sub" not in payload:
            raise ValueError("invalid token")
        user = db.get(User, int(payload["sub"]))
        if not user or not user.is_admin:
            raise ValueError("unauthorized")
    except Exception as _:
        async def _err_unauth():
            yield f"data: {json.dumps({'type':'error','message':'unauthorized'})}\n\n"
            yield f"data: {json.dumps({'type':'done','reason':'error'})}\n\n"
        return StreamingResponse(_err_unauth(), media_type="text/event-stream")

    try:
        ws_url = ensure_profile_ws(db, profile_id)
    except Exception as e:
        log.exception("ensure_profile_ws failed")
        async def error_gen():
            yield f"data: {json.dumps({'type':'error','message':f'ws_error: {str(e)}'})}\n\n"
            yield f"data: {json.dumps({'type':'done','reason':'error'})}\n\n"
        return StreamingResponse(error_gen(), media_type="text/event-stream")

    async def event_generator():
        try:
            start = {"type":"start","account_id":account_id,"profile_id":profile_id,"username":username,"mode":mode}
            log.info("mass-stream-open start %s", start)
            yield f"data: {json.dumps(start)}\n\n"
            async for ev in perform_mass_follow_stream(ws_url, username, mode, limit=limit, percent=percent, max_scrolls=max_scrolls, section=section, debug_dom=debug_dom):
                log.debug("mass-stream-open ev %s", ev)
                yield f"data: {json.dumps(ev)}\n\n"
        except Exception as e:
            log.exception("mass-stream-open crashed")
            yield f"data: {json.dumps({'type':'error','message':str(e)})}\n\n"
        finally:
            yield f"data: {json.dumps({'type':'done','reason':'closed'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# -------------------- Warmup SSE --------------------
@router.get("/warmup-stream")
async def warmup_stream(
    account_id: int,
    profile_id: int,
    duration_sec: int = 75,
    max_likes: int = -1,
    content: str = "home",
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    try:
        ws_url = ensure_profile_ws(db, profile_id)
    except Exception as e:
        async def error_gen():
            yield f"data: {json.dumps({'type':'error','message':f'ws_error: {str(e)}'})}\n\n"
            yield f"data: {json.dumps({'type':'done','reason':'error'})}\n\n"
        return StreamingResponse(error_gen(), media_type="text/event-stream")

    # Resolve randomized duration if requested (<= 0 means pick 60-90s)
    resolved_duration = duration_sec if duration_sec and duration_sec > 0 else random.randint(60, 90)

    async def event_generator():
        try:
            async for ev in perform_warmup_stream(ws_url, duration_sec=resolved_duration, max_likes=max_likes, content=content):
                yield f"data: {json.dumps(ev)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type':'error','message':str(e)})}\n\n"
        finally:
            yield f"data: {json.dumps({'type':'done','reason':'closed'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Alternate warmup SSE endpoint that accepts JWT via query param (for EventSource)
@router.get("/warmup-stream-open")
async def warmup_stream_open(
    account_id: int,
    profile_id: int,
    duration_sec: int = 75,
    max_likes: int = -1,
    content: str = "home",
    token: str | None = None,
    db: Session = Depends(get_db),
):
    # Manual auth
    if not token:
        async def _err_missing():
            yield f"data: {json.dumps({'type':'error','message':'missing token'})}\n\n"
            yield f"data: {json.dumps({'type':'done','reason':'error'})}\n\n"
        return StreamingResponse(_err_missing(), media_type="text/event-stream")
    try:
        payload = decode_token(token)
        if not payload or "sub" not in payload:
            raise ValueError("invalid token")
        user = db.get(User, int(payload["sub"]))
        if not user or not user.is_admin:
            raise ValueError("unauthorized")
    except Exception:
        async def _err_unauth():
            yield f"data: {json.dumps({'type':'error','message':'unauthorized'})}\n\n"
            yield f"data: {json.dumps({'type':'done','reason':'error'})}\n\n"
        return StreamingResponse(_err_unauth(), media_type="text/event-stream")

    # resolve WS and duration
    try:
        ws_url = ensure_profile_ws(db, profile_id)
    except Exception as e:
        async def error_gen():
            yield f"data: {json.dumps({'type':'error','message':f'ws_error: {str(e)}'})}\n\n"
            yield f"data: {json.dumps({'type':'done','reason':'error'})}\n\n"
        return StreamingResponse(error_gen(), media_type="text/event-stream")

    resolved_duration = duration_sec if duration_sec and duration_sec > 0 else random.randint(60, 90)

    async def event_generator():
        try:
            async for ev in perform_warmup_stream(ws_url, duration_sec=resolved_duration, max_likes=max_likes, content=content):
                yield f"data: {json.dumps(ev)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type':'error','message':str(e)})}\n\n"
        finally:
            yield f"data: {json.dumps({'type':'done','reason':'closed'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
