from fastapi import APIRouter
from sqlalchemy import text
from app.db.session import SessionLocal
import asyncio

router = APIRouter()

@router.get("/live")
def live():
    return {"status": "ok"}

@router.get("/db")
def db():
    with SessionLocal() as s:
        s.execute(text("SELECT 1"))
    return {"db": "ok"}
from sqlalchemy import text

@router.get("/sample/account")
def sample_account():
    with SessionLocal() as s:
        row = s.execute(text("SELECT id, handle, status FROM accounts ORDER BY id DESC LIMIT 1")).first()
        return {"id": row.id, "handle": row.handle, "status": row.status}
@router.get("/live")
def live():
    return {"ok": True}

@router.get("/loop-policy")
def loop_policy():
    pol = asyncio.get_event_loop_policy()
    return {"policy": type(pol).__name__}