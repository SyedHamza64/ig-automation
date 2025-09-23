from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone

from app.db.session import get_db
from app.models.account import Account
from app.models.action_log import ActionLog
from app.models.account_limit import AccountLimit
from app.models.profile import Profile
from app.schemas.account import AccountCreate, AccountUpdate, AccountOut
from app.api.auth import require_admin  # <-- guard
from app.services.actions import get_account_limits

router = APIRouter()

# ----- WRITE (protected) -----
@router.post("/", response_model=AccountOut, status_code=201, dependencies=[Depends(require_admin)])
def create_account(payload: AccountCreate, db: Session = Depends(get_db)):
    existing = db.query(Account).filter(Account.handle == payload.handle).first()
    if existing:
        raise HTTPException(status_code=409, detail="handle already exists")
    acc = Account(
        handle=payload.handle,
        timezone=payload.timezone,
        status=payload.status,
        limits_json=payload.limits_json or {},
    )
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return acc

@router.patch("/{account_id}", response_model=AccountOut, dependencies=[Depends(require_admin)])
def update_account(account_id: int, payload: AccountUpdate, db: Session = Depends(get_db)):
    acc = db.query(Account).get(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="account not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(acc, k, v)
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return acc

@router.delete("/{account_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_account(account_id: int, db: Session = Depends(get_db)):
    acc = db.query(Account).get(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="account not found")
    db.delete(acc)
    db.commit()
    return

# ----- READ (public) -----
@router.get("/", response_model=List[Dict[str, Any]])
def list_accounts(
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="search by handle prefix"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    # Join with profiles to get profile_id and adspower_profile_id
    query = db.query(
        Account.id,
        Account.handle,
        Profile.id.label('profile_id'),
        Profile.adspower_profile_id
    ).outerjoin(Profile, Account.id == Profile.account_id)
    
    if q:
        query = query.filter(Account.handle.ilike(f"{q}%"))
    
    rows = query.order_by(Account.id.desc()).offset(offset).limit(limit).all()
    
    return [
        {
            "id": row.id,
            "handle": row.handle,
            "profile_id": row.profile_id,
            "adspower_profile_id": row.adspower_profile_id
        }
        for row in rows
    ]

@router.get("/{account_id}", response_model=AccountOut)
def get_account(account_id: int, db: Session = Depends(get_db)):
    acc = db.query(Account).get(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="account not found")
    return acc

@router.get("/{account_id}/stats")
def get_account_stats(
    account_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get daily action counts and success rate for an account"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Daily action counts
    daily_stats = db.query(
        func.date(ActionLog.created_at).label('date'),
        ActionLog.action_type,
        func.count().label('count')
    ).filter(
        ActionLog.account_id == account_id,
        ActionLog.created_at >= since
    ).group_by(
        func.date(ActionLog.created_at), ActionLog.action_type
    ).all()
    
    # Format as nested dict
    result = {
        "likes_per_day": {},
        "follows_per_day": {},
        "unfollows_per_day": {},
        "success_rate": 0,
        "today_count": {"like": 0, "follow": 0, "unfollow": 0}
    }
    
    for row in daily_stats:
        date_str = row.date.isoformat()
        if row.action_type == "like":
            result["likes_per_day"][date_str] = row.count
        elif row.action_type == "follow":
            result["follows_per_day"][date_str] = row.count
        elif row.action_type == "unfollow":
            result["unfollows_per_day"][date_str] = row.count
    
    # Success rate over last 100 logs
    recent_logs = db.query(ActionLog).filter(
        ActionLog.account_id == account_id
    ).order_by(ActionLog.created_at.desc()).limit(100).all()
    
    if recent_logs:
        success_count = sum(1 for log in recent_logs if log.status == "success")
        result["success_rate"] = round((success_count / len(recent_logs)) * 100, 1)
    
    # Today's counts
    today = datetime.now(timezone.utc).date()
    today_stats = db.query(
        ActionLog.action_type,
        func.count().label('count')
    ).filter(
        ActionLog.account_id == account_id,
        func.date(ActionLog.created_at) == today
    ).group_by(ActionLog.action_type).all()
    
    for row in today_stats:
        result["today_count"][row.action_type] = row.count
    
    return result

@router.get("/{account_id}/recent-actions")
def get_recent_actions(
    account_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Get recent actions for an account with parsed target usernames"""
    logs = db.query(ActionLog).filter(
        ActionLog.account_id == account_id
    ).order_by(ActionLog.created_at.desc()).limit(limit).all()
    
    results = []
    for log in logs:
        # Extract target usernames from payload
        target_usernames = []
        if log.payload and isinstance(log.payload, dict):
            # Direct usernames in payload
            if "usernames" in log.payload:
                target_usernames.extend(log.payload["usernames"])
            
            # Usernames in result.results
            if "result" in log.payload and isinstance(log.payload["result"], dict):
                result_data = log.payload["result"]
                if "results" in result_data and isinstance(result_data["results"], list):
                    for r in result_data["results"]:
                        if isinstance(r, dict) and "username" in r:
                            target_usernames.append(r["username"])
        
        results.append({
            "id": log.id,
            "created_at": log.created_at.isoformat(),
            "action_type": log.action_type,
            "status": log.status,
            "error_message": log.error_message,
            "profile_id": log.profile_id,
            "targets": list(set(target_usernames))  # dedupe
        })
    
    return results

@router.get("/{account_id}/limits")
def get_account_limits_status(
    account_id: int,
    db: Session = Depends(get_db)
):
    """Get account limits configuration and usage"""
    try:
        # Get configured limits
        limits = get_account_limits(db, account_id)
        configured = limits
    except:
        configured = None
    
    # Calculate used today
    today = datetime.now(timezone.utc).date()
    used_today = db.query(
        ActionLog.action_type,
        func.count().label('count')
    ).filter(
        ActionLog.account_id == account_id,
        func.date(ActionLog.created_at) == today
    ).group_by(ActionLog.action_type).all()
    
    used_dict = {row.action_type: row.count for row in used_today}
    
    # Calculate remaining if configured
    remaining = {}
    if configured:
        for action in ["like", "follow", "unfollow", "dm"]:
            per_day = configured.get(action, {}).get("per_day", 0)
            used = used_dict.get(action, 0)
            remaining[action] = max(0, per_day - used)
    
    return {
        "configured": configured,
        "used_today": used_dict,
        "remaining": remaining
    }


@router.get("/{account_id}/adspower", tags=["profiles"])
def account_adspower_info(account_id: int, db: Session = Depends(get_db)):
    acc: Optional[Account] = db.query(Account).get(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="account not found")
    if not acc.profile_id:
        raise HTTPException(status_code=400, detail="account has no profile_id linked")

    client = AdsPowerClient()
    info = client.get_profile_info(str(acc.profile_id))
    return {"account_id": acc.id, "profile_id": acc.profile_id, "adspower": info}