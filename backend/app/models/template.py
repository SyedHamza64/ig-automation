from sqlalchemy import Column, Integer, String, JSON, TIMESTAMP
from sqlalchemy.sql import func
from app.models.base import Base

class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)  # unique for now
    body = Column(String, nullable=False)                           # message text, can include {{vars}}
    media_refs = Column(JSON, default=[])                           # list of image/video URLs/keys
    locale = Column(String, default="en")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
