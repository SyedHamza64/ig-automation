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
    
    # Profile information (merged from Profile model)
    bulk_profile_name = Column(String, unique=True, nullable=True, index=True)
    health = Column(String, default="unknown")  # unknown | ok | warn | error
    instagram_username = Column(String, nullable=True)  # Extracted from Instagram profile
    last_opened_at = Column(TIMESTAMP(timezone=True))
    last_ws_puppeteer = Column(String, nullable=True)  # e.g. ws://127.0.0.1:55xxx/devtools/browser/....
    last_ws_selenium = Column(String, nullable=True)  # e.g. 127.0.0.1:55xxx
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
