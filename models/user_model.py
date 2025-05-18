from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    id: str
    username: str
    email: EmailStr
    password: str
    is_active: bool = False


class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    is_active: bool = False

    class Config:
        from_attributes = True




