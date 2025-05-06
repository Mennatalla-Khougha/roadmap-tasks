from fastapi import APIRouter, HTTPException
from core.exceptions import InvalidRoadmapError, InvalidTaskError, InvalidTopicError, RoadmapNotFoundError, TaskNotFoundError, TopicNotFoundError
from models.roadmap_model import Roadmap, Topic, Task
from services.roadmap_service import (
    create_roadmap,
    get_all_roadmaps,
    get_all_roadmaps_ids,
    get_all_roadmap_topics,
    get_all_roadmap_topic_tasks,
    get_roadmap,
    update_roadmap,
    update_topic,
    update_task,
    delete_roadmap,
    delete_all_roadmaps,
    delete_topic,
    delete_task,
)

router = APIRouter(prefix="/roadmaps", tags=["roadmaps"])

@router.post("/", response_model=dict)
async def create_roadmap_endpoint(roadmap: Roadmap):
    try:
        return await create_roadmap(roadmap)
    except InvalidRoadmapError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")


@router.get("/ids", response_model=list[str])
async def get_all_roadmaps_id_endpoint():
    try:
        return await get_all_roadmaps_ids()
    except RoadmapNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")


@router.get("/", response_model=list[Roadmap])
async def get_all_roadmaps_endpoint():
    try:
        return await get_all_roadmaps()
    except RoadmapNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidRoadmapError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")
    

@router.get("/{roadmap_id}/topics", response_model=list[Topic])
async def get_all_roadmap_topics_endpoint(roadmap_id: str):
    try:
        return await get_all_roadmap_topics(roadmap_id)
    except RoadmapNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TopicNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidTopicError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")


@router.get("/{roadmap_id}", response_model=Roadmap)
async def get_roadmap_endpoint(roadmap_id: str):
    try:
        return await get_roadmap(roadmap_id)
    except RoadmapNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidRoadmapError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")
    

@router.get("/{roadmap_id}/topics/{topic_id}/tasks", response_model=list[Task])
async def get_all_roadmap_topic_tasks_endpoint(roadmap_id: str, topic_id: str):
    try:
        return await get_all_roadmap_topic_tasks(roadmap_id, topic_id)
    except RoadmapNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TopicNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidTaskError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")
    

@router.delete("/{roadmap_id}", response_model=dict)
async def delete_roadmap_endpoint(roadmap_id: str):
    try:
        return await delete_roadmap(roadmap_id)
    except RoadmapNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")


@router.delete("/", response_model=dict)
async def delete_all_roadmaps_endpoint():
    try:
        return await delete_all_roadmaps()
    except RoadmapNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")


@router.put("/{roadmap_id}", response_model=dict)
async def update_roadmap_endpoint(roadmap_id: str, roadmap: Roadmap):
    try:
        return await update_roadmap(roadmap_id, roadmap)
    except RoadmapNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidRoadmapError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")


@router.put("/{roadmap_id}/{topic_id}", response_model=dict)
async def update_topic_endpoint(roadmap_id: str, topic_id: str, topic: Topic):
    try:
        return await update_topic(roadmap_id, topic_id, topic)
    except RoadmapNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TopicNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidTopicError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")
    

@router.put("/{roadmap_id}/{topic_id}/{task_id}", response_model=dict)
async def update_task_endpoint(roadmap_id: str, topic_id: str, task_id: str, task: Task):
    try:
        return await update_task(roadmap_id, topic_id, task_id, task)
    except RoadmapNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TopicNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidTaskError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")
    

@router.delete("/{roadmap_id}/{topic_id}", response_model=dict)
async def delete_topic_endpoint(roadmap_id: str, topic_id: str):
    try:
        return await delete_topic(roadmap_id, topic_id)
    except RoadmapNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TopicNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")
    

@router.delete("/{roadmap_id}/{topic_id}/{task_id}", response_model=dict)
async def delete_task_endpoint(roadmap_id: str, topic_id: str, task_id: str):
    try:
        return await delete_task(roadmap_id, topic_id, task_id)
    except RoadmapNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TopicNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")