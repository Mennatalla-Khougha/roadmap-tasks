from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: str
    username: str
    email: EmailStr
    password: str
    is_active: bool = False
