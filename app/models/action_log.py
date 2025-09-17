from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from .base import Base

class ActionLog(Base):
    __tablename__ = "action_logs"
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id", ondelete="SET NULL"))
    action_type = Column(String(32), nullable=False, index=True)  # follow|unfollow|like|dm
    payload = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    status = Column(String(32), nullable=False, index=True)       # queued|running|success|error|skipped|rate_limited
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))

    account = relationship("Account")
    # profile relationship optional

Index("ix_action_logs_account_created_at", ActionLog.account_id, ActionLog.created_at)
Index("ix_action_logs_actiontype_created_at", ActionLog.action_type, ActionLog.created_at)
