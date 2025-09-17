from pydantic import BaseModel, Field
from typing import List, Optional

class TargetBase(BaseModel):
    username: str = Field(..., min_length=2, max_length=100)
    source: Optional[str] = None
    labels: Optional[List[str]] = None

class TargetCreate(TargetBase):
    pass

class TargetOut(TargetBase):
    id: int
    class Config:
        from_attributes = True

class TargetBulkIn(BaseModel):
    items: List[TargetCreate]
