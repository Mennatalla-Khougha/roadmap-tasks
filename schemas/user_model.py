from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from schemas.roadmap_model import Roadmap


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class UserCreate(BaseModel):
    id: Optional[str] = None
    username: str
    email: EmailStr
    password: str
    created_at: Optional[datetime] = None
    is_active: bool = False
    user_roadmaps_ids: list[str] = Field(default_factory=list)
    user_roadmaps: list[Roadmap] = Field(default_factory=list)
    role: UserRole = UserRole.USER

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    is_active: bool = False
    user_roadmaps_ids: list[str] = Field(default_factory=list)
    user_roadmaps: list[Roadmap] =  Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    model_config = ConfigDict(from_attributes=True)


class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[str] = None
    role: Optional[UserRole] = None