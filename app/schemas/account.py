from typing import Optional
from pydantic import BaseModel, Field


class AccountBase(BaseModel):
    username: str = Field(alias="handle")
    profile_id: Optional[int] = None

    class Config:
        from_attributes = True   # replaces orm_mode in v2
        populate_by_name = True


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    username: Optional[str] = Field(None, alias="handle")
    profile_id: Optional[int] = None

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
