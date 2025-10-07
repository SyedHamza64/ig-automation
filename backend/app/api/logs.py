# app/api/logs.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.db.session import get_db
from app.models.action_log import ActionLog
from datetime import datetime, timezone
from sqlalchemy import update

router = APIRouter()

@router.get("", response_model=List[dict])
def list_logs(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=200),
    account_id: Optional[int] = None,
    action: Optional[str] = None,
    status: Optional[str] = None,
):
    q = db.query(ActionLog)
    if account_id is not None:
        q = q.filter(ActionLog.account_id == account_id)
    if action:
        q = q.filter(ActionLog.action_type == action)
    if status:
        q = q.filter(ActionLog.status == status)

    rows = q.order_by(ActionLog.created_at.desc()).limit(limit).all()

    results = []
    for r in rows:
        # Extract result from payload JSON
        payload = getattr(r, "payload", None) or {}
        extracted_result = None
        if isinstance(payload, dict):
            extracted_result = payload.get("result") or payload.get("results")

        # If the row is 'running' but we have a result payload, surface it as 'success'.
        status = r.status
        if status == "running" and extracted_result is not None:
            status = "success"

        # Derive action label for mass stream vs single
        raw_mode = None
        if isinstance(payload, dict):
            raw_mode = payload.get("mode")
            if not raw_mode and isinstance(extracted_result, dict):
                raw_mode = extracted_result.get("mode")
        action_label = r.action_type
        if isinstance(raw_mode, str):
            if raw_mode.lower() == "follow":
                action_label = "mass_follow"
            elif raw_mode.lower() == "unfollow":
                action_label = "mass_unfollow"

        results.append({
            "id": r.id,
            "account_id": r.account_id,
            "profile_id": r.profile_id,
            "action": action_label,
            "status": status,
            "error_message": r.error_message,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "result": extracted_result,
            "payload": payload,
            "mode": raw_mode,
        })
    return results


@router.get("/debug")
def list_logs_debug(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=200),
):
    """Return raw logs with payload for debugging UI issues."""
    rows = (
        db.query(ActionLog)
        .order_by(ActionLog.created_at.desc())
        .limit(limit)
        .all()
    )
    out = []
    for r in rows:
        out.append(
            {
                "id": r.id,
                "account_id": r.account_id,
                "profile_id": r.profile_id,
                "action_type": r.action_type,
                "status": r.status,
                "error_message": r.error_message,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "payload": getattr(r, "payload", None),
            }
        )
    return out


@router.post("/finalize-stuck")
def finalize_stuck(
    db: Session = Depends(get_db),
    older_than_seconds: int = Query(120, ge=10, le=3600),
):
    """Finalize logs that are still 'running' beyond a threshold.
    - If payload.result exists with acted>0, mark success
    - else mark error with reason timed_out
    """
    cutoff = datetime.now(timezone.utc).timestamp() - older_than_seconds
    stuck = db.query(ActionLog).filter(ActionLog.status == "running").all()
    updated = 0
    for r in stuck:
        ts = r.started_at.timestamp() if r.started_at else 0
        if ts <= cutoff:
            payload = getattr(r, "payload", None) or {}
            result = None
            if isinstance(payload, dict):
                result = payload.get("result")
            if isinstance(result, dict) and (result.get("acted") or 0) > 0:
                r.status = "success"
            else:
                r.status = "error"
                r.error_message = "timed_out"
            r.finished_at = datetime.now(timezone.utc)
            db.add(r)
            updated += 1
    db.commit()
    return {"finalized": updated}
