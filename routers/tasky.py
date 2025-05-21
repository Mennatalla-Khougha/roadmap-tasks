from fastapi import APIRouter, HTTPException

from core.exceptions import RoadmapNotFoundError
from services.tasky_services import get_all_topics

router = APIRouter()


@router.get("/topics", response_model=dict)
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