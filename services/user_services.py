import asyncio
from datetime import datetime, timedelta

from google.cloud import firestore

from core.security import hash_password, verify_password, create_access_token
from schemas.user_model import UserCreate, UserResponse, UserLogin
from services.roadmap_services import get_roadmap, write_roadmap
from core.database import get_db

db = get_db()


def create_user(user: UserCreate) -> UserResponse:
    """
    Create a new user in the database.
    This function checks if the user already exists by email,
    hashes the password, and saves the user data in Firestore.
    Args:
        user (UserCreate): The user data to be created.
    Raises:
        ValueError: If the email already exists or if there is an error during user creation.
        FileNotFoundError: If the user does not exist when trying to retrieve it.
    Returns:
        UserResponse: The created user data.
    """
    try:
        user_id = str(user.email)
        user_ref = db.collection("users").document(user_id).get()
        if user_ref.exists:
            raise ValueError("Email already exists")
        hashed_password = hash_password(user.password)
        now = datetime.now()
        user_data = {
            "id": str(user.email),
            "username": user.username,
            "email": user.email,
            "password": hashed_password,
            "created_at": now,
            "updated_at": now,
            "is_active": user.is_active,
            "user_roadmaps_ids": [],
        }
        db.collection("users").document(user_id).set(user_data)
        return UserResponse(
            id=user_id,
            username=user.username,
            email=user.email,
            is_active=user.is_active
        )
    except ValueError as e:
        raise ValueError(f"User creation failed: {e}")
    except Exception as e:
        raise ValueError(f"Error creating user: {e}")


def get_user(email:str) -> UserResponse:
    """
    Get a user by email from the database.
    This function retrieves a user document from Firestore by email.
    Args:
        email (str): The email of the user to retrieve.
    Raises:
        FileNotFoundError: If no user exists with the provided email.
        ValueError: If there is an error retrieving the user.
    Returns:
        UserResponse: The user data retrieved from the database.
    """
    try:
        if not email:
            raise ValueError("Email is required")
        user_id = str(email)
        user_ref = db.collection("users").document(user_id).get()
        if not user_ref.exists:
            raise FileNotFoundError("No user exist with that Email")
        user_ref = user_ref.to_dict()
        return UserResponse (
            id=user_ref.get("id", user_id),
            username=user_ref.get("username"),
            email=user_ref.get("email"),
            is_active=user_ref.get("is_active", False),
            user_roadmaps_ids=user_ref.get("user_roadmaps_ids", []),
            created_at=user_ref.get("created_at", datetime.now()),
            updated_at=user_ref.get("updated_at", datetime.now())
        )
    except FileNotFoundError as e:
        raise FileNotFoundError(f"User not found: {e}")
    except Exception as e:
        raise ValueError(f"Error retrieving user: {e}")


def user_login(user: UserLogin) -> str:
    """
    Authenticate a user by email and password.
    This function checks if the user exists in the database,
    verifies the password, and returns an access token.
    Args:
        user (UserLogin): The user login data containing email and password.
    Raises:
        ValueError: If the email or password is missing, or if the authentication fails.
        FileNotFoundError: If the user does not exist in the database.
    Returns:
        str: An access token for the authenticated user.
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
        token = create_access_token(
            subject=user_data["email"],
            user_id=user_data["id"],
        )
        return token
    except Exception as e:
        raise ValueError(f"Error logging in: {e}")


async def add_roadmap_to_user(email: str, roadmap_id: str) -> UserResponse:
    """
    Add a roadmap to a user's active roadmaps.
    """
    try:
        user = get_user(email)
        if not user:
            raise FileNotFoundError("User not found")
        if not roadmap_id:
            raise ValueError("Roadmap ID is required")
        if roadmap_id in user.user_roadmaps_ids:
            raise ValueError("Roadmap already exists in user's roadmaps")
        roadmap = await get_roadmap(roadmap_id)
        user_ref = db.collection("users").document(email)
        parent = user_ref.collection("users_roadmaps")
        batch = db.batch()
        await write_roadmap(parent, roadmap, batch, roadmap_id)
        user_ref.update({
            "user_roadmaps_ids": firestore.ArrayUnion([roadmap_id]),
            "updated_at": datetime.now(),
        })
        await asyncio.to_thread(batch.commit)
        return get_user(email)
    except ValueError as e:
        raise ValueError(f"Error adding roadmap to user: {e}")
    except FileNotFoundError as e:
        raise FileNotFoundError(f"User not found: {e}")
    except Exception as e:
        raise Exception(f"Unexpected Error: {e}")