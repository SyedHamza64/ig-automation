from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.models.account import Account
from app.schemas.account import AccountCreate, AccountUpdate, AccountOut
from app.api.auth import require_admin  # <-- guard

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
@router.get("/", response_model=List[AccountOut])
def list_accounts(
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="search by handle prefix"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    query = db.query(Account)
    if q:
        query = query.filter(Account.handle.ilike(f"{q}%"))
    return query.order_by(Account.id.desc()).offset(offset).limit(limit).all()

@router.get("/{account_id}", response_model=AccountOut)
def get_account(account_id: int, db: Session = Depends(get_db)):
    acc = db.query(Account).get(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="account not found")
    return acc


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