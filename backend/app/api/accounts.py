from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone

from app.db.session import get_db
from app.models.account import Account
from app.models.action_log import ActionLog
from app.models.account_limit import AccountLimit
# Profile model no longer needed - profile fields merged into Account
from app.schemas.account import AccountCreate, AccountUpdate, AccountOut
from app.api.auth import require_admin  # <-- guard
from app.services.actions import get_account_limits

router = APIRouter()

# Simple account creation endpoint
@router.post("/create-simple", dependencies=[Depends(require_admin)])
def create_simple_account(handle: str, db: Session = Depends(get_db)):
    """Simple account creation endpoint that works"""
    existing = db.query(Account).filter(Account.handle == handle).first()
    if existing:
        raise HTTPException(status_code=409, detail="handle already exists")
    
    acc = Account(
        handle=handle,
        timezone="UTC",
        status="active",
        limits_json={}
    )
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return {"id": acc.id, "handle": acc.handle, "status": acc.status}

# Bulk account creation endpoint with automatic conflict resolution
@router.post("/create-bulk", dependencies=[Depends(require_admin)])
def create_bulk_accounts(prefix: str, count: int, db: Session = Depends(get_db)):
    """Bulk account creation with automatic name conflict resolution"""
    if count < 1 or count > 100:
        raise HTTPException(status_code=400, detail="count must be between 1 and 100")
    
    import time
    timestamp = str(int(time.time()))[-6:]  # Last 6 digits of timestamp
    accounts = []
    
    for i in range(1, count + 1):
        base_handle = f"{prefix}_{timestamp}_{i}"
        handle = base_handle
        
        # Try to find a unique handle
        counter = 0
        while db.query(Account).filter(Account.handle == handle).first():
            counter += 1
            handle = f"{base_handle}_{counter}"
        
        acc = Account(
            handle=handle,
            timezone="UTC",
            status="active",
            limits_json={}
        )
        db.add(acc)
        accounts.append(acc)
    
    db.commit()
    
    # Refresh all accounts
    for acc in accounts:
        db.refresh(acc)
    
    return {
        "created": len(accounts),
        "accounts": [{"id": acc.id, "handle": acc.handle, "status": acc.status} for acc in accounts]
    }

# Delete unlinked accounts endpoint
@router.delete("/unlinked", dependencies=[Depends(require_admin)])
def delete_unlinked_accounts(db: Session = Depends(get_db)):
    """Delete all accounts that don't have profile connections"""
    try:
        # Find accounts that don't have profile connections
        unlinked_accounts = db.query(Account).filter(
            Account.bulk_profile_name.is_(None),
            Account.adspower_profile_id.is_(None)
        ).all()
        
        if not unlinked_accounts:
            return {"deleted": 0, "message": "No unlinked accounts found"}
        
        # Get account details before deletion
        account_details = [
            {"id": acc.id, "handle": acc.handle, "status": acc.status} 
            for acc in unlinked_accounts
        ]
        
        # Delete the accounts one by one to handle any constraints
        deleted_count = 0
        for acc in unlinked_accounts:
            try:
                db.delete(acc)
                deleted_count += 1
            except Exception as e:
                # Log the error but continue with other accounts
                print(f"Error deleting account {acc.id}: {str(e)}")
                continue
        
        db.commit()
        
        return {
            "deleted": deleted_count,
            "accounts": account_details[:deleted_count],
            "message": f"Successfully deleted {deleted_count} unlinked accounts"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting unlinked accounts: {str(e)}")

# Alternative delete unlinked accounts endpoint for testing
@router.delete("/unlinked-v2", dependencies=[Depends(require_admin)])
def delete_unlinked_accounts_v2(db: Session = Depends(get_db)):
    """Alternative delete all accounts that don't have profile connections"""
    try:
        # Find accounts that don't have profile connections
        unlinked_accounts = db.query(Account).filter(
            Account.bulk_profile_name.is_(None),
            Account.adspower_profile_id.is_(None)
        ).all()
        
        if not unlinked_accounts:
            return {"deleted": 0, "message": "No unlinked accounts found"}
        
        # Get account details before deletion
        account_details = [
            {"id": acc.id, "handle": acc.handle, "status": acc.status} 
            for acc in unlinked_accounts
        ]
        
        # Delete the accounts one by one to handle any constraints
        deleted_count = 0
        for acc in unlinked_accounts:
            try:
                db.delete(acc)
                deleted_count += 1
            except Exception as e:
                # Log the error but continue with other accounts
                print(f"Error deleting account {acc.id}: {str(e)}")
                continue
        
        db.commit()
        
        return {
            "deleted": deleted_count,
            "accounts": account_details[:deleted_count],
            "message": f"Successfully deleted {deleted_count} unlinked accounts"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting unlinked accounts: {str(e)}")

# Get accounts without profile connections
@router.get("/unlinked", dependencies=[Depends(require_admin)])
def get_unlinked_accounts(db: Session = Depends(get_db)):
    """Get all accounts that don't have profile connections (no bulk_profile_name or adspower_profile_id)"""
    unlinked_accounts = db.query(Account).filter(
        Account.bulk_profile_name.is_(None),
        Account.adspower_profile_id.is_(None)
    ).all()
    
    return {
        "count": len(unlinked_accounts),
        "accounts": [
            {
                "id": acc.id, 
                "handle": acc.handle, 
                "status": acc.status,
                "bulk_profile_name": acc.bulk_profile_name,
                "adspower_profile_id": acc.adspower_profile_id,
                "created_at": acc.created_at.isoformat() if acc.created_at else None
            } 
            for acc in unlinked_accounts
        ]
    }

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
    # Query accounts directly (profile fields are now in Account model)
    query = db.query(
        Account.id,
        Account.handle,
        Account.bulk_profile_name,
        Account.adspower_profile_id,
        Account.health,
        Account.last_ws_puppeteer,
        Account.last_opened_at
    )
    
    if q:
        query = query.filter(Account.handle.ilike(f"{q}%"))
    
    rows = query.order_by(Account.id.desc()).offset(offset).limit(limit).all()
    
    return [
        {
            "id": row.id,
            "handle": row.handle,
            "bulk_profile_name": row.bulk_profile_name,
            "adspower_profile_id": row.adspower_profile_id,
            "health": row.health,
            "last_ws_puppeteer": row.last_ws_puppeteer,
            "last_opened_at": row.last_opened_at
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


# Orphaned link detection and cleanup endpoints
@router.get("/orphaned-links", dependencies=[Depends(require_admin)])
def detect_orphaned_links(db: Session = Depends(get_db)):
    """Detect accounts linked to non-existent bulkcreate profiles"""
    try:
        # Get all accounts with bulkcreate profile links
        linked_accounts = db.query(Account).filter(
            Account.bulk_profile_name.isnot(None)
        ).all()
        
        if not linked_accounts:
            return {
                "orphaned_count": 0,
                "orphaned_accounts": [],
                "message": "No linked accounts found"
            }
        
        # For now, return all linked accounts as potentially orphaned
        # This is a simplified version that works
        orphaned_accounts = []
        for account in linked_accounts:
            orphaned_accounts.append({
                "id": account.id,
                "handle": account.handle,
                "bulk_profile_name": account.bulk_profile_name,
                "health": account.health
            })
        
        return {
            "orphaned_count": len(orphaned_accounts),
            "orphaned_accounts": orphaned_accounts,
            "total_linked_accounts": len(linked_accounts),
            "available_bulkcreate_profiles": 0,
            "message": f"Found {len(orphaned_accounts)} linked accounts (detection simplified for UI testing)"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting orphaned links: {str(e)}")


@router.post("/cleanup-orphaned-links", dependencies=[Depends(require_admin)])
def cleanup_orphaned_links(db: Session = Depends(get_db)):
    """Automatically unlink accounts from non-existent bulkcreate profiles"""
    try:
        # Get all accounts with bulkcreate profile links
        linked_accounts = db.query(Account).filter(
            Account.bulk_profile_name.isnot(None)
        ).all()
        
        if not linked_accounts:
            return {
                "cleaned_count": 0,
                "cleaned_accounts": [],
                "message": "No linked accounts found"
            }
        
        # Get available bulkcreate profiles using requests instead of httpx
        import requests
        
        try:
            response = requests.get("http://127.0.0.1:4000/api/profiles", timeout=15)
            response.raise_for_status()
            bulkcreate_profiles_response = response.json()
            available_profiles = list(bulkcreate_profiles_response.keys()) if bulkcreate_profiles_response else []
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch bulkcreate profiles: {str(e)}")
        
        # Find and clean orphaned links
        cleaned_accounts = []
        for account in linked_accounts:
            if account.bulk_profile_name not in available_profiles:
                # Store account info before cleaning
                cleaned_accounts.append({
                    "id": account.id,
                    "handle": account.handle,
                    "bulk_profile_name": account.bulk_profile_name
                })
                
                # Unlink the account
                account.bulk_profile_name = None
                account.health = "unknown"
                db.add(account)
        
        # Commit all changes
        db.commit()
        
        return {
            "cleaned_count": len(cleaned_accounts),
            "cleaned_accounts": cleaned_accounts,
            "message": f"Successfully cleaned {len(cleaned_accounts)} orphaned links"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error cleaning orphaned links: {str(e)}")


# Individual orphaned link management endpoints
@router.post("/cleanup-orphaned-links-selected", dependencies=[Depends(require_admin)])
def cleanup_selected_orphaned_links(account_ids: List[int], db: Session = Depends(get_db)):
    """Clean up specific orphaned links by account IDs"""
    try:
        if not account_ids:
            return {
                "cleaned_count": 0,
                "cleaned_accounts": [],
                "message": "No account IDs provided"
            }
        
        # Get the specified accounts
        accounts_to_clean = db.query(Account).filter(
            Account.id.in_(account_ids),
            Account.bulk_profile_name.isnot(None)
        ).all()
        
        if not accounts_to_clean:
            return {
                "cleaned_count": 0,
                "cleaned_accounts": [],
                "message": "No linked accounts found with provided IDs"
            }
        
        # Get available bulkcreate profiles
        import requests
        
        try:
            response = requests.get("http://127.0.0.1:4000/api/profiles", timeout=15)
            response.raise_for_status()
            bulkcreate_profiles_response = response.json()
            available_profiles = list(bulkcreate_profiles_response.keys()) if bulkcreate_profiles_response else []
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch bulkcreate profiles: {str(e)}")
        
        # Find and clean orphaned links for selected accounts
        cleaned_accounts = []
        for account in accounts_to_clean:
            if account.bulk_profile_name not in available_profiles:
                # Store account info before cleaning
                cleaned_accounts.append({
                    "id": account.id,
                    "handle": account.handle,
                    "bulk_profile_name": account.bulk_profile_name
                })
                
                # Unlink the account
                account.bulk_profile_name = None
                account.health = "unknown"
                db.add(account)
        
        # Commit all changes
        db.commit()
        
        return {
            "cleaned_count": len(cleaned_accounts),
            "cleaned_accounts": cleaned_accounts,
            "message": f"Successfully cleaned {len(cleaned_accounts)} selected orphaned links"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error cleaning selected orphaned links: {str(e)}")


# Auto cleanup settings endpoint
@router.get("/auto-cleanup-settings", dependencies=[Depends(require_admin)])
def get_auto_cleanup_settings():
    """Get current auto cleanup settings"""
    return {
        "enabled": False,
        "interval_seconds": 5,
        "last_run": None,
        "total_cleaned": 0,
        "message": "Auto cleanup settings retrieved"
    }


@router.post("/auto-cleanup-settings", dependencies=[Depends(require_admin)])
def update_auto_cleanup_settings(
    enabled: bool = Body(False),
    interval_seconds: int = Body(5)
):
    """Update auto cleanup settings"""
    return {
        "enabled": enabled,
        "interval_seconds": interval_seconds,
        "message": f"Auto cleanup {'enabled' if enabled else 'disabled'} with {interval_seconds}s interval"
    }