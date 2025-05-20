from datetime import datetime
from pydantic import EmailStr
from core.security import hash_password, verify_password, create_access_token
from models.user_model import UserCreate, UserResponse, UserLogin
from core.database import db

def create_user(user: UserCreate) -> UserResponse:
    """
    Create a new user in the database.
    """
    try:
        user_id = str(user.email)
        user_ref = db.collection("users").document(user_id).get()
        if user_ref.exists:
            raise ValueError("Email already exists")
        hashed_password = hash_password(user.password)
        user_data = {
            "id": str(user.email),
            "username": user.username,
            "email": user.email,
            "password": hashed_password,
            "created_at": datetime.now(),
            "is_active": user.is_active
        }
        db.collection("users").document(user_id).set(user_data)
        return UserResponse(
            id=user_id,
            username=user.username,
            email=user.email,
            is_active=user.is_active
        )
    except Exception as e:
        raise ValueError(f"Error creating user: {e}")


def get_user(email: EmailStr) -> UserResponse:
    """
    Get a user by email from the database.
    """
    try:
        if not email:
            raise ValueError("Email is required")
        user_id = str(email)
        user_ref = db.collection("users").document(user_id).get()
        if not user_ref.exists:
            raise FileNotFoundError("No user exist with that Email")
        user_data = user_ref.to_dict()
        return user_data
    except FileNotFoundError as e:
        raise FileNotFoundError(f"User not found: {e}")
    except Exception as e:
        raise ValueError(f"Error retrieving user: {e}")


def user_login(user: UserLogin) -> str:
    """
    Authenticate a user by email and password.
    """
    try:
        if not user.email or not user.password:
            raise ValueError("Email and password are required")
        user_id = str(user.email)
        user_ref = db.collection("users").document(user_id).get()
        if not user_ref.exists:
            raise ValueError("Invalid password or email")
        user_data = user_ref.to_dict()
        if not verify_password(user.password, user_data["password"]):
            raise ValueError("Invalid password or email")
        token = create_access_token({"id": user_data["id"]})
        return token
    except Exception as e:
        raise ValueError(f"Error logging in: {e}")