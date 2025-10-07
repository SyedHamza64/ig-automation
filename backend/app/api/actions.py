from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import update
import asyncio

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


@router.get("/limits")
def get_all_accounts_limits(db: Session = Depends(get_db), _=Depends(require_admin)):
    """Get limits for all accounts"""
    from app.services.actions import DEFAULT_LIMITS
    
    # Get all accounts
    accounts = db.query(Account).all()
    
    # Get all account limits
    limits_rows = db.query(AccountLimit).all()
    limits_by_account = {row.account_id: row.limits_json for row in limits_rows}
    
    result = []
    for account in accounts:
        account_limits = limits_by_account.get(account.id, {})
        # Merge with defaults
        merged_limits = {**DEFAULT_LIMITS, **account_limits}
        
        result.append({
            "account_id": account.id,
            "handle": account.handle,
            "status": account.status,
            "limits": merged_limits,
            "has_custom_limits": bool(account_limits)
        })
    
    return {"accounts": result}


@router.post("/limits/{account_id}/reset")
def reset_account_limits(account_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    """Reset account limits to defaults"""
    # ensure account exists
    acc = db.get(Account, account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="account not found")
    
    # Remove custom limits (will fall back to defaults)
    row = db.query(AccountLimit).filter(AccountLimit.account_id == account_id).one_or_none()
    if row:
        db.delete(row)
        db.commit()
    
    return {"ok": True, "message": "Account limits reset to defaults"}

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
from ..db.session import get_db, SessionLocal
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
from ..services.actions import ensure_profile_ws, perform_mass_follow_stream, _now
from ..services.warmup import perform_reels_warmup
import random
from ..core.security import decode_token
from ..models.user import User
import logging
from sqlalchemy import update
log = logging.getLogger("app.api.actions.mass_stream")


@router.get("/mass-follow-stream")
async def mass_follow_stream(
    account_id: int,
    profile_id: int,
    username: str,
    mode: str = "follow",  # or "unfollow"
    limit: int = 50,
    percent: int | None = None,
    max_scrolls: int = 50,  # Reduced default
    section: str = "followers",  # or "following"
    debug_dom: bool = False,
    max_duration_minutes: int = 10,  # Maximum 10 minutes
    db: Session = Depends(get_db),
    _=Depends(require_admin)
):
    # Create an ActionLog to reflect this streaming job
    log_row = ActionLog(
        account_id=account_id,
        profile_id=profile_id,
        action_type=("unfollow" if mode == "unfollow" else "follow"),
        payload={
            "mode": mode,
            "username": username,
            "limit": limit,
            "section": section,
        },
        status="running",
        started_at=_now(),
    )
    db.add(log_row)
    db.commit()

    try:
        ws_url = await ensure_profile_ws(db, profile_id)
    except Exception as e:
        log.exception("ensure_profile_ws failed")
        async def error_gen():
            yield f"data: {json.dumps({'type':'error','message':f'ws_error: {str(e)}'})}\n\n"
            yield f"data: {json.dumps({'type':'done','reason':'error'})}\n\n"
            # Update log as error
            try:
                # Use raw SQL to update the log
                import json as json_module
                from sqlalchemy import text
                sql = text("""
                UPDATE action_logs 
                SET status = 'error', 
                    error_message = :error_message, 
                    finished_at = :finished_at 
                WHERE id = :log_id
                """)
                db.execute(sql, {
                    "error_message": f"ws_error: {str(e)}", 
                    "finished_at": _now(), 
                    "log_id": log_row.id
                })
                db.commit()
            except Exception:
                pass
        return StreamingResponse(error_gen(), media_type="text/event-stream")

    async def event_generator():
        upd_db = SessionLocal()
        try:
            start = {"type":"start","account_id":account_id,"profile_id":profile_id,"username":username,"mode":mode}
            log.info("mass-stream start %s", start)
            yield f"data: {json.dumps(start)}\n\n"
            acted = 0
            processed = 0
            scrolls = 0
            last_progress = asyncio.get_event_loop().time()
            
            # Initialize variables for finalization
            final_acted = 0
            final_processed = 0
            final_scrolls = 0

            async def watchdog():
                try:
                    log.info(f"Watchdog started for log {log_id}")
                    await asyncio.sleep(3)  # Wait 3 seconds
                    log.info(f"Watchdog timeout reached for log {log_id}")
                    # Force finalize after timeout
                    try:
                        status = "success" if acted > 0 else "error"
                        base_payload = {}
                        base_payload["result"] = {"acted": acted, "processed": processed, "scrolls": scrolls, "mode": mode, "username": username, "section": section, "reason": "watchdog_timeout"}
                        stmt = (
                            update(ActionLog)
                            .where(ActionLog.id == log_id)
                            .values(status=status, payload=base_payload, finished_at=_now())
                        )
                        upd_db.execute(stmt)
                        upd_db.commit()
                        log.info(f"Watchdog finalized log {log_id} as {status}")
                    except Exception as e:
                        log.error(f"Watchdog failed: {e}")
                except Exception as e:
                    log.error(f"Watchdog exception: {e}")

            wd_task = asyncio.create_task(watchdog())
            try:
                async for ev in perform_mass_follow_stream(ws_url, username, mode, limit=limit, percent=percent, max_scrolls=max_scrolls, section=section, debug_dom=debug_dom, max_duration_minutes=max_duration_minutes):
                    log.debug("mass-stream ev %s", ev)
                    if isinstance(ev, dict):
                        acted = ev.get("acted", acted)
                        processed = ev.get("processed", processed)
                        scrolls = ev.get("scrolls", scrolls)
                        last_progress = asyncio.get_event_loop().time()

                        # Update final values for finalization
                        if ev.get("type") in ("action", "scroll", "dwell", "start"):
                            final_acted = acted
                            final_processed = processed
                            final_scrolls = scrolls
                            # Persist progress periodically
                            try:
                                base_payload = {}
                                base_payload["result"] = {"acted": acted, "processed": processed, "scrolls": scrolls, "mode": mode, "username": username, "section": section}
                                stmt = (
                                    update(ActionLog)
                                    .where(ActionLog.id == log_id)
                                    .values(payload=base_payload)
                                )
                                upd_db.execute(stmt)
                                upd_db.commit()
                            except Exception:
                                pass
                        if ev.get("type") == "done":
                            # Update log to success BEFORE emitting done
                            try:
                                base_payload = {}
                                base_payload["result"] = {"acted": acted, "processed": processed, "scrolls": scrolls, "mode": mode, "username": username, "section": section, "reason": ev.get("reason")}
                                stmt = (
                                    update(ActionLog)
                                    .where(ActionLog.id == log_id)
                                    .values(status="success", payload=base_payload, finished_at=_now())
                                )
                                upd_db.execute(stmt)
                                upd_db.commit()
                            except Exception:
                                pass
                    # Always forward events to client
                    try:
                        yield f"data: {json.dumps(ev)}\n\n"
                    except Exception:
                        pass
            except Exception as e:
                log.exception("mass-stream crashed")
                yield f"data: {json.dumps({'type':'error','message':str(e)})}\n\n"
                try:
                    stmt = (
                        update(ActionLog)
                        .where(ActionLog.id == log_id)
                        .values(status="error", error_message=str(e), finished_at=_now())
                    )
                    upd_db.execute(stmt)
                    upd_db.commit()
                except Exception:
                    pass
        finally:
            log.info(f"Stream finally block executing for log {log_id}")
            yield f"data: {json.dumps({'type':'done','reason':'closed'})}\n\n"
            # Always finalize - mark success with a compact summary if not already error
            try:
                base_payload = {}
                base_payload["result"] = {"acted": final_acted, "processed": final_processed, "scrolls": final_scrolls, "mode": mode, "username": username, "section": section, "reason": "stream_closed"}
                stmt = (
                    update(ActionLog)
                    .where(ActionLog.id == log_id)
                    .values(status="success", payload=base_payload, finished_at=_now())
                )
                upd_db.execute(stmt)
                upd_db.commit()
                log.info(f"Stream finalized log {log_id} as success")
            except Exception as e:
                log.error(f"Stream finalization failed: {e}")
            try:
                # Wait for watchdog to complete or cancel it
                if not wd_task.done():
                    wd_task.cancel()
                    try:
                        await wd_task
                    except asyncio.CancelledError:
                        pass
                upd_db.close()
            except Exception:
                pass

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
    max_scrolls: int = 50,  # Reduced default
    section: str = "followers",
    debug_dom: bool = False,
    max_duration_minutes: int = 10,  # Maximum 10 minutes
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

    # Create an ActionLog to reflect this streaming job
    log_row = ActionLog(
        account_id=account_id,
        profile_id=profile_id,
        action_type=("unfollow" if mode == "unfollow" else "follow"),
        payload={
            "mode": mode,
            "username": username,
            "limit": limit,
            "section": section,
        },
        status="running",
        started_at=_now(),
    )
    db.add(log_row)
    db.commit()

    try:
        ws_url = await ensure_profile_ws(db, profile_id)
    except Exception as e:
        log.exception("ensure_profile_ws failed")
        async def error_gen():
            yield f"data: {json.dumps({'type':'error','message':f'ws_error: {str(e)}'})}\n\n"
            yield f"data: {json.dumps({'type':'done','reason':'error'})}\n\n"
            try:
                from app.db.session import SessionLocal
                update_db = SessionLocal()
                try:
                    stmt = (
                        update(ActionLog)
                        .where(ActionLog.id == log_row.id)
                        .values(
                            status="error",
                            error_message=f"ws_error: {str(e)}",
                            finished_at=_now()
                        )
                    )
                    update_db.execute(stmt)
                    update_db.commit()
                finally:
                    update_db.close()
            except Exception:
                pass
        return StreamingResponse(error_gen(), media_type="text/event-stream")

    # Store log_row.id before async context to avoid session issues
    log_id = log_row.id
    
    async def event_generator():
        try:
            start = {"type":"start","account_id":account_id,"profile_id":profile_id,"username":username,"mode":mode}
            log.info("mass-stream-open start %s", start)
            yield f"data: {json.dumps(start)}\n\n"
            
            # Use the same streaming logic for all limits, including limit=1
            # This ensures proper modal opening and user following
            
            # For limit > 1, use the streaming approach
            upd_db = SessionLocal()
            try:
                acted = 0
                processed = 0
                scrolls = 0
                last_progress = asyncio.get_event_loop().time()
                
                # Initialize variables for finalization
                final_acted = 0
                final_processed = 0
                final_scrolls = 0

                async def watchdog():
                    try:
                        log.info(f"Watchdog started for log {log_id}")
                        await asyncio.sleep(3)  # Wait 3 seconds
                        log.info(f"Watchdog timeout reached for log {log_id}")
                        # Force finalize after timeout
                        try:
                            status = "success" if acted > 0 else "error"
                            base_payload = {}
                            base_payload["result"] = {"acted": acted, "processed": processed, "scrolls": scrolls, "mode": mode, "username": username, "section": section, "reason": "watchdog_timeout"}
                            stmt = (
                                update(ActionLog)
                                .where(ActionLog.id == log_id)
                                .values(status=status, payload=base_payload, finished_at=_now())
                            )
                            upd_db.execute(stmt)
                            upd_db.commit()
                            log.info(f"Watchdog finalized log {log_id} as {status}")
                        except Exception as e:
                            log.error(f"Watchdog failed: {e}")
                    except Exception as e:
                        log.error(f"Watchdog exception: {e}")

                wd_task = asyncio.create_task(watchdog())
                try:
                    async for ev in perform_mass_follow_stream(ws_url, username, mode, limit=limit, percent=percent, max_scrolls=max_scrolls, section=section, debug_dom=debug_dom, max_duration_minutes=max_duration_minutes):
                        log.debug("mass-stream-open ev %s", ev)
                        try:
                            if isinstance(ev, dict):
                                acted = ev.get("acted", acted)
                                processed = ev.get("processed", processed)
                                scrolls = ev.get("scrolls", scrolls)
                                last_progress = asyncio.get_event_loop().time()
                                
                                # Update final values for finalization
                                final_acted = acted
                                final_processed = processed
                                final_scrolls = scrolls
                                if ev.get("type") in ("action", "scroll", "dwell"):
                                    try:
                                        base_payload = {}
                                        base_payload["result"] = {"acted": acted, "processed": processed, "scrolls": scrolls, "mode": mode, "username": username, "section": section}
                                        stmt = (
                                            update(ActionLog)
                                            .where(ActionLog.id == log_id)
                                            .values(payload=base_payload)
                                        )
                                        upd_db.execute(stmt)
                                        upd_db.commit()
                                    except Exception:
                                        pass
                                if ev.get("type") == "done":
                                    # Update log to success BEFORE emitting done
                                    try:
                                        base_payload = {}
                                        base_payload["result"] = {"acted": acted, "processed": processed, "scrolls": scrolls, "mode": mode, "username": username, "section": section, "reason": ev.get("reason")}
                                        stmt = (
                                            update(ActionLog)
                                            .where(ActionLog.id == log_id)
                                            .values(status="success", payload=base_payload, finished_at=_now())
                                        )
                                        upd_db.execute(stmt)
                                        upd_db.commit()
                                    except Exception:
                                        pass
                        except Exception:
                            pass
                        yield f"data: {json.dumps(ev)}\n\n"
                except Exception as e:
                    log.exception("mass-stream-open crashed")
                    yield f"data: {json.dumps({'type':'error','message':str(e)})}\n\n"
                    try:
                        stmt = (
                            update(ActionLog)
                            .where(ActionLog.id == log_id)
                            .values(status="error", error_message=str(e), finished_at=_now())
                        )
                        upd_db.execute(stmt)
                        upd_db.commit()
                    except Exception:
                        pass
                finally:
                    # Force-finalize using the main DB session to avoid session scope issues
                    try:
                        base_payload = {}
                        summary = {
                            "acted": final_acted if 'final_acted' in locals() else 0,
                            "processed": final_processed if 'final_processed' in locals() else 0,
                            "scrolls": final_scrolls if 'final_scrolls' in locals() else 0,
                            "mode": mode,
                            "username": username,
                            "section": section,
                            "reason": ("stream_closed_no_actions" if ((final_acted if 'final_acted' in locals() else 0) == 0) else "stream_closed")
                        }
                        base_payload["result"] = summary
                        # Use raw SQL to ensure the update happens
                        import json as json_module
                        sql = """
                        UPDATE action_logs 
                        SET status = 'success', 
                            payload = %s, 
                            finished_at = %s 
                        WHERE id = %s
                        """
                        db.execute(sql, (json_module.dumps(base_payload), _now(), log_id))
                        db.commit()
                    except Exception as e:
                        log.error(f"finalize (open) failed: {e}")
                    # Emit done to client after DB is finalized
                    yield f"data: {json.dumps({'type':'done','reason':'closed'})}\n\n"
                    # Wait for watchdog to complete or cancel it
                    if not wd_task.done():
                        wd_task.cancel()
                        try:
                            await wd_task
                        except asyncio.CancelledError:
                            pass
                    upd_db.close()
            except Exception as e:
                log.exception("streaming section failed")
                yield f"data: {json.dumps({'type':'error','message':str(e)})}\n\n"
                yield f"data: {json.dumps({'type':'done','reason':'error'})}\n\n"
        except Exception as e:
            log.exception("event_generator failed")
            yield f"data: {json.dumps({'type':'error','message':str(e)})}\n\n"
            yield f"data: {json.dumps({'type':'done','reason':'error'})}\n\n"

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
        ws_url = await ensure_profile_ws(db, profile_id)
    except Exception as e:
        async def error_gen():
            yield f"data: {json.dumps({'type':'error','message':f'ws_error: {str(e)}'})}\n\n"
            yield f"data: {json.dumps({'type':'done','reason':'error'})}\n\n"
        return StreamingResponse(error_gen(), media_type="text/event-stream")

    # Resolve randomized duration if requested (<= 0 means pick 60-90s)
    resolved_duration = duration_sec if duration_sec and duration_sec > 0 else random.randint(60, 90)

    # Create an ActionLog to track warmup session
    log_row = ActionLog(
        account_id=account_id,
        profile_id=profile_id,
        action_type="warmup",
        payload={
            "duration_sec": resolved_duration,
            "max_likes": max_likes,
            "content": content,
        },
        status="running",
        started_at=_now(),
    )
    db.add(log_row)
    db.commit()
    log_id = log_row.id

    async def event_generator():
        total_likes = 0
        logged_likes = 0  # Track how many likes we've already logged
        # Get account limits for rate limiting
        from ..services.actions import get_account_limits, rate_limit_guard
        limits = get_account_limits(db, account_id)
        
        try:
            async for ev in perform_reels_warmup(ws_url, duration_sec=resolved_duration, max_likes=max_likes):
                # Log individual likes to database for usage statistics
                if ev.get("type") == "liked":
                    current_count = ev.get("count", total_likes)
                    # Only log new likes (when count increases)
                    if current_count > logged_likes:
                        new_likes = current_count - logged_likes
                        logged_likes = current_count
                        total_likes = current_count
                        
                        # Check limits and log each new like
                        for i in range(new_likes):
                            try:
                                rate_limit_guard(db, account_id, "like", limits)
                                # Create a separate ActionLog entry for each like
                                like_log = ActionLog(
                                    account_id=account_id,
                                    profile_id=profile_id,
                                    action_type="like",
                                    payload={
                                        "source": "warmup",
                                        "warmup_session_id": log_id,
                                        "like_number": logged_likes - new_likes + i + 1,
                                        "total_likes": logged_likes,
                                    },
                                    status="success",
                                    started_at=_now(),
                                )
                                db.add(like_log)
                                db.commit()
                            except HTTPException as e:
                                # Rate limited - stop logging more likes for this session
                                yield f"data: {json.dumps({**ev, 'rate_limited': True, 'message': str(e.detail)})}\n\n"
                                break
                    else:
                        total_likes = current_count
                    
                    yield f"data: {json.dumps(ev)}\n\n"
                else:
                    yield f"data: {json.dumps(ev)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type':'error','message':str(e)})}\n\n"
        finally:
            # Finalize the warmup session log
            try:
                stmt = (
                    update(ActionLog)
                    .where(ActionLog.id == log_id)
                    .values(
                        status="success",
                        payload={
                            "duration_sec": resolved_duration,
                            "max_likes": max_likes,
                            "content": content,
                            "total_likes": total_likes,
                            "result": {"total_likes": total_likes, "duration": resolved_duration}
                        }
                    )
                )
                db.execute(stmt)
                db.commit()
            except Exception:
                pass
            yield f"data: {json.dumps({'type':'done','reason':'closed', 'total_likes': total_likes})}\n\n"

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
        ws_url = await ensure_profile_ws(db, profile_id)
    except Exception as e:
        async def error_gen():
            yield f"data: {json.dumps({'type':'error','message':f'ws_error: {str(e)}'})}\n\n"
            yield f"data: {json.dumps({'type':'done','reason':'error'})}\n\n"
        return StreamingResponse(error_gen(), media_type="text/event-stream")

    resolved_duration = duration_sec if duration_sec and duration_sec > 0 else random.randint(60, 90)

    async def event_generator():
        try:
            async for ev in perform_reels_warmup(ws_url, duration_sec=resolved_duration, max_likes=max_likes):
                yield f"data: {json.dumps(ev)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type':'error','message':str(e)})}\n\n"
        finally:
            yield f"data: {json.dumps({'type':'done','reason':'closed'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
