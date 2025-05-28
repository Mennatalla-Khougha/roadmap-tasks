from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from schemas.roadmap_model import Roadmap


class UserCreate(BaseModel):
    id: Optional[str] = None
    username: str
    email: EmailStr
    password: str
    created_at: Optional[datetime] = None
    is_active: bool = False
    user_roadmaps_ids: list[str] = Field(default_factory=list)
    user_roadmaps: list[Roadmap] = Field(default_factory=list)


class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    is_active: bool = False
    user_roadmaps_ids: list[str] = Field(default_factory=list)
    user_roadmaps: list[Roadmap] =  Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    class Config:
        from_attributes = True

