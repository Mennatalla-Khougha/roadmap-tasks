import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from unittest.mock import patch

# Import app correctly
from main import app
from schemas.user_model import UserCreate, UserResponse, UserLogin

# Create a test client
client = TestClient(app)


@pytest.fixture
def user_data():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword123",
        "is_active": True
    }


@pytest.fixture
def user_response_data():
    return {
        "id": "test@example.com",
        "username": "testuser",
        "email": "test@example.com",
        "created_at": datetime(2023, 1, 1),
        "is_active": True,
        "user_roadmaps_ids": []
    }


class TestUserRoutes:
    @patch("routers.users.create_user")
    def test_create_user_endpoint_success(self, mock_create_user, user_data, user_response_data):
        # Set up mock
        mock_create_user.return_value = UserResponse(**user_response_data)

        # Make request
        response = client.post("/users/register", json=user_data)

        # Assert
        assert response.status_code == 200
        # Verify response data matches expected fields
        response_data = response.json()
        assert response_data["username"] == user_response_data["username"]
        assert response_data["email"] == user_response_data["email"]

        # Verify mock was called with correct data
        called_arg = mock_create_user.call_args.args[0]
        assert isinstance(called_arg, UserCreate)
        assert called_arg.username == user_data["username"]
        assert called_arg.email == user_data["email"]

    @patch("routers.users.create_user")
    def test_create_user_endpoint_value_error(self, mock_create_user, user_data):
        # Set up mock
        mock_create_user.side_effect = ValueError("Email already exists")

        # Make request
        response = client.post("/users/register", json=user_data)

        # Assert
        assert response.status_code == 400
        assert "Email already exists" in response.json()["detail"]

    @patch("routers.users.create_user")
    def test_create_user_endpoint_unexpected_error(self, mock_create_user, user_data):
        # Set up mock
        mock_create_user.side_effect = Exception("Unexpected error")

        # Make request
        response = client.post("/users/register", json=user_data)

        # Assert
        assert response.status_code == 500
        assert "Unexpected Error" in response.json()["detail"]

    @patch("core.security.jwt.decode")
    @patch("routers.users.get_user")
    def test_get_user_endpoint_success(self, mock_get_user, mock_jwt_decode, user_response_data):
        # Setup mocks
        mock_jwt_decode.return_value = {"id": "test@example.com"}
        mock_get_user.return_value = UserResponse(**user_response_data)

        # Make request with authorization header
        response = client.get("/users/user", headers={"Authorization": "Bearer test-token"})

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["username"] == user_response_data["username"]
        assert response_data["email"] == user_response_data["email"]

    @patch("core.security.jwt.decode")
    @patch("routers.users.get_user")
    def test_get_user_endpoint_not_found(self, mock_get_user, mock_jwt_decode):
        # Setup mocks
        mock_jwt_decode.return_value = {"id": "test@example.com"}
        mock_get_user.side_effect = FileNotFoundError("User not found")

        # Make request with authorization header
        response = client.get("/users/user", headers={"Authorization": "Bearer test-token"})

        # Assert
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    @patch("core.security.jwt.decode")
    @patch("routers.users.get_user")
    def test_get_user_endpoint_unexpected_error(self, mock_get_user, mock_jwt_decode):
        # Setup mocks
        mock_jwt_decode.return_value = {"id": "test@example.com"}
        mock_get_user.side_effect = Exception("Unexpected error")

        # Make request with authorization header
        response = client.get("/users/user", headers={"Authorization": "Bearer test-token"})

        # Assert
        assert response.status_code == 500
        assert "Unexpected Error" in response.json()["detail"]

    @patch("routers.users.user_login")
    def test_login_user_endpoint_success(self, mock_user_login):
        # Arrange
        login_data = {"email": "test@example.com", "password": "securepassword123"}
        token = "valid_token"

        # Set up mock
        mock_user_login.return_value = token

        # Act
        response = client.post("/users/login", json=login_data)

        # Assert
        assert response.status_code == 200
        assert response.json() == token

    @patch("routers.users.user_login")
    def test_login_user_endpoint_invalid_credentials(self, mock_user_login):
        # Arrange
        login_data = {"email": "test@example.com", "password": "wrongpassword"}

        # Set up mock
        mock_user_login.side_effect = ValueError("Invalid password or email")

        # Act
        response = client.post("/users/login", json=login_data)

        # Assert
        assert response.status_code == 400
        assert "Invalid password or email" in response.json()["detail"]

    @patch("routers.users.user_login")
    def test_login_user_endpoint_unexpected_error(self, mock_user_login):
        # Arrange
        login_data = {"email": "test@example.com", "password": "securepassword123"}

        # Set up mock
        mock_user_login.side_effect = Exception("Unexpected error")

        # Act
        response = client.post("/users/login", json=login_data)

        # Assert
        assert response.status_code == 500
        assert "Unexpected Error" in response.json()["detail"]