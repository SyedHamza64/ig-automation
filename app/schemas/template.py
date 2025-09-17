from pydantic import BaseModel, Field
from typing import List, Optional

class TemplateBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    body: str = Field(..., min_length=1)
    media_refs: Optional[List[str]] = None
    locale: str = "en"

class TemplateCreate(TemplateBase):
    pass

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    body: Optional[str] = None
    media_refs: Optional[List[str]] = None
    locale: Optional[str] = None

class TemplateOut(TemplateBase):
    id: int
    class Config:
        from_attributes = True
