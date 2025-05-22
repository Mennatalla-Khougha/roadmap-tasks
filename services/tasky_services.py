from core.exceptions import RoadmapNotFoundError
from models.tasky_model import Topic, Task
from services.roadmap_services import get_roadmap


async def get_all_topics(roadmap_id: str) -> list[Topic]:
    """
    Get all topics from a roadmap.
    """
    try:
        roadmap_date = await get_roadmap(roadmap_id)
        if not roadmap_date:
            raise RoadmapNotFoundError(f"Roadmap with id {roadmap_id} not found.")
        topics = roadmap_date.topics
        return [topic for topic in topics]
    except RoadmapNotFoundError as e:
        raise RoadmapNotFoundError(f"Roadmap with id {roadmap_id} not found.") from e
    except Exception as e:
        raise RoadmapNotFoundError(f"Unexpected Error: {str(e)}") from e


async def get_all_topics_ids(roadmap_id: str) -> list[str]:
    """
    Get all topic IDs from a roadmap.
    """
    try:
        topics = await get_all_topics(roadmap_id)
        return [topic.id for topic in topics]
    except RoadmapNotFoundError as e:
        raise RoadmapNotFoundError(f"Roadmap with id {roadmap_id} not found.") from e
    except Exception as e:
        raise RoadmapNotFoundError(f"Unexpected Error: {str(e)}") from e

async def get_topic(roadmap_id: str, topic_id: str) -> Topic:
    """
    Get a specific topic from a roadmap.
    """
    try:
        topics = await get_all_topics(roadmap_id)
        for topic in topics:
            if topic.id == topic_id:
                return topic
        raise RoadmapNotFoundError(f"Topic with id {topic_id} not found in roadmap {roadmap_id}.")
    except RoadmapNotFoundError as e:
        raise RoadmapNotFoundError(f"Roadmap with id {roadmap_id} not found.") from e
    except Exception as e:
        raise RoadmapNotFoundError(f"Unexpected Error: {str(e)}") from e


async def get_all_tasks(roadmap_id: str, topic_id: str) -> list[Task]:
    """
    Get all tasks from a specific topic in a roadmap.
    """
    try:
        topic = await get_topic(roadmap_id, topic_id)
        tasks = topic.tasks
        return [task for task in tasks]
    except RoadmapNotFoundError as e:
        raise RoadmapNotFoundError(f"Roadmap with id {roadmap_id} not found.") from e
    except Exception as e:
        raise RoadmapNotFoundError(f"Unexpected Error: {str(e)}") from e
