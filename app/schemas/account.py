from pydantic import BaseModel, Field
from typing import Optional, Dict

class AccountBase(BaseModel):
    handle: str = Field(..., min_length=2, max_length=50)
    timezone: str = "Asia/Karachi"
    status: str = "new"
    limits_json: Optional[Dict] = None

class AccountCreate(AccountBase):
    pass

class AccountUpdate(BaseModel):
    handle: Optional[str] = None
    timezone: Optional[str] = None
    status: Optional[str] = None
    limits_json: Optional[Dict] = None

class AccountOut(AccountBase):
    id: int
    class Config:
        from_attributes = True
