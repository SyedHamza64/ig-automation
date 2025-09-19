from sqlalchemy import Column, Integer, String, JSON, TIMESTAMP
from sqlalchemy.sql import func
from app.models.base import Base

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    handle = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, default="new")          # new/ok/warn/blocked
    timezone = Column(String, default="Asia/Karachi")
    limits_json = Column(JSON, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
