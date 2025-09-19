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
