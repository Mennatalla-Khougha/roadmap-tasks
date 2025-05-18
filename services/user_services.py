from core.security import hash_password
from models.user_model import UserCreate
from core.database import db

def create_user(user: UserCreate):
    """
    Create a new user in the database.
    """
    try:
        user_ref = db.collection("users").where ("email", "==", user.email).get()
        if user_ref:
            raise ValueError("Email already exists")
        hashed_password = hash_password(user.password)
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "password": hashed_password,
            "is_active": user.is_active
        }
        db.collection("users").add(user_data)
        return user
    except Exception as e:
        raise ValueError(f"Error creating user: {e}")