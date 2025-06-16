import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from unittest.mock import patch, AsyncMock

from core.exceptions import UserNotFoundError, RoadmapNotFoundError
# Import app correctly
from main import app
from schemas.roadmap_model import Topic, Task, Roadmap
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

# Mock data for roadmaps (similar to test_roadmap_routes.py)
mock_topic = Topic(
    id="topic1",
    title="Topic 1",
    description="Description for Topic 1",
    duration_days=5,
    resources=["Resource1"],
    tasks=[Task(id="task1", task="Task 1", description="Description for Task 1", is_completed=False)]
)

mock_roadmap_data = Roadmap(
    id="roadmap123",
    title="Test Roadmap",
    description="A roadmap for testing",
    total_duration_weeks=4,
    topics=[mock_topic]
)

mock_roadmap_list_data = [mock_roadmap_data]


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
        mock_get_user.side_effect = UserNotFoundError("User not found")  # Changed from FileNotFoundError

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

    @patch("routers.users.add_roadmap_to_user", new_callable=AsyncMock)
    def test_add_roadmap_to_user_success(self, mock_add_roadmap, user_response_data):
        updated_user_response_data = user_response_data.copy()
        updated_user_response_data["user_roadmaps_ids"] = ["roadmap123"]
        mock_add_roadmap.return_value = UserResponse(**updated_user_response_data)

        response = client.post("/users/roadmaps?email=test@example.com&roadmap_id=roadmap123")

        assert response.status_code == 200
        response_json = response.json()
        assert response_json["email"] == "test@example.com"
        assert "roadmap123" in response_json["user_roadmaps_ids"]
        mock_add_roadmap.assert_called_once_with("test@example.com", "roadmap123")

    @patch("routers.users.add_roadmap_to_user", new_callable=AsyncMock)
    def test_add_roadmap_to_user_user_not_found(self, mock_add_roadmap):
        mock_add_roadmap.side_effect = UserNotFoundError("User not found")

        response = client.post("/users/roadmaps?email=test@example.com&roadmap_id=roadmap123")

        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    @patch("routers.users.add_roadmap_to_user", new_callable=AsyncMock)
    def test_add_roadmap_to_user_value_error(self, mock_add_roadmap):
        mock_add_roadmap.side_effect = ValueError("Invalid input")

        response = client.post("/users/roadmaps?email=test@example.com&roadmap_id=roadmap123")

        assert response.status_code == 400
        assert "Invalid input" in response.json()["detail"]

    @patch("routers.users.add_roadmap_to_user", new_callable=AsyncMock)
    def test_add_roadmap_to_user_unexpected_error(self, mock_add_roadmap):
        mock_add_roadmap.side_effect = Exception("Some DB error")

        response = client.post("/users/roadmaps?email=test@example.com&roadmap_id=roadmap123")

        assert response.status_code == 500
        assert "Unexpected Error" in response.json()["detail"]

    # Tests for get_user_roadmaps_endpoint
    @patch("core.security.jwt.decode")
    @patch("routers.users.get_user_roadmaps", new_callable=AsyncMock)
    def test_get_user_roadmaps_success(self, mock_get_roadmaps, mock_jwt_decode, user_response_data):
        mock_jwt_decode.return_value = {"id": "test@example.com"}
        mock_get_roadmaps.return_value = mock_roadmap_list_data

        response = client.get("/users/roadmaps", headers={"Authorization": "Bearer test-token"})

        assert response.status_code == 200
        response_json = response.json()
        assert len(response_json) == 1
        assert response_json[0]["title"] == mock_roadmap_data.title
        mock_get_roadmaps.assert_called_once_with("test@example.com")

    @patch("core.security.jwt.decode")
    @patch("routers.users.get_user_roadmaps", new_callable=AsyncMock)
    def test_get_user_roadmaps_user_not_found(self, mock_get_roadmaps, mock_jwt_decode):
        mock_jwt_decode.return_value = {"id": "test@example.com"}
        mock_get_roadmaps.side_effect = UserNotFoundError("User not found")

        response = client.get("/users/roadmaps", headers={"Authorization": "Bearer test-token"})

        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    @patch("core.security.jwt.decode")
    @patch("routers.users.get_user_roadmaps", new_callable=AsyncMock)
    def test_get_user_roadmaps_roadmap_not_found(self, mock_get_roadmaps, mock_jwt_decode):
        mock_jwt_decode.return_value = {"id": "test@example.com"}
        mock_get_roadmaps.side_effect = RoadmapNotFoundError("No roadmaps found for user")

        response = client.get("/users/roadmaps", headers={"Authorization": "Bearer test-token"})

        assert response.status_code == 404
        assert "No roadmaps found for user" in response.json()["detail"]

    @patch("core.security.jwt.decode")
    @patch("routers.users.get_user_roadmaps", new_callable=AsyncMock)
    def test_get_user_roadmaps_unexpected_error(self, mock_get_roadmaps, mock_jwt_decode):
        mock_jwt_decode.return_value = {"id": "test@example.com"}
        mock_get_roadmaps.side_effect = Exception("DB connection error")

        response = client.get("/users/roadmaps", headers={"Authorization": "Bearer test-token"})

        assert response.status_code == 500
        assert "Unexpected Error" in response.json()["detail"]

    # Tests for get_user_roadmap_endpoint
    @patch("core.security.jwt.decode")
    @patch("routers.users.get_user_roadmap", new_callable=AsyncMock)
    def test_get_user_roadmap_success(self, mock_get_roadmap, mock_jwt_decode):
        mock_jwt_decode.return_value = {"id": "test@example.com"}
        mock_get_roadmap.return_value = mock_roadmap_data

        response = client.get("/users/roadmap?roadmap_id=roadmap123", headers={"Authorization": "Bearer test-token"})

        assert response.status_code == 200
        response_json = response.json()
        assert response_json["title"] == mock_roadmap_data.title
        mock_get_roadmap.assert_called_once_with("roadmap123", "test@example.com")

    @patch("core.security.jwt.decode")
    @patch("routers.users.get_user_roadmap", new_callable=AsyncMock)
    def test_get_user_roadmap_user_not_found(self, mock_get_roadmap, mock_jwt_decode):
        mock_jwt_decode.return_value = {"id": "test@example.com"}
        mock_get_roadmap.side_effect = UserNotFoundError("User not found")

        response = client.get("/users/roadmap?roadmap_id=roadmap123", headers={"Authorization": "Bearer test-token"})

        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    @patch("core.security.jwt.decode")
    @patch("routers.users.get_user_roadmap", new_callable=AsyncMock)
    def test_get_user_roadmap_roadmap_not_found(self, mock_get_roadmap, mock_jwt_decode):
        mock_jwt_decode.return_value = {"id": "test@example.com"}
        mock_get_roadmap.side_effect = RoadmapNotFoundError("Roadmap not found for user")

        response = client.get("/users/roadmap?roadmap_id=roadmap123", headers={"Authorization": "Bearer test-token"})

        assert response.status_code == 404
        assert "Roadmap not found for user" in response.json()["detail"]

    @patch("core.security.jwt.decode")
    @patch("routers.users.get_user_roadmap", new_callable=AsyncMock)
    def test_get_user_roadmap_unexpected_error(self, mock_get_roadmap, mock_jwt_decode):
        mock_jwt_decode.return_value = {"id": "test@example.com"}
        mock_get_roadmap.side_effect = Exception("Server is down")

        response = client.get("/users/roadmap?roadmap_id=roadmap123", headers={"Authorization": "Bearer test-token"})

        assert response.status_code == 500
        assert "Unexpected Error" in response.json()["detail"]