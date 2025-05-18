from fastapi import  APIRouter, HTTPException
from models.user_model import  UserCreate, UserResponse
from services.user_services import create_user

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def create_user_endpoint(user: UserCreate):
    """
    Endpoint to create a new user.
    """
    try:
        return await create_user(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")