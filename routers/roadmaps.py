from fastapi import APIRouter, HTTPException, Query
from fastapi import Depends

from core.exceptions import InvalidRoadmapError, RoadmapNotFoundError
from core.security import get_current_admin_user
from schemas.roadmap_model import Roadmap
from services.roadmap_services import (
    create_roadmap,
    get_all_roadmaps,
    get_all_roadmaps_ids,
    get_roadmap,
    delete_roadmap,
    delete_all_roadmaps,
    get_roadmaps_paginated
)

router = APIRouter()

@router.post("/", response_model=dict)
async def create_roadmap_endpoint(roadmap: Roadmap, current_user: dict = Depends(get_current_admin_user)):
    """
    Endpoint to create a new roadmap.
    """
    try:
        return await create_roadmap(roadmap)
    except InvalidRoadmapError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")


@router.get("/ids", response_model=list[str])
async def get_all_roadmaps_id_endpoint():
    """
    Endpoint to get all roadmap IDs.
    """
    try:
        return await get_all_roadmaps_ids()
    except RoadmapNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")


@router.get("/", response_model=list[Roadmap])
async def get_all_roadmaps_endpoint():
    """
    Endpoint to get all roadmaps.
    """
    try:
        return await get_all_roadmaps()
    except RoadmapNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidRoadmapError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")
    

@router.get("/roadmaps-paginated", response_model=dict)
async def get_roadmaps(
    limit: int = Query(1, ge=1, le=10),
    cursor: str = Query(None)
):
    """
    Endpoint to get paginated roadmaps.
    """
    result = await get_roadmaps_paginated(limit=limit, last_doc_id=cursor)
    return {
        "roadmaps": result["roadmaps"],
        "pagination": {
            "next_cursor": result["next_cursor"],
            "has_more": result["has_more"]
        }
    }

@router.get("/{roadmap_id}", response_model=Roadmap)
async def get_roadmap_endpoint(roadmap_id: str):
    """
    Endpoint to get a specific roadmap by ID.
    """
    try:
        return await get_roadmap(roadmap_id)
    except RoadmapNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidRoadmapError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")
    

@router.delete("/{roadmap_id}", response_model=dict)
async def delete_roadmap_endpoint(roadmap_id: str, current_user: dict = Depends(get_current_admin_user)):
    """
    Endpoint to delete a specific roadmap by ID.
    """
    try:
        return await delete_roadmap(roadmap_id)
    except RoadmapNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")


@router.delete("/", response_model=dict)
async def delete_all_roadmaps_endpoint(current_user: dict = Depends(get_current_admin_user)):
    """
    Endpoint to delete all roadmaps.
    """
    try:
        return await delete_all_roadmaps()
    except RoadmapNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")
