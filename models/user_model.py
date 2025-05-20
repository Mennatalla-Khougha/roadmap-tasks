from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    id: str = None
    username: str
    email: EmailStr
    password: str
    created_at: datetime = None
    is_active: bool = False


class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    is_active: bool = False

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    class Config:
        from_attributes = True

