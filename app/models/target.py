
from sqlalchemy import Column, Integer, String, JSON, TIMESTAMP, UniqueConstraint
from sqlalchemy.sql import func
from app.models.base import Base
from sqlalchemy.dialects.postgresql import JSONB  # add this import

class Target(Base):
    __tablename__ = "targets"

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, index=True)
    source = Column(String, nullable=True)             # hashtag / competitor / engagers / upload
    labels = Column(JSONB, default=list)                # list of tags
    last_touched_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("username", name="uq_target_username"),  # global dedupe
    )
