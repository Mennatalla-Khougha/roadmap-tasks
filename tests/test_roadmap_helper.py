import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from google.cloud.firestore import DocumentSnapshot

from core.exceptions import InvalidRoadmapError, RoadmapNotFoundError
from schemas.roadmap_model import Roadmap, Topic, Task
from utilis.roadmap_helper import (
    generate_id,
    write_roadmap,
    fetch_topic_tasks,
    fetch_roadmap_topics,
    fetch_roadmap_from_firestore,
    delete_roadmap_helper
)

# Mock data for testing
mock_task = Task(id="install-python", task="Install Python",
                 description="Install Python 3.9+", is_completed=False)
mock_topic = Topic(
    id="python-basics",
    title="Python Basics",
    description="Learn Python fundamentals",
    duration_days=7,
    resources=["book1"],
    tasks=[mock_task]
)
mock_roadmap = Roadmap(
    title="Test Roadmap",
    description="Test Description",
    total_duration_weeks=4,
    topics=[mock_topic]
)


@pytest.fixture
def mock_firestore():
    """Fixture to mock Firestore objects."""
    # Mock DocumentSnapshot
    mock_doc_snapshot = MagicMock()
    mock_doc_snapshot.exists = True

    # Mock DocumentReference
    mock_doc_ref = MagicMock()
    mock_doc_ref.get = MagicMock(return_value=mock_doc_snapshot)
    mock_doc_ref.delete = MagicMock()
    mock_doc_ref.collection.return_value.stream = MagicMock(return_value=[])
    mock_doc_ref.collection.return_value.document.return_value = mock_doc_ref

    # Mock CollectionReference
    mock_collection_ref = MagicMock()
    mock_collection_ref.document.return_value = mock_doc_ref
    mock_collection_ref.stream = MagicMock(return_value=[])

    # Mock WriteBatch
    mock_batch = MagicMock()
    mock_batch.set = MagicMock()

    return {
        "collection_ref": mock_collection_ref,
        "doc_ref": mock_doc_ref,
        "doc_snapshot": mock_doc_snapshot,
        "batch": mock_batch
    }


class TestGenerateId:
    def test_simple_title(self):
        assert generate_id("My Title") == "my-title"

    def test_title_with_special_chars(self):
        assert generate_id("My Title!@#$%^&*()") == "my-title"

    def test_title_with_extra_spaces(self):
        assert generate_id("My    Title") == "my-title"

    def test_title_with_hyphens(self):
        assert generate_id("My-Title") == "my-title"


@pytest.mark.asyncio
class TestWriteRoadmap:
    async def test_write_roadmap_success(self, mock_firestore):
        roadmap_id = await write_roadmap(
            mock_firestore["collection_ref"],
            mock_roadmap, mock_firestore["batch"]
        )
        assert roadmap_id == "test-roadmap"
        # 1 for roadmap, 1 for topic, 1 for task
        assert mock_firestore["batch"].set.call_count == 3

    async def test_write_roadmap_with_provided_id(self, mock_firestore):
        roadmap_id = await write_roadmap(
            mock_firestore["collection_ref"],
            mock_roadmap, mock_firestore["batch"],
            "custom-id")
        assert roadmap_id == "custom-id"
        mock_firestore["collection_ref"].document.assert_called_with(
            "custom-id")

    async def test_write_roadmap_invalid_data(self, mock_firestore):
        with pytest.raises(
                InvalidRoadmapError,
                match="Invalid roadmap object provided"
        ):
            await write_roadmap(
                mock_firestore["collection_ref"],
                {"invalid": "data"},
                mock_firestore["batch"]
            )


@pytest.mark.asyncio
class TestFetchData:
    @patch('asyncio.to_thread')
    async def test_fetch_topic_tasks_success(
            self, mock_to_thread, mock_firestore
    ):
        mock_task_doc = MagicMock()
        mock_task_doc.id = "install-python"
        mock_task_doc.to_dict.return_value = {
            "task": "Install Python",
            "description": "Install Python 3.9+",
            "is_completed": False,
            "topic_id": "python-basics"
        }
        mock_to_thread.return_value = [mock_task_doc]

        tasks = await fetch_topic_tasks(
            mock_firestore["collection_ref"], "python-basics"
        )

        assert len(tasks) == 1
        assert isinstance(tasks[0], Task)
        assert tasks[0].id == "install-python"

    @patch('asyncio.to_thread', side_effect=Exception("DB Error"))
    async def test_fetch_topic_tasks_exception(
            self, mock_to_thread, mock_firestore
    ):
        with pytest.raises(
                Exception,
                match="Unexpected Error while fetching tasks: DB Error"
        ):
            await fetch_topic_tasks(
                mock_firestore["collection_ref"], "python-basics"
            )

    @patch('utilis.roadmap_helper.fetch_topic_tasks', new_callable=AsyncMock)
    @patch('asyncio.to_thread')
    async def test_fetch_roadmap_topics_success(
            self, mock_to_thread, mock_fetch_tasks, mock_firestore
    ):
        mock_topic_doc = MagicMock()
        mock_topic_doc.id = "python-basics"
        mock_topic_doc.to_dict.return_value = {
            "title": "Python Basics",
            "description": "Learn Python fundamentals"}
        mock_to_thread.return_value = [mock_topic_doc]
        mock_fetch_tasks.return_value = [mock_task]

        topics = await fetch_roadmap_topics(
            mock_firestore["collection_ref"], "test-roadmap")

        assert len(topics) == 1
        assert isinstance(topics[0], Topic)
        assert topics[0].id == "python-basics"
        assert len(topics[0].tasks) == 1
        mock_fetch_tasks.assert_called_once()

    @patch('utilis.roadmap_helper.fetch_roadmap_topics',
           new_callable=AsyncMock)
    @patch('asyncio.to_thread')
    async def test_fetch_roadmap_from_firestore_success(
            self, mock_to_thread, mock_fetch_topics, mock_firestore
    ):
        mock_firestore["doc_snapshot"].to_dict.return_value = {
            "title": "Test Roadmap", "description": "Test Desc"}
        mock_to_thread.return_value = mock_firestore["doc_snapshot"]
        mock_fetch_topics.return_value = [mock_topic]

        roadmap = await fetch_roadmap_from_firestore(
            mock_firestore["collection_ref"], "test-roadmap"
        )

        assert isinstance(roadmap, Roadmap)
        assert roadmap.id == "test-roadmap"
        assert roadmap.title == "Test Roadmap"
        assert len(roadmap.topics) == 1
        mock_fetch_topics.assert_called_once_with(
            mock_firestore["collection_ref"], "test-roadmap")

    @patch('asyncio.to_thread')
    async def test_fetch_roadmap_from_firestore_not_found(
            self, mock_to_thread, mock_firestore
    ):
        mock_firestore["doc_snapshot"].exists = False
        mock_to_thread.return_value = mock_firestore["doc_snapshot"]

        with pytest.raises(RoadmapNotFoundError,
                           match="Roadmap with id test-roadmap not found."):
            await fetch_roadmap_from_firestore(
                mock_firestore["collection_ref"], "test-roadmap")


@pytest.mark.asyncio
class TestDeleteRoadmapHelper:
    @patch('asyncio.to_thread')
    async def test_delete_roadmap_helper_success(
            self, mock_to_thread, mock_firestore
    ):
        mock_topic_doc = MagicMock(id="python-basics")
        mock_task_doc = MagicMock(id="install-python")

        def to_thread_side_effect(func, *args, **kwargs):
            if "topics" in str(func):
                return [mock_topic_doc]
            if "tasks" in str(func):
                return [mock_task_doc]
            return func()

        mock_to_thread.side_effect = to_thread_side_effect

        result = await delete_roadmap_helper(
            mock_firestore["collection_ref"], "test-roadmap")

        assert result == {
            "message": "Roadmap and all related data deleted successfully"}
        # Check that delete was called on the main roadmap doc
        mock_firestore["doc_ref"].delete.assert_called_once()

    @patch('asyncio.to_thread')
    async def test_delete_roadmap_helper_not_found(
            self, mock_to_thread, mock_firestore
    ):
        mock_firestore["doc_snapshot"].exists = False
        mock_to_thread.return_value = mock_firestore["doc_snapshot"]

        with pytest.raises(RoadmapNotFoundError,
                           match="Roadmap test-roadmap not found"):
            await delete_roadmap_helper(
                mock_firestore["collection_ref"],
                "test-roadmap")

    @patch('asyncio.to_thread', side_effect=Exception("DB Error"))
    async def test_delete_roadmap_helper_exception(
            self, mock_to_thread,
            mock_firestore):
        with pytest.raises(
                Exception, match="Unexpected Error while deleting roadmap: "
                                 "DB Error"):
            await delete_roadmap_helper(
                mock_firestore["collection_ref"], "test-roadmap")
