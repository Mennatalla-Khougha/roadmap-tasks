import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch, call
import asyncio

from google.cloud.firestore import WriteBatch
from schemas.roadmap_model import Roadmap, Topic, Task
from core.exceptions import RoadmapNotFoundError, InvalidRoadmapError
from services.roadmap_services import (
    generate_id,
    write_roadmap,
    create_roadmap,
    get_all_roadmaps_ids,
    get_all_roadmaps,
    get_roadmap,
    get_roadmaps_paginated,
    delete_roadmap,
    delete_all_roadmaps,
    update_roadmap
)


@pytest.fixture
def sample_task():
    return Task(
        id="task-1",
        task="Learn Python basics",
        description="Start with variables and basic syntax",
        completed=False
    )


@pytest.fixture
def sample_topic(sample_task):
    return Topic(
        id="python-basics",
        title="Python Basics",
        description="Fundamentals of Python programming",
        duration_days=14,
        resources=["book1", "video1"],
        tasks=[sample_task]
    )


@pytest.fixture
def sample_roadmap(sample_topic):
    return Roadmap(
        id="python-roadmap",
        title="Python Roadmap",
        description="Complete guide to learning Python",
        total_duration_weeks=12,
        topics=[sample_topic]
    )


@pytest.fixture
def mock_db():
    with patch("services.roadmap_services.db") as mock:
        mock_collection_ref = MagicMock()
        mock.collection.return_value = mock_collection_ref
        mock_doc_ref = MagicMock()
        mock_collection_ref.document.return_value = mock_doc_ref
        yield mock


@pytest.fixture
def mock_redis():
    with patch("services.roadmap_services.r") as mock:
        # Make sure delete doesn't cause issues
        mock.delete.return_value = True
        mock.get.return_value = None
        mock.set.return_value = True
        mock.flushall.return_value = True
        yield mock


def test_generate_id():
    assert generate_id("Python Roadmap") == "python-roadmap"
    assert generate_id("Machine Learning!") == "machine-learning"
    assert generate_id("Data Science & Analytics") == "data-science-analytics"


@pytest.mark.asyncio
async def test_write_roadmap():
    # Setup
    parent = MagicMock()
    roadmap = Roadmap(
        title="Python Roadmap",
        description="Guide to learning Python",
        total_duration_weeks=12,
        topics=[
            Topic(
                title="Python Basics",
                description="Fundamentals",
                duration_days=7,
                resources=["link1"],
                tasks=[
                    Task(task="Learn variables", description="", completed=False)
                ]
            )
        ]
    )
    batch = MagicMock()  # Corrected line: provide a generic mock for the batch parameter

    # Mock document references
    roadmap_ref = MagicMock()
    parent.document.return_value = roadmap_ref

    topic_ref = MagicMock()
    roadmap_ref.collection.return_value.document.return_value = topic_ref

    task_ref = MagicMock()
    topic_ref.collection.return_value.document.return_value = task_ref

    # Call function
    roadmap_id = await write_roadmap(parent, roadmap, batch)

    # Assert
    assert roadmap_id == "python-roadmap"
    assert batch.set.call_count == 3  # Roadmap, topic, task
    parent.document.assert_called_once_with("python-roadmap")


@pytest.mark.asyncio
async def test_write_roadmap_invalid_roadmap():
    with pytest.raises(InvalidRoadmapError):
        await write_roadmap(MagicMock(), "not a roadmap", MagicMock())


@pytest.mark.asyncio
async def test_create_roadmap(mock_db, sample_roadmap):
    # Setup
    mock_db.batch.return_value = MagicMock()
    mock_db.collection.return_value = MagicMock()

    with patch("services.roadmap_services.write_roadmap", new_callable=AsyncMock) as mock_write, \
         patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
        mock_write.return_value = "python-roadmap"

        # Call function
        result = await create_roadmap(sample_roadmap)

        # Assert
        assert result == {"roadmap_id": "python-roadmap", "roadmap_title": "Python Roadmap"}
        mock_write.assert_called_once()
        mock_to_thread.assert_called_once()  # Check that it was called, not the count


@pytest.mark.asyncio
async def test_get_all_roadmaps_ids(mock_db):
    # Setup
    doc1 = MagicMock()
    doc1.id = "roadmap1"
    doc2 = MagicMock()
    doc2.id = "roadmap2"

    mock_db.collection.return_value.stream.return_value = [doc1, doc2]

    with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
        mock_to_thread.return_value = [doc1, doc2]

        # Call function
        result = await get_all_roadmaps_ids()

        # Assert
        assert result == ["roadmap1", "roadmap2"]


@pytest.mark.asyncio
async def test_get_all_roadmaps(mock_redis, sample_roadmap):
    # Setup
    with patch("services.roadmap_services.get_all_roadmaps_ids", new_callable=AsyncMock) as mock_get_ids:
        mock_get_ids.return_value = ["roadmap1", "roadmap2"]

        # Case 1: Roadmap in cache
        mock_redis.get.side_effect = lambda x: json.dumps(sample_roadmap.model_dump()) if x == "roadmap1" else None

        # Case 2: Roadmap not in cache
        with patch("services.roadmap_services.get_roadmap", new_callable=AsyncMock) as mock_get_roadmap:
            mock_get_roadmap.return_value = sample_roadmap

            # Call function
            result = await get_all_roadmaps()

            # Assert
            assert len(result) == 2
            assert isinstance(result[0], Roadmap)
            assert isinstance(result[1], Roadmap)
            mock_get_roadmap.assert_called_once_with("roadmap2")


@pytest.mark.asyncio
async def test_get_roadmap_from_cache(mock_db, mock_redis, sample_roadmap):
    # Setup - roadmap in cache
    mock_redis.get.return_value = json.dumps(sample_roadmap.model_dump())

    # Call function
    result = await get_roadmap("python-roadmap")

    # Assert
    assert isinstance(result, Roadmap)
    assert result.title == "Python Roadmap"
    mock_redis.get.assert_called_once_with("python-roadmap")
    mock_db.collection.assert_not_called()


@pytest.mark.asyncio
async def test_get_roadmap_not_found(mock_db, mock_redis):
    # Setup - roadmap not in cache
    mock_redis.get.return_value = None

    # Setup - roadmap not in DB
    firestore_doc_mock = MagicMock()
    firestore_doc_mock.exists = False

    # Track which function is being passed to to_thread
    async def custom_mock_to_thread(func, *args, **kwargs):
        # When it's the Redis get call
        if func is mock_redis.get:
            # Call the original function to register the call
            result = func(*args, **kwargs)
            # We know this will be None based on our mock setup
            return result
        else:
            # Return a document mock with exists=False for Firestore calls
            return firestore_doc_mock

    # Patch with our custom function
    with patch("asyncio.to_thread", new=custom_mock_to_thread):
        # Call function and expect RoadmapNotFoundError
        with pytest.raises(RoadmapNotFoundError, match="Roadmap nonexistent not found"):
            await get_roadmap("nonexistent")

        # Verify Redis get was called
        mock_redis.get.assert_called_once_with("nonexistent")


@pytest.mark.asyncio
async def test_get_roadmaps_paginated(mock_db):
    # Setup
    doc1 = MagicMock()
    doc1.id = "roadmap1"
    doc2 = MagicMock()
    doc2.id = "roadmap2"

    query_mock = MagicMock()
    mock_db.collection.return_value.order_by.return_value = query_mock
    query_mock.limit.return_value = query_mock

    with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
        mock_to_thread.return_value = [doc1, doc2]

        with patch("services.roadmap_services.get_roadmap", new_callable=AsyncMock) as mock_get_roadmap:
            mock_get_roadmap.side_effect = [Roadmap(title="Roadmap 1"), Roadmap(title="Roadmap 2")]

            # Call function
            result = await get_roadmaps_paginated(limit=2)

            # Assert
            assert len(result["roadmaps"]) == 2
            assert result["has_more"] == False
            assert result["next_cursor"] is None


@pytest.mark.asyncio
async def test_delete_roadmap(mock_db, mock_redis):
    # Setup
    roadmap_ref = MagicMock()
    mock_db.collection.return_value.document.return_value = roadmap_ref

    doc_mock = MagicMock()
    doc_mock.exists = True

    topic_doc = MagicMock()
    topic_doc.id = "topic1"

    task_doc = MagicMock()
    task_doc.id = "task1"

    with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
        mock_to_thread.side_effect = [
            doc_mock,  # For roadmap document check
            [topic_doc],  # For topics list
            [task_doc],  # For tasks list
            None,  # For task deletion
            None,  # For topic deletion
            None,  # For roadmap deletion
        ]

        # Call function
        result = await delete_roadmap("python-roadmap")

        # Assert
        assert result["message"] == "Roadmap and all related data deleted successfully"
        mock_redis.delete.assert_called_once_with("python-roadmap")


@pytest.mark.asyncio
async def test_delete_roadmap_not_found(mock_db, mock_redis):  # Add mock_redis parameter
    # Setup
    doc_mock = MagicMock()
    doc_mock.exists = False

    with patch("asyncio.to_thread", return_value=doc_mock):
        # Call function and expect exception
        with pytest.raises(RoadmapNotFoundError):
            await delete_roadmap("nonexistent")


@pytest.mark.asyncio
async def test_delete_all_roadmaps(mock_redis):
    # Setup
    with patch("services.roadmap_services.get_all_roadmaps_ids", new_callable=AsyncMock) as mock_get_ids:
        mock_get_ids.return_value = ["roadmap1", "roadmap2"]

        with patch("services.roadmap_services.delete_roadmap", new_callable=AsyncMock) as mock_delete:
            # Call function
            result = await delete_all_roadmaps()

            # Assert
            assert result["message"] == "All roadmaps deleted successfully"
            mock_redis.flushall.assert_called_once()
            assert mock_delete.call_count == 2
            mock_delete.assert_has_calls([call("roadmap1"), call("roadmap2")])


@pytest.mark.asyncio
async def test_update_roadmap(mock_db, mock_redis, sample_roadmap):
    # Setup
    roadmap_ref = MagicMock()
    mock_db.collection.return_value.document.return_value = roadmap_ref

    topic_ref = MagicMock()
    roadmap_ref.collection.return_value = topic_ref

    topic_doc_ref = MagicMock()
    topic_ref.document.return_value = topic_doc_ref

    task_ref = MagicMock()
    topic_doc_ref.collection.return_value = task_ref

    task_doc_ref = MagicMock()
    task_ref.document.return_value = task_doc_ref

    with patch("asyncio.to_thread", new_callable=AsyncMock):
        # Call function
        result = await update_roadmap("python-roadmap", sample_roadmap)

        # Assert
        assert result["message"] == "Roadmap updated successfully"
        mock_redis.delete.assert_called_once_with("python-roadmap")
        mock_redis.set.assert_called_once()