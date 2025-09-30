# app/api/logs.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.db.session import get_db
from app.models.action_log import ActionLog
from datetime import datetime, timezone

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

        results.append({
            "id": r.id,
            "account_id": r.account_id,
            "profile_id": r.profile_id,
            "action": r.action_type,
            "status": status,
            "error_message": r.error_message,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "result": extracted_result,
        })
    return results
