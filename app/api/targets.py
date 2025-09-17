from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Set

from app.db.session import get_db
from app.models.target import Target
from app.schemas.target import TargetCreate, TargetOut, TargetBulkIn
from app.api.auth import require_admin  # <-- guard

router = APIRouter()

# ----- WRITE (protected) -----
@router.post("/", response_model=TargetOut, status_code=201, dependencies=[Depends(require_admin)])
def create_target(payload: TargetCreate, db: Session = Depends(get_db)):
    existing = db.query(Target).filter(Target.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="username already exists")
    t = Target(username=payload.username, source=payload.source, labels=payload.labels or [])
    db.add(t)
    db.commit()
    db.refresh(t)
    return t

@router.post("/bulk", status_code=201, dependencies=[Depends(require_admin)])
def bulk_import(payload: TargetBulkIn, db: Session = Depends(get_db)):
    names: Set[str] = {item.username for item in payload.items}
    if not names:
        return {"inserted": 0, "skipped": 0}

    existing = db.query(Target.username).filter(Target.username.in_(list(names))).all()
    exist_set = {u for (u,) in existing}

    to_insert = [
        Target(username=item.username, source=item.source, labels=item.labels or [])
        for item in payload.items
        if item.username not in exist_set
    ]
    for t in to_insert:
        db.add(t)
    db.commit()

    return {"inserted": len(to_insert), "skipped": len(names) - len(to_insert)}

@router.delete("/{target_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_target(target_id: int, db: Session = Depends(get_db)):
    t = db.query(Target).get(target_id)
    if not t:
        raise HTTPException(status_code=404, detail="target not found")
    db.delete(t)
    db.commit()
    return

# ----- READ (public) -----
@router.get("/", response_model=List[TargetOut])
def list_targets(
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="search by username prefix"),
    source: Optional[str] = Query(None),
    label: Optional[str] = Query(None, description="filter by one label"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    query = db.query(Target)
    if q:
        query = query.filter(Target.username.ilike(f"{q}%"))
    if source:
        query = query.filter(Target.source == source)
    if label:
        query = query.filter(Target.labels.contains([label]))  # labels is JSONB
    return query.order_by(Target.id.desc()).offset(offset).limit(limit).all()

@router.get("/{target_id}", response_model=TargetOut)
def get_target(target_id: int, db: Session = Depends(get_db)):
    t = db.query(Target).get(target_id)
    if not t:
        raise HTTPException(status_code=404, detail="target not found")
    return t
