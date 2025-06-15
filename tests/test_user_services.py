from datetime import datetime

import pytest
from unittest.mock import MagicMock, ANY

from core.exceptions import UserNotFoundError
from schemas.user_model import UserCreate, UserLogin
from services.user_services import create_user, get_user, user_login

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