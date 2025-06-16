from datetime import datetime

import pytest
from unittest.mock import MagicMock, ANY, AsyncMock

from core.exceptions import UserNotFoundError, RoadmapNotFoundError
from schemas.roadmap_model import Roadmap, Topic, Task
from schemas.user_model import UserCreate, UserLogin, UserResponse
from services.user_services import create_user, get_user, user_login, get_user_roadmap, add_roadmap_to_user, \
    get_user_roadmaps

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_db():
    with patch("services.user_services.db") as mock:
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
    with patch("services.user_services.get_user") as mock:
        yield mock

@pytest.fixture
def mock_get_roadmap_service():
    with patch("services.user_services.get_roadmap", new_callable=AsyncMock) as mock:
        yield mock

@pytest.fixture
def mock_write_roadmap_util():
    with patch("services.user_services.write_roadmap", new_callable=AsyncMock) as mock:
        yield mock

@pytest.fixture
def mock_fetch_roadmap_from_firestore_util():
    with patch("services.user_services.fetch_roadmap_from_firestore", new_callable=AsyncMock) as mock:
        yield mock

@pytest.fixture
def sample_user_response():
    return UserResponse(
        id="test@example.com",
        username="testuser",
        email="test@example.com",
        is_active=True,
        user_roadmaps_ids=[],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

@pytest.fixture
def sample_roadmap():
    return Roadmap(
        id="roadmap1",
        title="Test Roadmap",
        description="A test roadmap",
        total_duration_weeks=4,
        topics=[
            Topic(
                id="topic1",
                title="Test Topic",
                description="A test topic",
                duration_days=7,
                resources=["Resource1"],
                tasks=[Task(id="task1", task="Test Task", description="A test task", is_completed=False)]
            )
        ]
    )


def test_create_user_with_valid_data(mock_db, mock_hash_password):
    # Arrange
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="securepassword123",
        is_active=True
    )
    mock_db.collection.return_value.document.return_value.get.return_value.exists = False
    mock_hash_password.return_value = "hashedpassword123"

    # Act
    result = create_user(user_data)

    # Assert
    mock_db.collection.assert_called_with("users")
    mock_db.collection.return_value.document.assert_called_with("test@example.com")
    mock_db.collection.return_value.document.return_value.set.assert_called_once()
    assert result.email == user_data.email
    assert result.username == user_data.username
    assert result.is_active == user_data.is_active


def test_create_user_raises_error_for_existing_email(mock_db):
    # Arrange
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="securepassword123",
        is_active=True
    )
    mock_db.collection.return_value.document.return_value.get.return_value.exists = True

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        create_user(user_data)
    assert str(exc_info.value) == "User creation failed: Email already exists"


def test_create_user_raises_error_on_database_failure(mock_db):
    # Arrange
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="securepassword123",
        is_active=True
    )
    mock_db.collection.side_effect = Exception("Database connection failed")

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        create_user(user_data)
    assert "Error creating user: Database connection failed" in str(exc_info.value)


def test_get_user_with_valid_email(mock_db):
    # Arrange
    email = "test@example.com"
    user_data = {
        "id": email,
        "username": "testuser",
        "email": email,
        "is_active": True,
        "user_roadmaps_ids": ["roadmap1", "roadmap2"],
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    mock_db.collection.return_value.document.return_value.get.return_value.exists = True
    mock_db.collection.return_value.document.return_value.get.return_value.to_dict.return_value = user_data

    # Act
    result = get_user(email)

    # Assert
    mock_db.collection.assert_called_with("users")
    mock_db.collection.return_value.document.assert_called_with(email)
    assert result.email == email
    assert result.username == user_data["username"]
    assert result.is_active == user_data["is_active"]
    assert result.user_roadmaps_ids == user_data["user_roadmaps_ids"]


def test_user_login_with_empty_password(mock_db):
    # Arrange
    user_login_data = UserLogin(email="test@example.com", password="")

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        user_login(user_login_data)
    assert "Email and password are required" in str(exc_info.value)


def test_get_user_raises_error_for_nonexistent_user(mock_db):
    # Arrange
    email = "nonexistent@example.com"
    mock_db.collection.return_value.document.return_value.get.return_value.exists = False

    # Act & Assert
    with pytest.raises(UserNotFoundError) as exc_info:  # Changed from FileNotFoundError
        get_user(email)
    assert "No user exist with that Email" in str(exc_info.value)


def test_get_user_raises_error_on_database_failure(mock_db):
    # Arrange
    email = "test@example.com"
    mock_db.collection.side_effect = Exception("Database connection failed")

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        get_user(email)
    assert "Unexpected Error: Database connection failed" in str(exc_info.value)


def test_user_login_with_valid_credentials(mock_db, mock_verify_password, mock_create_access_token):
    # Arrange
    user_login_data = UserLogin(email="test@example.com", password="securepassword123")
    user_data = {
        "id": "test@example.com",
        "email": "test@example.com",
        "password": "hashedpassword"
    }
    mock_db.collection.return_value.document.return_value.get.return_value.exists = True
    mock_db.collection.return_value.document.return_value.get.return_value.to_dict.return_value = user_data
    mock_verify_password.return_value = True
    mock_create_access_token.return_value = "valid_access_token"

    # Act
    result = user_login(user_login_data)

    # Assert
    mock_db.collection.assert_called_with("users")
    mock_db.collection.return_value.document.assert_called_with("test@example.com")
    mock_verify_password.assert_called_with(user_login_data.password, user_data["password"])
    mock_create_access_token.assert_called_with(subject=user_data["email"], user_id=user_data["id"])
    assert result == "valid_access_token"


def test_user_login_with_empty_credentials(mock_db, monkeypatch):
    # Create login data with empty credentials
    class MockUserLogin:
        def __init__(self, email, password):
            self.email = email
            self.password = password

    monkeypatch.setattr('services.user_services.UserLogin', MockUserLogin)
    login_data = MockUserLogin(email="", password="")

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        user_login(login_data)
    assert "Email and password are required" in str(exc_info.value)


def test_user_login_with_nonexistent_email(mock_db):
    # Arrange
    user_login_data = UserLogin(email="nonexistent@example.com", password="password123")
    mock_db.collection.return_value.document.return_value.get.return_value.exists = False

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        user_login(user_login_data)
    assert "Invalid password or email" in str(exc_info.value)


def test_user_login_with_incorrect_password(mock_db, mock_verify_password):
    # Arrange
    user_login_data = UserLogin(email="test@example.com", password="wrongpassword")
    user_data = {
        "id": "test@example.com",
        "email": "test@example.com",
        "password": "hashedpassword"
    }
    mock_db.collection.return_value.document.return_value.get.return_value.exists = True
    mock_db.collection.return_value.document.return_value.get.return_value.to_dict.return_value = user_data
    mock_verify_password.return_value = False

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        user_login(user_login_data)
    assert "Invalid password or email" in str(exc_info.value)


@pytest.mark.asyncio
async def test_add_roadmap_to_user_success(mock_db, mock_get_user_service, mock_get_roadmap_service,
                                           mock_write_roadmap_util, sample_user_response, sample_roadmap):
    # Arrange
    email = "test@example.com"
    roadmap_id = "roadmap1"

    mock_get_user_service.side_effect = [
        sample_user_response,  # First call in add_roadmap_to_user
        UserResponse(**{**sample_user_response.model_dump(), "user_roadmaps_ids": [roadmap_id]})
        # Second call (final get_user)
    ]
    mock_get_roadmap_service.return_value = sample_roadmap

    mock_batch = AsyncMock()
    mock_db.batch.return_value = mock_batch
    mock_db.collection.return_value.document.return_value = MagicMock()  # for user_ref

    # Act
    result = await add_roadmap_to_user(email, roadmap_id)

    # Assert
    assert mock_get_user_service.call_count == 2
    mock_get_user_service.assert_any_call(email)
    mock_get_roadmap_service.assert_called_once_with(roadmap_id)
    mock_write_roadmap_util.assert_called_once_with(ANY, sample_roadmap, mock_batch, roadmap_id)
    mock_db.collection.assert_called_with("users")
    mock_db.collection.return_value.document.assert_called_with(email)
    mock_db.collection.return_value.document.return_value.update.assert_called_once_with({
        "user_roadmaps_ids": ANY,  # firestore.ArrayUnion is tricky to mock precisely without deeper firestore mocks
        "updated_at": ANY,
    })
    mock_batch.commit.assert_called_once()
    assert roadmap_id in result.user_roadmaps_ids


@pytest.mark.asyncio
async def test_add_roadmap_to_user_user_not_found(mock_get_user_service):
    # Arrange
    email = "nonexistent@example.com"
    roadmap_id = "roadmap1"
    mock_get_user_service.side_effect = UserNotFoundError("User not found")

    # Act & Assert
    with pytest.raises(UserNotFoundError) as exc_info:
        await add_roadmap_to_user(email, roadmap_id)
    assert "User not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_add_roadmap_to_user_missing_roadmap_id(mock_get_user_service, sample_user_response):
    # Arrange
    email = "test@example.com"
    roadmap_id = ""
    mock_get_user_service.return_value = sample_user_response

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        await add_roadmap_to_user(email, roadmap_id)
    assert "Error adding roadmap to user: Roadmap ID is required" in str(exc_info.value)


@pytest.mark.asyncio
async def test_add_roadmap_to_user_already_exists(mock_get_user_service, sample_user_response):
    # Arrange
    email = "test@example.com"
    roadmap_id = "roadmap1"
    sample_user_response.user_roadmaps_ids = [roadmap_id]
    mock_get_user_service.return_value = sample_user_response

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        await add_roadmap_to_user(email, roadmap_id)
    assert "Error adding roadmap to user: Roadmap already exists in user's roadmaps" in str(exc_info.value)


@pytest.mark.asyncio
async def test_add_roadmap_to_user_get_roadmap_fails(mock_get_user_service, mock_get_roadmap_service,
                                                     sample_user_response):
    # Arrange
    email = "test@example.com"
    roadmap_id = "roadmap1"
    mock_get_user_service.return_value = sample_user_response
    mock_get_roadmap_service.side_effect = Exception("Failed to fetch roadmap")

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        await add_roadmap_to_user(email, roadmap_id)
    assert "Unexpected Error: Failed to fetch roadmap" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_user_roadmaps_success(mock_get_user_service, sample_user_response, sample_roadmap):
    # Arrange
    email = "test@example.com"
    roadmap_id = "roadmap1"
    sample_user_response.user_roadmaps_ids = [roadmap_id]
    mock_get_user_service.return_value = sample_user_response

    with patch("services.user_services.get_user_roadmap", new_callable=AsyncMock) as mock_get_user_roadmap_specific:
        mock_get_user_roadmap_specific.return_value = sample_roadmap

        # Act
        result = await get_user_roadmaps(email)

        # Assert
        mock_get_user_service.assert_called_once_with(email)
        mock_get_user_roadmap_specific.assert_called_once_with(roadmap_id, email)
        assert len(result) == 1
        assert result[0] == sample_roadmap


@pytest.mark.asyncio
async def test_get_user_roadmaps_user_not_found(mock_get_user_service):
    # Arrange
    email = "nonexistent@example.com"
    mock_get_user_service.side_effect = UserNotFoundError("User not found")

    # Act & Assert
    with pytest.raises(UserNotFoundError) as exc_info:
        await get_user_roadmaps(email)
    assert "Error retrieving user's roadmaps: User not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_user_roadmaps_no_roadmaps(mock_get_user_service, sample_user_response):
    # Arrange
    email = "test@example.com"
    sample_user_response.user_roadmaps_ids = []
    mock_get_user_service.return_value = sample_user_response

    # Act & Assert
    with pytest.raises(RoadmapNotFoundError) as exc_info:
        await get_user_roadmaps(email)
    assert "No roadmaps found for user: User has no roadmaps" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_user_roadmaps_get_specific_roadmap_fails(mock_get_user_service, sample_user_response):
    # Arrange
    email = "test@example.com"
    roadmap_id = "roadmap1"
    sample_user_response.user_roadmaps_ids = [roadmap_id]
    mock_get_user_service.return_value = sample_user_response

    with patch("services.user_services.get_user_roadmap", new_callable=AsyncMock) as mock_get_user_roadmap_specific:
        mock_get_user_roadmap_specific.side_effect = Exception("DB error")
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await get_user_roadmaps(email)
        assert "Unexpected Error: DB error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_user_roadmap_success(mock_db, mock_get_user_service, mock_fetch_roadmap_from_firestore_util,
                                        sample_user_response, sample_roadmap):
    # Arrange
    email = "test@example.com"
    roadmap_id = "roadmap1"
    sample_user_response.user_roadmaps_ids = [roadmap_id]
    mock_get_user_service.return_value = sample_user_response
    mock_fetch_roadmap_from_firestore_util.return_value = sample_roadmap
    mock_db.collection.return_value.document.return_value.collection.return_value = "mock_doc_ref"

    # Act
    result = await get_user_roadmap(roadmap_id, email)

    # Assert
    mock_get_user_service.assert_called_once_with(email)
    mock_db.collection.assert_called_with("users")
    mock_db.collection.return_value.document.assert_called_with(email)
    mock_db.collection.return_value.document.return_value.collection.assert_called_with("users_roadmaps")
    mock_fetch_roadmap_from_firestore_util.assert_called_once_with("mock_doc_ref", roadmap_id)
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
    assert "Error retrieving user's roadmaps: User not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_user_roadmap_id_missing(mock_get_user_service, sample_user_response):
    # Arrange
    email = "test@example.com"
    roadmap_id = ""  # Empty roadmap_id
    mock_get_user_service.return_value = sample_user_response

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        await get_user_roadmap(roadmap_id, email)
    # This assertion depends on the exact error message from your service
    assert "Roadmap ID is required" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_user_roadmap_not_in_users_list(mock_get_user_service, sample_user_response):
    # Arrange
    email = "test@example.com"
    roadmap_id = "roadmap1"
    sample_user_response.user_roadmaps_ids = ["another_roadmap"]  # roadmap_id not in this list
    mock_get_user_service.return_value = sample_user_response

    # Act & Assert
    with pytest.raises(RoadmapNotFoundError) as exc_info:
        await get_user_roadmap(roadmap_id, email)
    assert f"Roadmap {roadmap_id} not found for user {email}: Roadmap not found in user's roadmaps" in str(
        exc_info.value)


@pytest.mark.asyncio
async def test_get_user_roadmap_fetch_fails(mock_db, mock_get_user_service, mock_fetch_roadmap_from_firestore_util,
                                            sample_user_response):
    # Arrange
    email = "test@example.com"
    roadmap_id = "roadmap1"
    sample_user_response.user_roadmaps_ids = [roadmap_id]
    mock_get_user_service.return_value = sample_user_response
    mock_fetch_roadmap_from_firestore_util.side_effect = Exception("Firestore error")
    mock_db.collection.return_value.document.return_value.collection.return_value = "mock_doc_ref"

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        await get_user_roadmap(roadmap_id, email)
    assert "Unexpected Error: Firestore error" in str(exc_info.value)