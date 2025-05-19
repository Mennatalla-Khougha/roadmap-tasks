from fastapi import  APIRouter, HTTPException
from pydantic import EmailStr

from models.user_model import  UserCreate, UserResponse
from services.user_services import create_user, get_user

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def create_user_endpoint(user: UserCreate):
    """
    Endpoint to create a new user.
    """
    try:
        return create_user(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")


@router.get("/users/{email}", response_model=UserResponse)
def get_user_endpoint(email: EmailStr):
    """
    Endpoint to get a user by email.
    """
    try:
        user = get_user(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")