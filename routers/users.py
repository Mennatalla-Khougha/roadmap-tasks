from fastapi import APIRouter, HTTPException, Depends

from core.exceptions import UserNotFoundError, RoadmapNotFoundError
from core.security import get_current_user
from schemas.roadmap_model import Roadmap
from schemas.user_model import UserCreate, UserResponse, UserLogin, TokenData
from services.user_services import (create_user,
                                    get_user,
                                    user_login,
                                    add_roadmap_to_user,
                                    get_user_roadmap,
                                    get_user_roadmaps,
                                    update_user_roadmap,
                                    delete_user_roadmap,
                                    delete_all_user_roadmaps)

router = APIRouter()


@router.post("/register", response_model=UserResponse)
def create_user_endpoint(user: UserCreate):
    """
    Endpoint to create a new user.
    This endpoint accepts user details and creates a new user in the database.
    Args:
        user (UserCreate): The user data to be created.
    Raises:
        HTTPException: If the email already exists.
    Returns:
        UserResponse: The created user data.
    """
    try:
        return create_user(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected Error: {str(e)}")


@router.get("/user", response_model=UserResponse)
def get_user_endpoint(
        current_user_token: TokenData = Depends(get_current_user)
):
    """
    Endpoint to get a user by email.
    This endpoint retrieves user details based on the provided email.
    Args:
        current_user_token (TokenData): The current user's token data.
    Raises:
        HTTPException: If no user exists with the provided email
                        or if there is an error retrieving the user.
    Returns:
        UserResponse: The user data retrieved from the database.
    """
    try:
        user = get_user(current_user_token.email)
        return user
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected Error: {str(e)}")


@router.post("/login", response_model=str)
def login_user_endpoint(user: UserLogin):
    """
    Endpoint to log in a user.
    This endpoint accepts user credentials and returns a token.
    Args:
        user (UserLogin): The user credentials for login.
    Raises:
        HTTPException: If the login fails due to invalid credentials or
                        if there is an error during login.
    Returns:
        str: A token if the login is successful.
    """
    try:
        user = user_login(user)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected Error: {str(e)}")


@router.post("/roadmaps", response_model=UserResponse)
async def add_roadmaps_to_user_endpoint(
        roadmap_id: str,
        current_user_token: TokenData = Depends(get_current_user)
):
    """
    Endpoint to add a roadmap to a user.
    This endpoint adds a specified roadmap to the user's list of roadmaps.
    Args:
        roadmap_id (str): The ID of the roadmap to be added.
        current_user_token (TokenData): The current user's token data.
    Raises:
        HTTPException: If the user does not exist,
                        or if there is an error adding the roadmap.
    Returns:
        UserResponse: The updated user data after adding the roadmap.
    """
    try:
        email = current_user_token.email
        return await add_roadmap_to_user(roadmap_id, email)
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected Error: {str(e)}")


@router.get("/roadmaps", response_model=list[Roadmap])
async def get_user_roadmaps_endpoint(
        current_user_token: TokenData = Depends(get_current_user)
):
    """
    Endpoint to get all roadmaps of a user.
    This endpoint retrieves the list of roadmap IDs associated with the user.
    Args:
        current_user_token (TokenData): The current user's token data.
    Raises:
        HTTPException: If no user exists with the provided email
                        or if there is an error retrieving the roadmaps.
    Returns:
        list[str]: A list of roadmap IDs associated with the user.
    """
    try:
        email = current_user_token.email
        roadmaps = await get_user_roadmaps(email)
        return roadmaps
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RoadmapNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected Error: {str(e)}")


@router.get("/roadmap/{roadmap_id}", response_model=Roadmap)
async def get_user_roadmap_endpoint(roadmap_id: str,
                                    current_user_token: TokenData = Depends(
                                        get_current_user)
                                    ):
    """
    Endpoint to get all roadmaps of a user.
    This endpoint retrieves the list of roadmap IDs associated with the user.
    Args:
        roadmap_id (str): The ID of the roadmap to retrieve.
        current_user_token (TokenData): The current user's token data.
    Raises:
        HTTPException: If no user exists with the provided email or
                        if there is an error retrieving the roadmaps.
    Returns:
        list[str]: A list of roadmap IDs associated with the user.
    """
    try:
        email = current_user_token.email
        return await get_user_roadmap(roadmap_id, email)
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RoadmapNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected Error: {str(e)}")


@router.patch("/roadmap/{roadmap_id}", response_model=str)
async def update_user_roadmap_endpoint(
        roadmap_id: str,
        updated_fields: dict,
        current_user_token: TokenData = Depends(get_current_user)
):
    """
    Endpoint to update a user's roadmap.
    This endpoint allows updating specific fields of a user's roadmap.
    Args:
        roadmap_id (str): The ID of the roadmap to be updated.
        updated_fields (dict): A dictionary containing the fields to
                                be updated. Only 'title',
                                'total_duration_weeks', and
                                 'description' are allowed.
        current_user_token (TokenData): The current user's token data.
    Raises:
        HTTPException: If the user or roadmap is not found,
                        if the provided data is invalid.
    Returns:
        str: A success message indicating the roadmap has been updated.
    """
    try:
        email = current_user_token.email
        return await update_user_roadmap(roadmap_id, updated_fields, email)
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RoadmapNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected Error: {str(e)}")


@router.delete("/roadmap/{roadmap_id}", response_model=dict)
async def delete_user_roadmap_endpoint(
        roadmap_id: str,
        current_user_token: TokenData = Depends(get_current_user)
):
    """
    Endpoint to delete a user's roadmap.
    This endpoint allows deleting a specific roadmap associated with the user.
    Args:
        roadmap_id (str): The ID of the roadmap to be deleted.
        current_user_token (TokenData): The current user's token data.
    Raises:
        HTTPException: If the user or roadmap is not found.
    Returns:
        dict: A success message indicating the roadmap has been deleted.
    """
    try:
        email = current_user_token.email
        return await delete_user_roadmap(roadmap_id, email)
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RoadmapNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected Error: {str(e)}")


@router.delete("/roadmaps", response_model=dict)
async def delete_all_user_roadmaps_endpoint(
        current_user_token: TokenData = Depends(get_current_user)
):
    """
    Endpoint to delete all roadmaps of a user.
    This endpoint allows deleting all roadmaps associated with the user.
    Args:
        current_user_token (TokenData): The current user's token data.
    Raises:
        HTTPException: If the user is not found.
    Returns:
        dict: A success message indicating all roadmaps have been deleted.
    """
    try:
        email = current_user_token.email
        return await delete_all_user_roadmaps(email)
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected Error: {str(e)}")
