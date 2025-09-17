from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True)

    # Link to our logical IG account
    account_id = Column(
        Integer,
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # AdsPower's profile identifier (a.k.a. user_id shown in AdsPower UI)
    adspower_profile_id = Column(String, unique=True, nullable=False, index=True)

    # Runtime/health metadata
    health = Column(String, default="unknown")  # unknown | ok | warn | error
    last_opened_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # NEW: connection info returned by AdsPower when we open the profile
    # e.g. ws://127.0.0.1:55xxx/devtools/browser/....
    last_ws_puppeteer = Column(String, nullable=True)
    # e.g. 127.0.0.1:55xxx
    last_ws_selenium = Column(String, nullable=True)

    # ORM relationship
    account = relationship("Account", backref="profiles")
