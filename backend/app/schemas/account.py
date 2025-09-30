from typing import Optional
from pydantic import BaseModel, Field


class AccountBase(BaseModel):
    username: str = Field(alias="handle")
    profile_id: Optional[int] = None

    class Config:
        from_attributes = True   # replaces orm_mode in v2
        populate_by_name = True


class AccountCreate(AccountBase):
    timezone: Optional[str] = "Asia/Karachi"
    status: Optional[str] = "new"
    limits_json: Optional[dict] = {}


class AccountUpdate(BaseModel):
    username: Optional[str] = Field(None, alias="handle")
    bulk_profile_name: Optional[str] = None
    adspower_profile_id: Optional[str] = None
    health: Optional[str] = None
    last_ws_puppeteer: Optional[str] = None
    last_ws_selenium: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class AccountOut(BaseModel):
    id: int
    username: str = Field(alias="handle")
    profile_id: Optional[int] = None

    class Config:
        from_attributes = True
        populate_by_name = True
