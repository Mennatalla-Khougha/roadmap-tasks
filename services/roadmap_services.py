import json

from google.cloud import firestore

from schemas.roadmap_model import Roadmap, Topic, Task
from core.exceptions import RoadmapError, InvalidRoadmapError, RoadmapNotFoundError
import asyncio
from core.database import get_db, get_redis
from utilis.roadmap_helper import write_roadmap, generate_id, fetch_roadmap_from_firestore

db = get_db()
r = get_redis()

# Fix: Update Function for updating topics and tasks


async def create_roadmap(roadmap: Roadmap) -> dict:
    """
    Create a new roadmap in Firestore.
    Args:
        roadmap: Roadmap object to be created
    Returns:
        A dictionary containing the roadmap ID and title
    """
    try:
        batch = db.batch()
        parent = db.collection("roadmaps")
        roadmap_id = await write_roadmap(parent, roadmap, batch)
        await asyncio.to_thread(batch.commit)
        return {"roadmap_id": roadmap_id, "roadmap_title": roadmap.title}
    except InvalidRoadmapError as e:
        raise InvalidRoadmapError(f"Invalid data: {str(e)}")


async def get_all_roadmaps_ids() -> list[str]:
    """
    Fetch all roadmap IDs from Firestore.
    Returns:
        A list of roadmap IDs
    """
    try:
        docs = await asyncio.to_thread(
            lambda: list(db.collection("roadmaps").stream())
            )
        roadmaps_ids = [doc.id for doc in docs]
        return roadmaps_ids
    except RoadmapError as e:
        raise RoadmapError(f"Error fetching roadmaps id: {str(e)}")


async def get_all_roadmaps() -> list[Roadmap]:
    """
    Fetch all roadmaps from Firestore.
    Returns:
        A list of Roadmap objects
    """
    try:
        ids_list = await get_all_roadmaps_ids()
        roadmaps = []
        for roadmap_id in ids_list:
            cached_roadmap = r.get(roadmap_id)
            if cached_roadmap:
                roadmap_dict = json.loads(cached_roadmap)
                roadmaps.append(Roadmap(**roadmap_dict))
            else:
                roadmaps.append(await get_roadmap(roadmap_id))
        return roadmaps
    except RoadmapError as e:
        raise RoadmapError(f"Error fetching roadmaps: {str(e)}")


async def get_roadmaps_paginated(limit: int = 10, last_doc_id: str = None) -> dict:
    """
    Fetch roadmaps with pagination and concurrent processing
    
    Args:
        limit: Number of roadmaps to fetch at once
        last_doc_id: ID of the last document from previous page

    Returns:
        Dict containing roadmaps, next_cursor and has_more flag
    """
    try:
        query = db.collection("roadmaps").order_by("title")
        if last_doc_id:
            # Get the last document as a reference point
            last_doc = await asyncio.to_thread(
                lambda: db.collection("roadmaps").document(last_doc_id).get()
            )
            if not last_doc.exists:
                raise RoadmapError(f"Invalid pagination token: {last_doc_id}")

            # Start after the last document
            query = query.start_after(last_doc)
        query = query.limit(limit + 1)  # Get one extra to check if there are more
        docs = await asyncio.to_thread(lambda: list(query.stream()))

        # Check if there are more results
        has_more = len(docs) > limit
        if has_more:
            docs = docs[:limit]  # Remove the extra document
        # Set the next cursor (if there are more results)
        next_cursor = docs[-1].id if has_more and docs else None

        # Create tasks for fetching roadmap details concurrently
        roadmap_tasks = [get_roadmap(doc.id) for doc in docs]
        roadmaps = await asyncio.gather(*roadmap_tasks)

        return {
            "roadmaps": roadmaps,
            "next_cursor": next_cursor,
            "has_more": has_more
        }
        
    except RoadmapError as e:
        raise RoadmapError(f"Error fetching roadmaps: {str(e)}")


async def get_roadmap(roadmap_id: str) -> Roadmap:
    """
    Fetch a specific roadmap by ID from Firestore.
    """
    try:
        cached_roadmap = await asyncio.to_thread(r.get, roadmap_id)
        if cached_roadmap:
          roadmap_dict = json.loads(cached_roadmap)
          return Roadmap(**roadmap_dict)

        doc_ref = db.collection("roadmaps")
        roadmap = await fetch_roadmap_from_firestore(doc_ref, roadmap_id)

        serialized_roadmap = json.dumps(roadmap.model_dump())
        await asyncio.to_thread(r.set, roadmap_id, serialized_roadmap, ex=15)
        return roadmap
    except RoadmapNotFoundError:
        raise RoadmapNotFoundError(f"Roadmap {roadmap_id} not found")
    except Exception as e:
        raise Exception(f"Unexpected Error: {str(e)}")


async def delete_roadmap(roadmap_id: str) -> dict:
    """
    Delete a specific roadmap and all its topics and tasks from Firestore.
    Args:
        roadmap_id: ID of the roadmap to be deleted
    Returns:
        A dictionary containing a success message
    """
    try:
        r.delete(roadmap_id)
        roadmap_ref = db.collection("roadmaps").document(roadmap_id)
        doc = await asyncio.to_thread(roadmap_ref.get)
        if not doc.exists:
            raise RoadmapNotFoundError(f"Roadmap {roadmap_id} not found")

        # Get all topics under the roadmap
        topic_docs = await asyncio.to_thread(lambda: list(roadmap_ref.collection("topics").stream()))
        async def delete_topic_and_tasks(topic_doc):
            """
            Delete a topic and all its tasks concurrently.
            """
            topic_id = topic_doc.id
            topic_ref = roadmap_ref.collection("topics").document(topic_id)

            # Get all tasks under the topic
            task_docs = await asyncio.to_thread(lambda: list(topic_ref.collection("tasks").stream()))
            await asyncio.gather(*[
                asyncio.to_thread(lambda: topic_ref.collection("tasks").document(task.id).delete())
                for task in task_docs
            ])
            await asyncio.to_thread(topic_ref.delete)

        await asyncio.gather(*[delete_topic_and_tasks(topic) for topic in topic_docs])
        await asyncio.to_thread(roadmap_ref.delete)
        return {"message": "Roadmap and all related data deleted successfully"}
    except RoadmapNotFoundError:
        raise RoadmapNotFoundError(f"Roadmap {roadmap_id} not found")
    except Exception as e:
        raise Exception(f"Unexpected Error during deletion: {str(e)}")


async def delete_all_roadmaps() -> dict:
    """
    Delete all roadmaps and their associated topics and tasks from Firestore.
    """
    try:
        r.flushall()
        roadmap_ids = await get_all_roadmaps_ids()
        for roadmap_id in roadmap_ids:
            await delete_roadmap(roadmap_id)
        return {"message": "All roadmaps deleted successfully"}
    except RoadmapError as e:
        raise RoadmapError(f"Error deleting all roadmaps: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected Error during deletion: {str(e)}")


async def update_roadmap(roadmap_id: str, roadmap: Roadmap) -> dict:
    """
    Update a specific roadmap and its topics and tasks in Firestore.
    """
    try:
        r.delete(roadmap_id)
        roadmap_ref = db.collection("roadmaps").document(roadmap_id)
        # Update roadmap fields
        await asyncio.to_thread(roadmap_ref.update, {
            "title": roadmap.title,
            "description": roadmap.description,
            "total_duration_weeks": roadmap.total_duration_weeks,
        })
        topic_ref = roadmap_ref.collection("topics")

        async def update_topic(topic: Topic):
            """
            Update a specific topic and its tasks in Firestore.
            """
            topic_id = topic.id if topic.id else generate_id(topic.title)
            topic_doc_ref = topic_ref.document(topic_id)

            await asyncio.to_thread(topic_doc_ref.set, {
                "title": topic.title,
                "description": topic.description,
                "duration_days": topic.duration_days,
                "resources": topic.resources,
                "id": topic_id
            }, merge=True)
            task_ref = topic_doc_ref.collection("tasks")
            print(topic_id)

            async def update_task(task: Task):
                """
                Update a specific task in Firestore.
                """
                task_id = task.id if task.id else generate_id(task.task)
                task_doc_ref = task_ref.document(task_id)
                await asyncio.to_thread(task_doc_ref.set, task.model_dump(), True)
                task_doc_ref.update({"topic_id": topic_id})
                print(task_id)
            # Update all tasks concurrently
            await asyncio.gather(*[update_task(task) for task in topic.tasks])

        # Update all topics concurrently
        await asyncio.gather(*[update_topic(topic) for topic in roadmap.topics])
        serialized_roadmap = json.dumps(roadmap.model_dump())
        r.set(roadmap_id, serialized_roadmap, ex=15)
        return {"message": "Roadmap updated successfully"}
    except Exception as e:
        raise RoadmapNotFoundError(f"Roadmap {roadmap_id} not found or update failed: {str(e)}")
