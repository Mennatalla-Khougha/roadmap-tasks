from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from google.cloud import firestore
from core.exceptions import UserNotFoundError, RoadmapNotFoundError
from schemas.roadmap_model import Roadmap
from schemas.user_model import UserCreate, UserLogin, UserResponse
from services.user_services import (
    create_user, get_user, user_login, get_user_roadmap, add_roadmap_to_user,
    get_user_roadmaps, update_user_roadmap
)


@pytest.fixture
def mock_db():
    with patch("services.user_services.db") as mock:
        # Common setup for db mock if needed across tests
        mock_batch = MagicMock(name="firestore_batch")
        mock.batch.return_value = mock_batch
        yield mock


@pytest.fixture
def mock_hash_password():
    with patch("services.user_services.hash_password") as mock:
        yield mock


@pytest.fixture
def mock_verify_password():
    with patch("services.user_services.verify_password") as mock:
        yield mock


@pytest.fixture
def mock_create_access_token():
    with patch("services.user_services.create_access_token") as mock:
        yield mock


@pytest.fixture
def mock_get_user_service():
    # If get_user is synchronous and used by async functions,
    # patching it as a regular MagicMock is fine.
    # If it were async, new_callable=AsyncMock would be appropriate.
    with patch("services.user_services.get_user") as mock:
        yield mock


@pytest.fixture
def mock_get_roadmap_service():
    # Assuming get_roadmap is an async function as per add_roadmap_to_user
    with patch("services.user_services.get_roadmap",
               new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_write_roadmap_util():
    with patch("services.user_services.write_roadmap",
               new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_fetch_roadmap_from_firestore_util():
    with patch("services.user_services.fetch_roadmap_from_firestore",
               new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def sample_user_response():
    now = datetime.now()
    return UserResponse(
        id="test@example.com",
        username="testuser",
        email="test@example.com",
        is_active=True,
        user_roadmaps_ids=[],
        created_at=now,
        updated_at=now
    )


@pytest.fixture
def sample_roadmap():
    return Roadmap(
        id="roadmap1",
        title="Test Roadmap",
        description="A test roadmap",
        total_duration_weeks=4,
        topics=[]
    )


def test_create_user_with_valid_data(mock_db, mock_hash_password):
    # Arrange
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="password123",
        is_active=True
    )
    doc_ref = mock_db.collection.return_value.document.return_value
    doc_ref.get.return_value.exists = False
    mock_hash_password.return_value = "hashedpassword123"

    # Act
    result = create_user(user_data)

    # Assert
    mock_db.collection.assert_called_with("users")
    mock_db.collection.return_value.document.assert_called_with(
        "test@example.com")
    doc_ref.set.assert_called_once()
    # Check the fields that create_user actually returns in UserResponse
    assert result.email == user_data.email
    assert result.username == user_data.username
    assert result.is_active == user_data.is_active
    # As per create_user logic
    assert result.id == user_data.email


def test_create_user_raises_error_for_existing_email(mock_db):
    # Arrange
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="password123",
        is_active=True
    )
    doc_ref = mock_db.collection.return_value.document.return_value
    doc_ref.get.return_value.exists = True

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        create_user(user_data)
    assert str(exc_info.value) == "User creation failed: Email already exists"


def test_create_user_raises_error_on_database_failure(mock_db):
    # Arrange
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="password123",
        is_active=True
    )
    mock_db.collection.side_effect = Exception("Database connection failed")

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        create_user(user_data)
    assert "Error creating user: Database connection failed" in str(
        exc_info.value)


def test_get_user_with_valid_email(mock_db):
    # Arrange
    email = "test@example.com"
    now = datetime.now()
    user_data_dict = {
        "id": email,
        "username": "testuser",
        "email": email,
        "is_active": True,
        "user_roadmaps_ids": ["roadmap1"],
        "created_at": now,
        "updated_at": now,
        "role": "user",
        "password": "hashedpassword"
    }
    mock_user_get_result = MagicMock()
    mock_user_get_result.exists = True
    mock_user_get_result.to_dict.return_value = user_data_dict
    doc_ref = mock_db.collection.return_value.document.return_value
    doc_ref.get.return_value = mock_user_get_result

    # Act
    result = get_user(email)

    # Assert
    mock_db.collection.assert_called_with("users")
    mock_db.collection.return_value.document.assert_called_with(email)
    assert result.email == email
    assert result.username == user_data_dict["username"]
    assert result.is_active == user_data_dict["is_active"]
    assert result.user_roadmaps_ids == user_data_dict["user_roadmaps_ids"]
    assert result.created_at == user_data_dict["created_at"]
    assert result.updated_at == user_data_dict["updated_at"]


def test_user_login_with_empty_password(mock_db):  # Renamed for clarity
    # Arrange
    # Valid email, empty password
    user_login_data = UserLogin(email="test@example.com", password="")

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        user_login(user_login_data)
    assert ("Error logging in with email or password: "
            "Email and password are required") in str(exc_info.value)


def test_get_user_raises_error_for_nonexistent_user(mock_db):
    # Arrange
    email = "nonexistent@example.com"
    doc_ref = mock_db.collection.return_value.document.return_value
    doc_ref.get.return_value.exists = False

    # Act & Assert
    with pytest.raises(UserNotFoundError) as exc_info:
        get_user(email)
    assert "User not found: No user exist with that Email" in str(
        exc_info.value)


def test_get_user_raises_error_on_database_failure(mock_db):
    # Arrange
    email = "test@example.com"
    mock_db.collection.side_effect = Exception("Database connection failed")

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        get_user(email)
    assert "Unexpected Error: Database connection failed" in str(
        exc_info.value)


def test_user_login_with_valid_credentials(mock_db, mock_verify_password,
                                           mock_create_access_token):
    # Arrange
    user_login_data = UserLogin(
        email="test@example.com", password="securepassword123")
    user_data = {
        "email": "test@example.com",
        "password": "hashedpassword",
        "id": "someid",
        "role": "user"
    }
    mock_user_get_result = MagicMock()
    mock_user_get_result.exists = True
    mock_user_get_result.to_dict.return_value = user_data
    doc_ref = mock_db.collection.return_value.document.return_value
    doc_ref.get.return_value = mock_user_get_result
    mock_verify_password.return_value = True
    mock_create_access_token.return_value = "valid_access_token"

    # Act
    result = user_login(user_login_data)

    # Assert
    mock_db.collection.assert_called_with("users")
    mock_db.collection.return_value.document.assert_called_with(
        "test@example.com")
    mock_verify_password.assert_called_with(
        user_login_data.password, user_data["password"])
    mock_create_access_token.assert_called_with(
        subject=user_data["email"],
        user_id=user_data["id"],
        user_role=user_data["role"]
    )
    assert result == "valid_access_token"


def test_user_login_with_empty_credentials(mock_db):
    # Pydantic's EmailStr prevents email="", so we test with a valid email
    # and empty password to hit the service's internal check for empty
    # credentials.
    login_data = UserLogin(email="test@example.com", password="")
    with pytest.raises(ValueError) as exc_info:
        user_login(login_data)
    assert ("Error logging in with email or password: "
            "Email and password are required") in str(exc_info.value)


def test_user_login_with_nonexistent_email(mock_db):
    # Arrange
    user_login_data = UserLogin(
        email="nonexistent@example.com", password="password123")
    doc_ref = mock_db.collection.return_value.document.return_value
    doc_ref.get.return_value.exists = False

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        user_login(user_login_data)
    assert ("Error logging in with email or password: "
            "Invalid password or email") in str(exc_info.value)


def test_user_login_with_incorrect_password(mock_db, mock_verify_password):
    # Arrange
    user_login_data = UserLogin(
        email="test@example.com", password="wrongpassword")
    user_data = {"email": "test@example.com",
                 "password": "hashedpassword", "id": "someid", "role": "user"}
    mock_user_get_result = MagicMock()
    mock_user_get_result.exists = True
    mock_user_get_result.to_dict.return_value = user_data
    doc_ref = mock_db.collection.return_value.document.return_value
    doc_ref.get.return_value = mock_user_get_result
    mock_verify_password.return_value = False

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        user_login(user_login_data)
    assert ("Error logging in with email or password: "
            "Invalid password or email") in str(exc_info.value)


@pytest.mark.asyncio
async def test_add_roadmap_to_user_success(
        mock_db, mock_get_user_service, mock_get_roadmap_service,
        mock_write_roadmap_util, sample_user_response, sample_roadmap):
    # Arrange
    email = "test@example.com"
    roadmap_id = "roadmap1"

    initial_user_response = UserResponse(**sample_user_response.model_dump())
    # Start with no roadmaps
    initial_user_response.user_roadmaps_ids = []

    final_user_response = UserResponse(**sample_user_response.model_dump())
    # End with the new roadmap
    final_user_response.user_roadmaps_ids = [roadmap_id]

    # get_user is called twice: once at the start, once at the end
    mock_get_user_service.side_effect = [
        initial_user_response, final_user_response]
    mock_get_roadmap_service.return_value = sample_roadmap

    mock_batch = mock_db.batch.return_value  # From mock_db fixture

    # Mock for user_ref = db.collection("users").document(email)
    mock_user_doc_ref = MagicMock(name="user_doc_ref_in_add_roadmap")
    mock_user_doc_ref.update = MagicMock(
        name="user_doc_ref_update_method")  # This is sync
    mock_user_doc_ref.collection.return_value = MagicMock(
        name="users_roadmaps_subcollection_ref")

    mock_db.collection.return_value.document.return_value = mock_user_doc_ref

    with patch("services.user_services.asyncio.to_thread",
               new_callable=AsyncMock) as mock_to_thread:
        # Act
        result = await add_roadmap_to_user(roadmap_id=roadmap_id, email=email)

        # Assert
        assert mock_get_user_service.call_count == 2
        mock_get_user_service.assert_any_call(email)  # First call
        mock_get_user_service.assert_any_call(email)  # Second call

        mock_get_roadmap_service.assert_called_once_with(roadmap_id)

        # Check Firestore interactions for user_ref and subcollection
        mock_db.collection.assert_any_call("users")  # For user_ref
        mock_db.collection.return_value.document.assert_any_call(
            email)  # For user_ref

        # Assert write_roadmap call to the subcollection
        mock_user_doc_ref.collection.assert_called_once_with("users_roadmaps")
        mock_write_roadmap_util.assert_called_once_with(
            mock_user_doc_ref.collection.return_value,
            sample_roadmap,
            mock_batch,
            roadmap_id
        )

        # Assert user_ref.update call
        mock_user_doc_ref.update.assert_called_once()

        # Inspect the arguments passed to the update call
        update_args, _ = mock_user_doc_ref.update.call_args
        update_payload = update_args[0]

        # Assert on the payload
        assert "user_roadmaps_ids" in update_payload
        assert "updated_at" in update_payload
        assert isinstance(update_payload["updated_at"], datetime)

        # Check the ArrayUnion part robustly
        array_union_obj = update_payload["user_roadmaps_ids"]
        if isinstance(firestore, MagicMock):
            # In CI/mocked environment, firestore.ArrayUnion is a mock
            firestore.ArrayUnion.assert_called_once_with([roadmap_id])
            assert array_union_obj == firestore.ArrayUnion.return_value
        else:
            # In local/real environment, it's a real class instance
            assert isinstance(array_union_obj, firestore.ArrayUnion)
            # The values are stored in a 'values' attribute
            assert array_union_obj.values == [roadmap_id]

        # Assert batch.commit call was passed to asyncio.to_thread
        mock_to_thread.assert_called_once_with(mock_batch.commit)

        # Check the final returned UserResponse
        assert result == final_user_response
        assert roadmap_id in result.user_roadmaps_ids


@pytest.mark.asyncio
async def test_add_roadmap_to_user_user_not_found(mock_get_user_service):
    # Arrange
    email = "nonexistent@example.com"
    roadmap_id = "roadmap1"
    mock_get_user_service.side_effect = UserNotFoundError("User not found")

    # Act & Assert
    with pytest.raises(UserNotFoundError) as exc_info:
        await add_roadmap_to_user(roadmap_id=roadmap_id, email=email)
    assert "User not found: User not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_add_roadmap_to_user_missing_roadmap_id(
        mock_get_user_service, sample_user_response):
    # Arrange
    email_val = "test@example.com"
    roadmap_id_val = ""  # Empty roadmap_id
    mock_get_user_service.return_value = sample_user_response  # User exists

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        await add_roadmap_to_user(roadmap_id=roadmap_id_val, email=email_val)
    assert "Error adding roadmap to user: Roadmap ID is required" in str(
        exc_info.value)


@pytest.mark.asyncio
async def test_add_roadmap_to_user_already_exists(
        mock_get_user_service, sample_user_response):
    # Arrange
    email_val = "test@example.com"
    roadmap_id_val = "roadmap1"

    user_with_roadmap = UserResponse(**sample_user_response.model_dump())
    # Roadmap already in user's list
    user_with_roadmap.user_roadmaps_ids = [roadmap_id_val]
    mock_get_user_service.return_value = user_with_roadmap

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        await add_roadmap_to_user(roadmap_id=roadmap_id_val, email=email_val)
    assert ("Error adding roadmap to user: "
            "Roadmap already exists in user's roadmaps") in str(
        exc_info.value)


@pytest.mark.asyncio
async def test_add_roadmap_to_user_get_roadmap_fails(
        mock_get_user_service, mock_get_roadmap_service,
        sample_user_response):
    # Arrange
    email = "test@example.com"
    roadmap_id = "roadmap1"
    # User exists and has no roadmaps initially
    mock_get_user_service.return_value = sample_user_response
    mock_get_roadmap_service.side_effect = Exception(
        "Failed to fetch roadmap")

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        await add_roadmap_to_user(roadmap_id=roadmap_id, email=email)
    assert "Unexpected Error: Failed to fetch roadmap" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_user_roadmaps_success(
        mock_get_user_service, sample_user_response, sample_roadmap):
    # Arrange
    email = "test@example.com"
    roadmap_id = "roadmap1"
    user_with_roadmaps = UserResponse(**sample_user_response.model_dump())
    user_with_roadmaps.user_roadmaps_ids = [roadmap_id]
    mock_get_user_service.return_value = user_with_roadmaps

    # Mock the internal call to get_user_roadmap
    with patch("services.user_services.get_user_roadmap",
               new_callable=AsyncMock) as mock_get_user_roadmap_specific:
        # It will return this for each ID
        mock_get_user_roadmap_specific.return_value = sample_roadmap

        # Act
        result_roadmaps = await get_user_roadmaps(email)

        # Assert
        mock_get_user_service.assert_called_once_with(email)
        mock_get_user_roadmap_specific.assert_called_once_with(
            roadmap_id, email)
        assert len(result_roadmaps) == 1
        assert result_roadmaps[0] == sample_roadmap


@pytest.mark.asyncio
async def test_get_user_roadmaps_user_not_found(mock_get_user_service):
    # Arrange
    email = "nonexistent@example.com"
    mock_get_user_service.side_effect = UserNotFoundError("User not found")

    # Act & Assert
    with pytest.raises(UserNotFoundError) as exc_info:
        await get_user_roadmaps(email)
    assert "Error retrieving user's roadmaps: User not found" in str(
        exc_info.value)


@pytest.mark.asyncio
async def test_get_user_roadmaps_no_roadmaps(
        mock_get_user_service, sample_user_response):
    # Arrange
    email = "test@example.com"
    user_without_roadmaps = UserResponse(**sample_user_response.model_dump())
    user_without_roadmaps.user_roadmaps_ids = []  # No roadmaps
    mock_get_user_service.return_value = user_without_roadmaps

    # Act & Assert
    with pytest.raises(RoadmapNotFoundError) as exc_info:
        await get_user_roadmaps(email)
    assert "No roadmaps found for user: User has no roadmaps" in str(
        exc_info.value)


@pytest.mark.asyncio
async def test_get_user_roadmaps_get_specific_roadmap_fails(
        mock_get_user_service, sample_user_response):
    # Arrange
    email = "test@example.com"
    roadmap_id = "roadmap1"
    user_with_roadmaps = UserResponse(**sample_user_response.model_dump())
    user_with_roadmaps.user_roadmaps_ids = [roadmap_id]
    mock_get_user_service.return_value = user_with_roadmaps

    with patch("services.user_services.get_user_roadmap",
               new_callable=AsyncMock) as mock_get_user_roadmap_specific:
        mock_get_user_roadmap_specific.side_effect = Exception(
            "Failed to fetch specific roadmap")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await get_user_roadmaps(email)
        assert "Unexpected Error: Failed to fetch specific roadmap" in str(
            exc_info.value)


@pytest.mark.asyncio
async def test_get_user_roadmap_success(
        mock_db, mock_get_user_service,
        mock_fetch_roadmap_from_firestore_util, sample_user_response,
        sample_roadmap):
    # Arrange
    email = "test@example.com"
    roadmap_id = "roadmap1"
    user_with_roadmap = UserResponse(**sample_user_response.model_dump())
    # User has this roadmap ID
    user_with_roadmap.user_roadmaps_ids = [roadmap_id]
    mock_get_user_service.return_value = user_with_roadmap
    mock_fetch_roadmap_from_firestore_util.return_value = sample_roadmap

    # Mock for doc_ref = db.collection("users")...("users_roadmaps")
    mock_coll_ref = MagicMock(name="users_roadmaps_coll_ref_get_user_roadmap")
    (mock_db.collection.return_value.document.return_value
     .collection.return_value) = mock_coll_ref

    # Act
    result = await get_user_roadmap(roadmap_id, email)

    # Assert
    mock_get_user_service.assert_called_once_with(email)
    # Check the path to users_roadmaps collection
    mock_db.collection.assert_called_with("users")
    mock_db.collection.return_value.document.assert_called_with(email)
    (mock_db.collection.return_value.document.return_value
     .collection.assert_called_with("users_roadmaps"))

    mock_fetch_roadmap_from_firestore_util.assert_called_once_with(
        mock_coll_ref, roadmap_id)
    assert result == sample_roadmap


@pytest.mark.asyncio
async def test_get_user_roadmap_user_not_found(mock_get_user_service):
    # Arrange
    email = "nonexistent@example.com"
    roadmap_id = "roadmap1"
    mock_get_user_service.side_effect = UserNotFoundError("User not found")

    # Act & Assert
    with pytest.raises(UserNotFoundError) as exc_info:
        await get_user_roadmap(roadmap_id, email)
    assert "Error retrieving user's roadmaps: User not found" in str(
        exc_info.value)


@pytest.mark.asyncio
async def test_get_user_roadmap_id_missing(
        mock_get_user_service, sample_user_response):
    # Arrange
    email = "test@example.com"
    roadmap_id = ""  # Empty roadmap_id
    mock_get_user_service.return_value = sample_user_response  # User exists

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        await get_user_roadmap(roadmap_id, email)
    assert "Invalid input: Roadmap ID is required" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_user_roadmap_not_in_users_list(
        mock_get_user_service, sample_user_response):
    # Arrange
    email = "test@example.com"
    roadmap_id = "roadmap1"  # This roadmap is NOT in the user's list
    user_without_this_roadmap = UserResponse(
        **sample_user_response.model_dump())
    # User has other roadmaps
    user_without_this_roadmap.user_roadmaps_ids = ["another_roadmap_id"]
    mock_get_user_service.return_value = user_without_this_roadmap

    # Act & Assert
    with pytest.raises(RoadmapNotFoundError) as exc_info:
        await get_user_roadmap(roadmap_id, email)
    assert (f"Roadmap {roadmap_id} not found for user {email}: "
            f"Roadmap not found in user's roadmaps") in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_user_roadmap_fetch_fails(
        mock_db, mock_get_user_service,
        mock_fetch_roadmap_from_firestore_util, sample_user_response):
    # Arrange
    email = "test@example.com"
    roadmap_id = "roadmap1"
    user_with_roadmap = UserResponse(**sample_user_response.model_dump())
    user_with_roadmap.user_roadmaps_ids = [roadmap_id]
    mock_get_user_service.return_value = user_with_roadmap
    mock_fetch_roadmap_from_firestore_util.side_effect = Exception(
        "Firestore error")

    mock_coll_ref = MagicMock(name="users_roadmaps_coll_ref_fetch_fails")
    (mock_db.collection.return_value.document.return_value
     .collection.return_value) = mock_coll_ref

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        await get_user_roadmap(roadmap_id, email)
    assert "Unexpected Error: Firestore error" in str(exc_info.value)


# No mock_get_user_service needed as it's testing get_user directly
def test_get_user_with_empty_email(mock_db):
    # Arrange
    email = ""

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        get_user(email)
    assert "Error retrieving user: Email is required" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_user_roadmap_success(
        mock_db, mock_get_user_service, sample_user_response):
    # Arrange
    email = "test@example.com"
    roadmap_id = "roadmap1"
    updated_fields = {"title": "New Title", "description": "New Description"}

    user_with_roadmap = UserResponse(**sample_user_response.model_dump())
    user_with_roadmap.user_roadmaps_ids = [roadmap_id]
    mock_get_user_service.return_value = user_with_roadmap

    mock_doc_ref = MagicMock(name="firestore_doc_ref_update_success")
    mock_doc_snapshot = MagicMock(
        name="firestore_doc_snapshot_update_success")
    mock_doc_snapshot.exists = True
    # doc_ref.get() is sync, so its return value is the snapshot
    mock_doc_ref.get = MagicMock(return_value=mock_doc_snapshot)
    # doc_ref.update() is sync
    mock_doc_ref.update = MagicMock(name="firestore_doc_ref_update_method")

    (mock_db.collection.return_value.document.return_value
     .collection.return_value.document.return_value) = mock_doc_ref

    # Simulate asyncio.to_thread for synchronous Firestore calls
    async def mock_async_to_thread_executor(func, *args):
        return func(*args)  # Directly execute the sync function

    with patch("services.user_services.asyncio.to_thread",
               side_effect=mock_async_to_thread_executor
               ) as mock_async_to_thread:
        result = await update_user_roadmap(roadmap_id, updated_fields, email)

    # Assert
    mock_get_user_service.assert_called_once_with(email)

    users_collection_mock = mock_db.collection.return_value
    user_doc_mock = users_collection_mock.document.return_value
    roadmaps_collection_mock = user_doc_mock.collection.return_value
    roadmap_doc_constructor = roadmaps_collection_mock.document

    mock_db.collection.assert_called_with("users")
    users_collection_mock.document.assert_called_with(email)
    user_doc_mock.collection.assert_called_with("users_roadmaps")
    roadmap_doc_constructor.assert_called_with(roadmap_id)

    assert mock_async_to_thread.call_count == 2  # For .get() and .update()

    mock_doc_ref.get.assert_called_once()  # Check sync get call
    mock_doc_ref.update.assert_called_once()  # Check sync update call
    args_update, _ = mock_doc_ref.update.call_args
    update_payload = args_update[0]
    assert update_payload["title"] == "New Title"
    assert update_payload["description"] == "New Description"
    assert "updated_at" in update_payload
    assert isinstance(update_payload["updated_at"], datetime)

    assert result == "Roadmap updated successfully"


@pytest.mark.asyncio
async def test_update_user_roadmap_user_not_found(mock_get_user_service):
    email = "test@example.com"
    roadmap_id = "roadmap1"
    updated_fields = {"title": "New Title"}
    mock_get_user_service.side_effect = UserNotFoundError("User not found")
    with pytest.raises(UserNotFoundError) as exc_info:
        await update_user_roadmap(roadmap_id, updated_fields, email)
    assert "User not found: User not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_user_roadmap_id_missing(
        mock_get_user_service, sample_user_response):
    email = "test@example.com"
    roadmap_id = ""  # Missing roadmap_id
    updated_fields = {"title": "New Title"}
    mock_get_user_service.return_value = sample_user_response
    with pytest.raises(ValueError) as exc_info:
        await update_user_roadmap(roadmap_id, updated_fields, email)
    assert "Invalid input or operation: Roadmap ID is required" in str(
        exc_info.value)


@pytest.mark.asyncio
async def test_update_user_roadmap_not_in_users_list(
        mock_get_user_service, sample_user_response):
    email = "test@example.com"
    roadmap_id = "roadmap_not_owned"
    updated_fields = {"title": "New Title"}
    user_without_roadmap = UserResponse(**sample_user_response.model_dump())
    # User doesn't have roadmap_id
    user_without_roadmap.user_roadmaps_ids = ["some_other_roadmap"]
    mock_get_user_service.return_value = user_without_roadmap
    with pytest.raises(RoadmapNotFoundError) as exc_info:
        await update_user_roadmap(roadmap_id, updated_fields, email)
    assert "Roadmap not found: Roadmap not found in user's roadmaps" in str(
        exc_info.value)


@pytest.mark.asyncio
async def test_update_user_roadmap_doc_not_exists_in_firestore(
        mock_db, mock_get_user_service, sample_user_response):
    email = "test@example.com"
    roadmap_id = "roadmap1"
    updated_fields = {"title": "New Title"}
    user_with_roadmap = UserResponse(**sample_user_response.model_dump())
    # User owns the roadmap ID
    user_with_roadmap.user_roadmaps_ids = [roadmap_id]
    mock_get_user_service.return_value = user_with_roadmap

    mock_doc_ref = MagicMock(name="firestore_doc_ref_not_exists")
    mock_doc_snapshot = MagicMock(name="firestore_doc_snapshot_not_exists")
    mock_doc_snapshot.exists = False  # Document does not exist in Firestore
    mock_doc_ref.get = MagicMock(return_value=mock_doc_snapshot)
    mock_doc_ref.update = MagicMock(
        name="firestore_doc_ref_update_method_not_exists")

    (mock_db.collection.return_value.document.return_value
     .collection.return_value.document.return_value) = mock_doc_ref

    async def mock_async_to_thread_executor(func, *args):
        return func(*args)

    with patch("services.user_services.asyncio.to_thread",
               side_effect=mock_async_to_thread_executor
               ) as mock_async_to_thread:
        with pytest.raises(RoadmapNotFoundError) as exc_info:
            await update_user_roadmap(roadmap_id, updated_fields, email)

    assert (f"Roadmap not found: Roadmap with id {roadmap_id} "
            f"not found for user {email}") in str(exc_info.value)
    mock_async_to_thread.assert_called_once()  # Only for .get()
    mock_doc_ref.get.assert_called_once()
    mock_doc_ref.update.assert_not_called()


@pytest.mark.asyncio
async def test_update_user_roadmap_no_valid_fields(
        mock_get_user_service, sample_user_response):
    email = "test@example.com"
    roadmap_id = "roadmap1"
    user_with_roadmap = UserResponse(**sample_user_response.model_dump())
    # User must have the roadmap
    user_with_roadmap.user_roadmaps_ids = [roadmap_id]
    mock_get_user_service.return_value = user_with_roadmap

    with pytest.raises(ValueError) as exc_info:
        await update_user_roadmap(
            roadmap_id, {"invalid_field": "value", "another_bad": 123}, email)
    assert ("Invalid input or operation: "
            "No valid fields provided for update.") in str(exc_info.value)
