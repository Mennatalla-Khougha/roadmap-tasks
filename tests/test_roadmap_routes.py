import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from main import app
from schemas.roadmap_model import Roadmap, Topic, Task
from core.exceptions import InvalidRoadmapError, RoadmapNotFoundError

client = TestClient(app)

# Mock data for testing
mock_roadmap = Roadmap(
    title="Test Roadmap",
    description="Test Description",
    total_duration_weeks=4,
    topics=[
        Topic(
            id="python-basics",
            title="Python Basics",
            description="Learn Python fundamentals",
            duration_days=7,
            resources=["book1", "video1"],
            tasks=[
                Task(
                    id="install-python",
                    task="Install Python",
                    description="Install Python 3.9+",
                    is_completed=False
                )
            ]
        )
    ]
)

mock_roadmap_response = {
    "roadmap_id": "test-roadmap",
    "roadmap_title": "Test Roadmap"
}

mock_roadmap_list = [mock_roadmap]
mock_roadmap_ids = ["test-roadmap", "another-roadmap"]

mock_paginated_response = {
    "roadmaps": [mock_roadmap],
    "next_cursor": "test-roadmap",
    "has_more": False
}


@pytest.fixture
def mock_services():
    """Mock all roadmap service functions"""
    with patch("routers.roadmaps.create_roadmap", new_callable=AsyncMock) as mock_create, \
            patch("routers.roadmaps.get_all_roadmaps", new_callable=AsyncMock) as mock_get_all, \
            patch("routers.roadmaps.get_all_roadmaps_ids", new_callable=AsyncMock) as mock_get_ids, \
            patch("routers.roadmaps.get_roadmap", new_callable=AsyncMock) as mock_get, \
            patch("routers.roadmaps.delete_roadmap", new_callable=AsyncMock) as mock_delete, \
            patch("routers.roadmaps.delete_all_roadmaps", new_callable=AsyncMock) as mock_delete_all, \
            patch("routers.roadmaps.get_roadmaps_paginated", new_callable=AsyncMock) as mock_paginated:
        mock_create.return_value = mock_roadmap_response
        mock_get_all.return_value = mock_roadmap_list
        mock_get_ids.return_value = mock_roadmap_ids
        mock_get.return_value = mock_roadmap
        mock_delete.return_value = {"message": "Roadmap and all related data deleted successfully"}
        mock_delete_all.return_value = {"message": "All roadmaps deleted successfully"}
        mock_paginated.return_value = mock_paginated_response

        yield {
            "create": mock_create,
            "get_all": mock_get_all,
            "get_ids": mock_get_ids,
            "get": mock_get,
            "delete": mock_delete,
            "delete_all": mock_delete_all,
            "paginated": mock_paginated
        }


class TestRoadmapRoutes:

    def test_create_roadmap_success(self, mock_services):
        """Test successful roadmap creation"""
        response = client.post("/roadmaps/", json=mock_roadmap.model_dump())

        assert response.status_code == 200
        assert response.json() == mock_roadmap_response
        mock_services["create"].assert_called_once()

    def test_create_roadmap_invalid_data(self, mock_services):
        """Test roadmap creation with invalid data"""
        mock_services["create"].side_effect = InvalidRoadmapError("Invalid roadmap data")

        response = client.post("/roadmaps/", json=mock_roadmap.model_dump())

        assert response.status_code == 400
        assert "Invalid roadmap data" in response.json()["detail"]

    def test_create_roadmap_unexpected_error(self, mock_services):
        """Test roadmap creation with unexpected error"""
        mock_services["create"].side_effect = Exception("Database error")

        response = client.post("/roadmaps/", json=mock_roadmap.model_dump())

        assert response.status_code == 500
        assert "Unexpected Error" in response.json()["detail"]

    def test_get_all_roadmap_ids_success(self, mock_services):
        """Test successful retrieval of all roadmap IDs"""
        response = client.get("/roadmaps/ids")

        assert response.status_code == 200
        assert response.json() == mock_roadmap_ids
        mock_services["get_ids"].assert_called_once()

    def test_get_all_roadmap_ids_not_found(self, mock_services):
        """Test retrieving roadmap IDs when none exist"""
        mock_services["get_ids"].side_effect = RoadmapNotFoundError("No roadmaps found")

        response = client.get("/roadmaps/ids")

        assert response.status_code == 404
        assert "No roadmaps found" in response.json()["detail"]

    def test_get_all_roadmaps_success(self, mock_services):
        """Test successful retrieval of all roadmaps"""
        response = client.get("/roadmaps/")

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["title"] == mock_roadmap.title
        mock_services["get_all"].assert_called_once()

    def test_get_all_roadmaps_not_found(self, mock_services):
        """Test retrieving roadmaps when none exist"""
        mock_services["get_all"].side_effect = RoadmapNotFoundError("No roadmaps found")

        response = client.get("/roadmaps/")

        assert response.status_code == 404
        assert "No roadmaps found" in response.json()["detail"]

    def test_get_paginated_roadmaps_success(self, mock_services):
        """Test successful retrieval of paginated roadmaps"""
        response = client.get("/roadmaps/roadmaps-paginated?limit=5&cursor=last-id")

        assert response.status_code == 200
        assert "roadmaps" in response.json()
        assert "pagination" in response.json()
        assert response.json()["pagination"]["next_cursor"] == "test-roadmap"
        mock_services["paginated"].assert_called_once_with(limit=5, last_doc_id="last-id")

    def test_get_roadmap_by_id_success(self, mock_services):
        """Test successful retrieval of a specific roadmap"""
        response = client.get("/roadmaps/test-roadmap")

        assert response.status_code == 200
        assert response.json()["title"] == mock_roadmap.title
        mock_services["get"].assert_called_once_with("test-roadmap")

    def test_get_roadmap_by_id_not_found(self, mock_services):
        """Test retrieving a roadmap that doesn't exist"""
        mock_services["get"].side_effect = RoadmapNotFoundError("Roadmap not found")

        response = client.get("/roadmaps/nonexistent")

        assert response.status_code == 404
        assert "Roadmap not found" in response.json()["detail"]

    def test_delete_roadmap_success(self, mock_services):
        """Test successful deletion of a roadmap"""
        response = client.delete("/roadmaps/test-roadmap")

        assert response.status_code == 200
        assert "message" in response.json()
        assert "deleted successfully" in response.json()["message"]
        mock_services["delete"].assert_called_once_with("test-roadmap")

    def test_delete_roadmap_not_found(self, mock_services):
        """Test deleting a roadmap that doesn't exist"""
        mock_services["delete"].side_effect = RoadmapNotFoundError("Roadmap not found")

        response = client.delete("/roadmaps/nonexistent")

        assert response.status_code == 404
        assert "Roadmap not found" in response.json()["detail"]

    def test_delete_all_roadmaps_success(self, mock_services):
        """Test successful deletion of all roadmaps"""
        response = client.delete("/roadmaps/")

        assert response.status_code == 200
        assert "message" in response.json()
        assert "All roadmaps deleted successfully" in response.json()["message"]
        mock_services["delete_all"].assert_called_once()

    def test_delete_all_roadmaps_not_found(self, mock_services):
        """Test deleting all roadmaps when none exist"""
        mock_services["delete_all"].side_effect = RoadmapNotFoundError("No roadmaps found")

        response = client.delete("/roadmaps/")

        assert response.status_code == 404
        assert "No roadmaps found" in response.json()["detail"]
