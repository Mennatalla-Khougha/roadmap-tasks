from fastapi import APIRouter, HTTPException
from core.exceptions import RoadmapNotFoundError
from models.tasky_model import Topic, Task

from services.tasky_services import get_all_topics, get_topic, get_all_topics_ids, get_all_tasks

router = APIRouter()


@router.get("/", response_model=dict)
async def get_all_topics_endpoint(roadmap_id: str):
    """
    Get all topics from the roadmap.
    """
    try:
        # Assuming you have a function to get all topics from a roadmap
        topics = await get_all_topics(roadmap_id)
        return {"topics": topics}
    except RoadmapNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/ids", response_model=list[str])
async def get_all_topics_ids_endpoint(roadmap_id: str):
    """
    Get all topic IDs from the roadmap.
    """
    try:
        # Assuming you have a function to get all topic IDs from a roadmap
        return await get_all_topics_ids(roadmap_id)
    except RoadmapNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{topic_id}", response_model= Topic)
async def get_topic_endpoint(roadmap_id: str, topic_id: str):
    """
    Get a specific topic from the roadmap.
    """
    try:
        # Assuming you have a function to get a specific topic from a roadmap
        return await get_topic(roadmap_id, topic_id)
    except RoadmapNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{topic_id}/tasks", response_model=list[Task])
async def get_all_tasks_endpoint(roadmap_id: str, topic_id: str):
    """
    Get all tasks from a specific topic in the roadmap.
    """
    try:
        return await get_all_tasks(roadmap_id, topic_id)
    except RoadmapNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))