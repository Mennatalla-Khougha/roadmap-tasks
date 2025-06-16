import asyncio
from datetime import datetime, timedelta

from google.cloud import firestore

from core.exceptions import RoadmapNotFoundError, UserNotFoundError
from core.security import hash_password, verify_password, create_access_token
from schemas.roadmap_model import Roadmap
from schemas.user_model import UserCreate, UserResponse, UserLogin
from services.roadmap_services import get_roadmap
from core.database import get_db
from utilis.roadmap_helper import write_roadmap, fetch_roadmap_from_firestore

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
        UserNotFoundError: If no user exists with the provided email.
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
            raise UserNotFoundError("No user exist with that Email")
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
    except UserNotFoundError as e:
        raise UserNotFoundError(f"User not found: {e}")
    except ValueError as e:
        raise ValueError(f"Error retrieving user: {e}")
    except Exception as e:
        raise ValueError(f"Unexpected Error: {e}")


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
    except ValueError as e:
        raise ValueError(f"Error logging in with email or password: {e}")
    except Exception as e:
        raise ValueError(f"Unexpected Error during login: {e}")


async def add_roadmap_to_user(email: str, roadmap_id: str) -> UserResponse:
    """
    Add a roadmap to a user's active roadmaps.
    Args:
        email (str): The email of the user to whom the roadmap will be added.
        roadmap_id (str): The ID of the roadmap to be added.
    Raises:
        ValueError: If the roadmap ID is missing or if the roadmap already exists in the user's roadmaps.
        FileNotFoundError: If the user does not exist.
        Exception: For any unexpected errors during the process.
    Returns:
        UserResponse: The updated user data after adding the roadmap.
    """
    try:
        user = get_user(email)
        if not user:
            raise UserNotFoundError("User not found")
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
    except UserNotFoundError as e:
        raise UserNotFoundError(f"User not found: {e}")
    except Exception as e:
        raise Exception(f"Unexpected Error: {e}")


async def get_user_roadmaps(email: str) -> list[Roadmap]:
    """
    Get all roadmaps for a user by email.
    Args:
        email (str): The email of the user whose roadmaps are to be retrieved.
    Raises:
        FileNotFoundError: If the user does not exist or if no roadmaps are found for the user.
        Exception: For any unexpected errors during the process.
    Returns:
        list[Roadmap]: A list of roadmaps associated with the user.
    """
    try:
        user = get_user(email)
        if not user:
            raise UserNotFoundError("User not found")
        if not user.user_roadmaps_ids:
            raise RoadmapNotFoundError("User has no roadmaps")
        roadmaps = []
        for roadmap_id in user.user_roadmaps_ids:
            roadmap = await get_user_roadmap(roadmap_id, email)
            roadmaps.append(roadmap)
        return roadmaps
    except UserNotFoundError as e:
        raise UserNotFoundError(f"Error retrieving user's roadmaps: {e}")
    except RoadmapNotFoundError as e:
        raise RoadmapNotFoundError(f"No roadmaps found for user: {e}")
    except Exception as e:
        raise Exception(f"Unexpected Error: {e}")


async def get_user_roadmap(roadmap_id: str, email: str) -> Roadmap:
    """
    Get a user's roadmaps by email.
    Args:
        email (str): The email of the user whose roadmaps are to be retrieved.
        roadmap_id (str): The ID of the roadmap to be retrieved.
    Raises:
        FileNotFoundError: If the user does not exist or if the roadmap does not exist.
        Exception: For any unexpected errors during the process.
    Returns:
        UserResponse: The user data with the specified roadmap included.
    """
    try:
        user = get_user(email)
        if not user:
            raise UserNotFoundError("User not found")
        if not roadmap_id:
            raise ValueError("Roadmap ID is required")
        if roadmap_id not in user.user_roadmaps_ids:
            raise RoadmapNotFoundError("Roadmap not found in user's roadmaps")
        doc_ref = db.collection("users").document(email).collection("users_roadmaps")
        roadmap = await fetch_roadmap_from_firestore(doc_ref, roadmap_id)
        return roadmap
    except UserNotFoundError as e:
        raise UserNotFoundError(f"Error retrieving user's roadmaps: {e}")
    except RoadmapNotFoundError as e:
        raise RoadmapNotFoundError(f"Roadmap {roadmap_id} not found for user {email}: {e}")
    except ValueError as e:
        raise ValueError(f"Invalid input: {e}")
    except Exception as e:
        raise Exception(f"Unexpected Error: {e}")


async def update_user_roadmap(roadmap_id: str, updated_fields: dict, email: str) -> str:
    """
    Update a specific roadmap for a user.
    Args:
        roadmap_id (str): The ID of the roadmap to be updated.
        updated_fields (dict): A dictionary containing the fields to be updated in the roadmap.
                               Only 'title', 'total_duration_weeks', and 'description' are allowed.
        email (str): The email of the user whose roadmap is to be updated.
    Raises:
        UserNotFoundError: If the user does not exist.
        RoadmapNotFoundError: If the roadmap does not exist for the user.
        ValueError: If the roadmap ID or email is invalid, or if trying to update disallowed fields.
        Exception: For any unexpected errors during the process.
    Returns:
        Roadmap: The updated roadmap object.
    """
    try:
        user = get_user(email)
        if not user:
            raise UserNotFoundError("User not found")
        if not roadmap_id:
            raise ValueError("Roadmap ID is required")
        if roadmap_id not in user.user_roadmaps_ids:
            raise RoadmapNotFoundError("Roadmap not found in user's roadmaps")
        allowed_update_fields = {"title", "total_duration_weeks", "description"}
        fields_to_update = {
            key: value for key, value in updated_fields.items() if key in allowed_update_fields
        }
        if not fields_to_update:
            raise ValueError("No valid fields provided for update or all fields are disallowed.")
        doc_ref = db.collection("users").document(email).collection("users_roadmaps").document(roadmap_id)
        doc_snapshot = await asyncio.to_thread(doc_ref.get)
        if not doc_snapshot.exists:
            raise RoadmapNotFoundError(f"Roadmap with id {roadmap_id} not found for user {email}")
        fields_to_update["updated_at"] = datetime.now()
        await asyncio.to_thread(doc_ref.update, fields_to_update)

        return "Roadmap updated successfully"

    except UserNotFoundError as e:
        raise UserNotFoundError(f"User not found: {e}")
    except RoadmapNotFoundError as e:
        raise RoadmapNotFoundError(f"Roadmap not found: {e}")
    except ValueError as e:
        raise ValueError(f"Invalid input or operation: {e}")
    except Exception as e:
        raise Exception(f"Unexpected Error while updating user's roadmap: {str(e)}")