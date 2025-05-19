from pydantic import EmailStr

from core.security import hash_password
from models.user_model import UserCreate, UserResponse
from core.database import db

def create_user(user: UserCreate) -> UserCreate:
    """
    Create a new user in the database.
    """
    try:
        user_ref = db.collection("users").document(user.id).get()
        if user_ref.exists:
            raise ValueError("Email already exists")
        hashed_password = hash_password(user.password)
        user_data = {
            "id": user.email,
            "username": user.username,
            "email": user.email,
            "password": hashed_password,
            "is_active": user.is_active
        }
        db.collection("users").document(user.id).set(user_data)
        return user
    except Exception as e:
        raise ValueError(f"Error creating user: {e}")


def get_user(email: EmailStr):
    """
    Get a user by email from the database.
    """
    try:
        if not email:
            raise ValueError("Email is required")
        user_ref = db.collection("users").document(email).get()
        if not user_ref.exists:
            raise FileNotFoundError("No user exist with that Email")
        user_data = user_ref.to_dict()
        return user_data
    except FileNotFoundError as e:
        raise FileNotFoundError(f"User not found: {e}")
    except Exception as e:
        raise ValueError(f"Error retrieving user: {e}")