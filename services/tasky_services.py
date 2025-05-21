from core.exceptions import RoadmapNotFoundError
from models.tasky_model import Topic
from services.roadmap_services import get_roadmap


async def get_all_topics(roadmap_id: str) -> list[Topic]:
    """
    Get all topics from a roadmap.
    """
    roadmap_date = await get_roadmap(roadmap_id)
    if not roadmap_date:
        raise RoadmapNotFoundError(f"Roadmap with id {roadmap_id} not found.")
    topics = roadmap_date.topics
    # print(topics)
    # ids = []
    # for topic in topics:
    #     ids.append(topic.id)
    # print(ids)
    return [topic for topic in topics]
    # return topics