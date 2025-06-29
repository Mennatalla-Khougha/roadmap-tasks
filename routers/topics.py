from fastapi import APIRouter, HTTPException, Depends
from core.exceptions import (RoadmapNotFoundError,
                             TopicNotFoundError,
                             InvalidTopicError, RoadmapError)
from core.security import get_current_user
from schemas.roadmap_model import Topic, Task
from schemas.user_model import TokenData

from services.topic_services import (get_all_topics,
                                     get_topic,
                                     get_all_topics_ids,
                                     get_all_tasks)

router = APIRouter()

# Fix: Exception handling


@router.get("/", response_model=dict)
async def get_all_topics_endpoint(
        roadmap_id: str,
        current_user_token: TokenData = Depends(get_current_user)
):
    """
    Get all topics from the roadmap.
    This endpoint retrieves all topics associated with a specific roadmap.
    Args:
        roadmap_id (str): The ID of the roadmap to retrieve topics from.
        current_user_token (TokenData): The current user's token for authentication.
    Returns:
        dict: A dictionary containing a list of topics.
    """
    try:
        topics = await get_all_topics(roadmap_id)
        return {"topics": topics}
    except RoadmapNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected Error: {str(e)}"
        )


@router.get("/ids", response_model=list[str])
async def get_all_topics_ids_endpoint(roadmap_id: str):
    """
    Get all topic IDs from the roadmap.
    This endpoint retrieves all topic IDs associated with a specific roadmap.
    Args:
        roadmap_id (str): The ID of the roadmap to retrieve topic IDs from.
    Returns:
        list[str]: A list of topic IDs associated with the roadmap.
    """
    try:
        return await get_all_topics_ids(roadmap_id)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected Error: {str(e)}")


@router.get("/{topic_id}", response_model=Topic)
async def get_topic_endpoint(roadmap_id: str, topic_id: str):
    """
    Get a specific topic from the roadmap.
    This endpoint retrieves a specific topic by its ID from a specified roadmap.
    Args:
        roadmap_id (str): The ID of the roadmap to retrieve the topic from.
        topic_id (str): The ID of the topic to retrieve.
    Returns:
        Topic: The Topic object associated with the specified topic ID.
    """
    try:
        return await get_topic(roadmap_id, topic_id)
    except TopicNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected Error: {str(e)}")


@router.get("/{topic_id}/tasks", response_model=list[Task])
async def get_all_tasks_endpoint(roadmap_id: str, topic_id: str):
    """
    Get all tasks from a specific topic in the roadmap.
    """
    try:
        return await get_all_tasks(roadmap_id, topic_id)
    except RoadmapNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{topic_id}/tasks/ids", response_model=list[str])
async def get_all_tasks_ids_endpoint(roadmap_id: str, topic_id: str):
    """
    Get all task IDs from a specific topic in the roadmap.
    """
    try:
        tasks = await get_all_tasks(roadmap_id, topic_id)
        return [task.id for task in tasks]
    except RoadmapNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{topic_id}/tasks/{task_id}", response_model=Task)
async def get_task_endpoint(roadmap_id: str, topic_id: str, task_id: str):
    """
    Get a specific task from a topic in the roadmap.
    """
    try:
        tasks = await get_all_tasks(roadmap_id, topic_id)
        for task in tasks:
            if task.id == task_id:
                return task
        raise RoadmapNotFoundError(
            f"Task with id {task_id} not found in topic {topic_id}.")
    except RoadmapNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
