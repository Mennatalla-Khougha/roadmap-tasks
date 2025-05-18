import json
import pytest
from unittest.mock import AsyncMock, patch
from services.roadmap_services import create_roadmap, generate_id
from models.roadmap_model import Roadmap, Topic, Task


@pytest.mark.asyncio
async def test_create_roadmap():
    # Load the JSON data from the file
    with open("/app/data.json", "r") as file:
        data = json.load(file)

    # Create a Roadmap object from the JSON data
    roadmap = Roadmap(
        title=data["title"],
        description=data.get("description", ""),
        total_duration_weeks=data["total_duration_weeks"],
        topics=[
            Topic(
                title=topic["title"],
                description=topic.get("description", ""),
                duration_days=topic.get("duration_days"),
                resources=topic.get("resources", []),
                tasks=[
                    Task(
                        task=task["task"],
                        description=task.get("description", ""),
                        duration_minutes=task.get("duration_minutes")
                    ) for task in topic.get("tasks", [])
                ]
            ) for topic in data["topics"]
        ]
    )

    # Mock Firestore batch and its methods
    mock_batch = AsyncMock()
    mock_batch.set = AsyncMock()
    mock_batch.commit = AsyncMock()

    # Mock Firestore db
    with patch("services.roadmaps.roadmap_services.db") as mock_db:
        mock_db.batch.return_value = mock_batch

        # Call the function
        result = await create_roadmap(roadmap)

        # Assertions
        assert result is not None
        assert result["roadmap_id"] == "data-structures-and-algorithms-dsa-mastery-roadmap"
        assert result["roadmap_title"] == data["title"]

        # Verify Firestore interactions for roadmap
        roadmap_ref = mock_db.collection("roadmaps").document(result["roadmap_id"])
        mock_batch.set.assert_any_call(roadmap_ref, {
            "id": result["roadmap_id"],
            "title": data["title"],
            "description": data.get("description", ""),
            "total_duration_weeks": data["total_duration_weeks"]
        })

        # Verify Firestore interactions for topics and tasks
        for topic in data["topics"]:
            topic_id = generate_id(topic["title"])
            topic_ref = roadmap_ref.collection("topics").document(topic_id)
            mock_batch.set.assert_any_call(topic_ref, {
                "id": topic_id,
                "title": topic["title"],
                "description": topic.get("description", ""),
                "duration_days": topic["duration_days"],
                "resources": topic["resources"]
            })

            for task in topic["tasks"]:
                task_id = generate_id(task["task"])
                task_ref = topic_ref.collection("tasks").document(task_id)
                mock_batch.set.assert_any_call(task_ref, {
                    "id": task_id,
                    "task": task["task"],
                    "description": task.get("description", ""),  # Default to empty string
                    "duration_minutes": task.get("duration_minutes")
                })

        # Verify batch commit was called
        mock_batch.commit.assert_called_once()