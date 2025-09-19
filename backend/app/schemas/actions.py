from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ActionType(str, Enum):
    follow = "follow"
    unfollow = "unfollow"
    like = "like"
    like_recent = "like_recent"
    dm = "dm"

class FollowRequest(BaseModel):
    account_id: int
    profile_id: int
    usernames: Optional[List[str]] = Field(default=None, description="Explicit usernames to follow")
    target_id: Optional[int] = Field(default=None, description="(Future) target query id")

class LikeRequest(BaseModel):
    account_id: int
    profile_id: int
    post_urls: Optional[List[str]] = None

class DMRequest(BaseModel):
    account_id: int
    profile_id: int
    usernames: List[str]
    template_id: int
    placeholders: Optional[Dict[str, Any]] = None

class ActionEnqueueResponse(BaseModel):
    log_id: int
    status: str

class ActionLogDTO(BaseModel):
    id: int
    account_id: int
    profile_id: Optional[int]
    action_type: ActionType
    payload: Dict[str, Any]
    status: str
    error_message: Optional[str] = None

    class Config:
        from_attributes = True  # pydantic v2: orm_mode replacement

class ActionRequest(BaseModel):
    account_id: int
    profile_id: int
    usernames: Optional[List[str]] = None
    post_urls: Optional[List[str]] = None
    template_id: Optional[int] = None
    placeholders: Optional[Dict[str, Any]] = None
    count: Optional[int] = 2