import json
import re
from datetime import datetime
from models.roadmap_model import Roadmap, Topic, Task
from core.database import db
from core.exceptions import RoadmapError, TopicNotFoundError, TaskNotFoundError, InvalidRoadmapError, RoadmapNotFoundError
import asyncio
from core.database import r


def generate_id(title: str) -> str:
    # Generate ID from title: lowercase, replace spaces with hyphens, remove special chars
    title = re.sub(r'[^\w\s-]', '', title.lower())
    title = re.sub(r'[\s]+', '-', title)
    
    # # Add timestamp to avoid collisions with duplicate titles
    # timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    # return f"{title}-{timestamp}"
    return title


from google.cloud import firestore

# Initialize Firestore client
db = firestore.Client()

async def create_roadmap(roadmap: Roadmap) -> dict:
    # Create roadmap
    try:
        # Generate roadmap ID if not provided
        roadmap_id = roadmap.id if roadmap.id else generate_id(roadmap.title)

        # Create batch for Firestore
        batch = db.batch()

        # Set roadmap document
        roadmap_ref = db.collection("roadmaps").document(roadmap_id)
        batch.set(roadmap_ref, {
            "title": roadmap.title,
            "description": roadmap.description,
            "total_duration_weeks": roadmap.total_duration_weeks,
        })

        # Loop through topics and add them to batch
        for topic in roadmap.topics:
            topic_id = topic.id if topic.id else generate_id(topic.title)
            topic_ref = roadmap_ref.collection("topics").document(topic_id)
            batch.set(topic_ref, {
                "title": topic.title,
                "description": topic.description,
                "duration_days": topic.duration_days,
                "resources": topic.resources
            })

            # Loop through tasks and add them to batch
            for task in topic.tasks:
                task_id = task.id if task.id else generate_id(task.task)
                task_ref = topic_ref.collection("tasks").document(task_id)
                batch.set(task_ref, task.model_dump())

        # Commit all batched operations
        await asyncio.to_thread(batch.commit)

        return {"roadmap_id": roadmap_id, "roadmap_title": roadmap.title}

    except InvalidRoadmapError as e:
        raise InvalidRoadmapError(f"Invalid data: {str(e)}")


async def get_all_roadmaps_ids() -> list[str]:
    # Fetch all roadmap IDs
    try:
        # Run the Firestore stream call in a separate thread
        docs = await asyncio.to_thread(
            lambda: list(db.collection("roadmaps").stream())
            )

        roadmaps_ids = [doc.id for doc in docs]

        return roadmaps_ids

    except RoadmapError as e:
        raise RoadmapError(f"Error fetching roadmaps id: {str(e)}")


async def get_all_roadmaps() -> list[Roadmap]:
    """Fetch all roadmaps with improved performance using concurrent fetching"""
    try:
        # # Fetch all roadmaps
        # docs = await asyncio.to_thread(
        #     lambda: list(db.collection("roadmaps").stream())
        # )
        
        # # Create tasks for fetching all roadmaps concurrently
        # roadmap_tasks = []
        # for doc in docs:
        #     roadmap_id = doc.id
        #     roadmap_tasks.append(get_roadmap(roadmap_id))
        
        # # Execute all tasks concurrently
        # roadmaps = await asyncio.gather(*roadmap_tasks)
        
        # return roadmaps
        ids_list = await get_all_roadmaps_ids()
        roadmaps = []
        for id in ids_list:
            cached_roadmap = r.get(id)
            if cached_roadmap:
                roadmap_dict = json.loads(cached_roadmap)
                roadmaps.append(Roadmap(**roadmap_dict))
            else:
                roadmaps.append(await get_roadmap(id))
        return roadmaps
    
    except RoadmapError as e:
        raise RoadmapError(f"Error fetching roadmaps: {str(e)}")


# async def get_roadmaps_paginated(limit: int = 10, last_doc_id: str = None, 
#                                            fetch_details: bool = False) -> dict:
#     """
#     Fetch roadmaps with pagination and concurrent processing
    
#     Args:
#         limit: Number of roadmaps to fetch at once
#         last_doc_id: ID of the last document from previous page
#         fetch_details: Whether to fetch complete roadmap details or just basic info
    
#     Returns:
#         Dict containing roadmaps, next_cursor and has_more flag
#     """
#     try:
#         # Start with basic query
#         query = db.collection("roadmaps").order_by("title")
        
#         # Apply pagination
#         if last_doc_id:
#             # Get the last document as a reference point
#             last_doc = await asyncio.to_thread(
#                 lambda: db.collection("roadmaps").document(last_doc_id).get()
#             )
#             if not last_doc.exists:
#                 raise RoadmapError(f"Invalid pagination token: {last_doc_id}")
                
#             # Start after the last document
#             query = query.start_after(last_doc)
            
#         # Apply limit to query
#         query = query.limit(limit + 1)  # Get one extra to check if there are more
        
#         # Execute query
#         docs = await asyncio.to_thread(lambda: list(query.stream()))
        
#         # Check if there are more results
#         has_more = len(docs) > limit
#         if has_more:
#             docs = docs[:limit]  # Remove the extra document
            
#         # Set the next cursor (if there are more results)
#         next_cursor = docs[-1].id if has_more and docs else None
            
#         roadmaps = []
        
#         if fetch_details:
#             # Create tasks for fetching roadmap details concurrently
#             roadmap_tasks = [get_roadmap(doc.id) for doc in docs]
            
#             # Execute all tasks concurrently
#             roadmaps = await asyncio.gather(*roadmap_tasks)
#         else:
#             # Just create basic roadmap objects without details
#             for doc in docs:
#                 data = doc.to_dict()
#                 roadmaps.append(Roadmap(
#                     id=doc.id,
#                     title=data.get("title", ""),
#                     description=data.get("description", ""),
#                     total_duration_weeks=data.get("total_duration_weeks", 0),
#                     topics=[]  # Empty topics list
#                 ))
            
#         return {
#             "roadmaps": roadmaps,
#             "next_cursor": next_cursor,
#             "has_more": has_more
#         }
        
#     except RoadmapError as e:
#         raise RoadmapError(f"Error fetching roadmaps: {str(e)}")


# async def get_all_roadmap_topics(roadmap_id: str) -> list[Topic]:
#     # Fetch all topics for a specific roadmap
#     try:
#         topics_ref = db.collection("roadmaps").document(roadmap_id)\
#           .collection("topics")

#         # Fetch topics (run in a thread to avoid blocking)
#         topic_docs = await asyncio.to_thread(lambda: list(topics_ref.stream()))
#         topics = []

#         for topic_doc in topic_docs:
#             topic_data = topic_doc.to_dict()
#             topic_id = topic_doc.id

#             # Fetch tasks for each topic
#             task_docs = await asyncio.to_thread(lambda: list(
#                 topics_ref.document(topic_id).collection("tasks").stream()
#             ))

#             tasks = [
#                 Task(id=task_doc.id, **task_doc.to_dict())
#                 for task_doc in task_docs
#             ]

#             topics.append(Topic(id=topic_id, tasks=tasks, **topic_data))

#         return topics

#     except TopicNotFoundError as e:
#         raise TopicNotFoundError(f"Topic not found: {str(e)}")


# async def get_all_roadmap_topic_tasks(roadmap_id: str, topic_id: str) -> list[Task]:
#     # Fetch all tasks for a specific topic in a roadmap
#     try:
#         task_ref = db.collection("roadmaps").document(roadmap_id)\
#             .collection("topics").document(topic_id).collection("tasks")

#         task_docs = await asyncio.to_thread(lambda: list(task_ref.stream()))
#         tasks = [
#             Task(id=task_doc.id, **task_doc.to_dict())
#             for task_doc in task_docs
#         ]

#         return tasks

#     except TaskNotFoundError as e:
#         raise TaskNotFoundError(f"Task not found: {str(e)}")


async def get_roadmap(roadmap_id: str) -> Roadmap:
    try:
        cached_roadmap = r.get(roadmap_id)
        if cached_roadmap:
          roadmap_dict = json.loads(cached_roadmap)
          return Roadmap(**roadmap_dict)

        # Fetch the roadmap document
        doc = await asyncio.to_thread(
            lambda: db.collection("roadmaps").document(roadmap_id).get()
        )

        if not doc.exists:
            raise RoadmapNotFoundError(f"Roadmap {roadmap_id} not found")
 
        roadmap_data = doc.to_dict()
        roadmap = Roadmap(id=roadmap_id, **roadmap_data)

        # Reference to topics collection
        topic_ref = db.collection("roadmaps").document(roadmap_id).collection("topics")
        topic_docs = await asyncio.to_thread(lambda: list(topic_ref.stream()))

        async def fetch_topic_with_tasks(topic_doc) -> Topic:
            topic_data = topic_doc.to_dict()
            topic_id = topic_doc.id
            topic_data.pop("id", None)

            # Fetch tasks for this topic
            task_ref = topic_ref.document(topic_id).collection("tasks")
            task_docs = await asyncio.to_thread(lambda: list(task_ref.stream()))

            tasks = [
                Task(id=task_doc.id, **{k: v for k, v in task_doc.to_dict().items() if k != "id"})
                for task_doc in task_docs
            ]

            return Topic(id=topic_id, tasks=tasks, **topic_data)

        # Fetch all topics with tasks concurrently
        topics: list[Topic] = await asyncio.gather(
            *[fetch_topic_with_tasks(doc) for doc in topic_docs]
        )

        roadmap.topics = topics
        serialized_roadmap = json.dumps(roadmap.model_dump())
        r.set(roadmap_id, serialized_roadmap, ex=15)
        
        return roadmap

    except RoadmapNotFoundError:
        raise RoadmapNotFoundError(f"Roadmap {roadmap_id} not found")
    except Exception as e:
        raise Exception(f"Unexpected Error: {str(e)}")


async def delete_roadmap(roadmap_id: str) -> dict:
    try:
        r.delete(roadmap_id)
        roadmap_ref = db.collection("roadmaps").document(roadmap_id)

        # Check if the roadmap exists
        doc = await asyncio.to_thread(roadmap_ref.get)
        if not doc.exists:
            raise RoadmapNotFoundError(f"Roadmap {roadmap_id} not found")

        # Get all topics under the roadmap
        topic_docs = await asyncio.to_thread(lambda: list(roadmap_ref.collection("topics").stream()))

        async def delete_topic_and_tasks(topic_doc):
            topic_id = topic_doc.id
            topic_ref = roadmap_ref.collection("topics").document(topic_id)

            # Get all tasks under the topic
            task_docs = await asyncio.to_thread(lambda: list(topic_ref.collection("tasks").stream()))

            # Delete all tasks concurrently
            await asyncio.gather(*[
                asyncio.to_thread(lambda: topic_ref.collection("tasks").document(task.id).delete())
                for task in task_docs
            ])

            # Delete the topic
            await asyncio.to_thread(topic_ref.delete)

        # Delete all topics and their tasks concurrently
        await asyncio.gather(*[delete_topic_and_tasks(topic) for topic in topic_docs])

        # Finally, delete the roadmap
        await asyncio.to_thread(roadmap_ref.delete)

        return {"message": "Roadmap and all related data deleted successfully"}

    except RoadmapNotFoundError:
        raise
    except Exception as e:
        raise Exception(f"Unexpected Error during deletion: {str(e)}")


async def delete_all_roadmaps() -> dict:
    try:
        r.flushall()
        # Fetch all roadmap documents
        roadmap_docs = await asyncio.to_thread(lambda: list(db.collection("roadmaps").stream()))

        async def delete_single_roadmap(roadmap_doc):
            roadmap_ref = roadmap_doc.reference

            # Fetch topics under this roadmap
            topic_docs = await asyncio.to_thread(lambda: list(roadmap_ref.collection("topics").stream()))

            async def delete_topic(topic_doc):
                topic_ref = roadmap_ref.collection("topics").document(topic_doc.id)

                # Fetch and delete all tasks under this topic concurrently
                task_docs = await asyncio.to_thread(lambda: list(topic_ref.collection("tasks").stream()))
                await asyncio.gather(*[
                    asyncio.to_thread(lambda ref=task_doc.reference: ref.delete())
                    for task_doc in task_docs
                ])

                # Delete the topic itself
                await asyncio.to_thread(topic_ref.delete)

            # Delete all topics (and their tasks) concurrently
            await asyncio.gather(*[delete_topic(topic_doc) for topic_doc in topic_docs])

            # Delete the roadmap document
            await asyncio.to_thread(roadmap_ref.delete)

        # Delete all roadmaps concurrently
        await asyncio.gather(*[delete_single_roadmap(doc) for doc in roadmap_docs])

        return {"message": "All roadmaps and related data deleted successfully"}

    except Exception as e:
        raise Exception(f"Unexpected error during deletion: {str(e)}")


async def update_roadmap(roadmap_id: str, roadmap: Roadmap) -> dict:
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
            topic_id = topic.id if topic.id else generate_id(topic.title)
            topic_doc_ref = topic_ref.document(topic_id)

            # Use set(..., merge=True) to create or update
            await asyncio.to_thread(topic_doc_ref.set, {
                "title": topic.title,
                "description": topic.description,
                "duration_days": topic.duration_days,
                "resources": topic.resources
            }, merge=True)

            task_ref = topic_doc_ref.collection("tasks")

            async def update_task(task: Task):
                task_id = task.id if task.id else generate_id(task.task)
                task_doc_ref = task_ref.document(task_id)

                await asyncio.to_thread(task_doc_ref.set, task.model_dump(), True)

            # Update all tasks concurrently
            await asyncio.gather(*[update_task(task) for task in topic.tasks])

        # Update all topics concurrently
        await asyncio.gather(*[update_topic(topic) for topic in roadmap.topics])

        serialized_roadmap = json.dumps(roadmap.model_dump())
        r.set(roadmap_id, serialized_roadmap, ex=15)
        return {"message": "Roadmap updated successfully"}

    except Exception as e:
        raise RoadmapNotFoundError(f"Roadmap {roadmap_id} not found or update failed: {str(e)}")


# async def update_topic(roadmap_id: str, topic_id: str, topic: Topic) -> dict:
#     # Update a specific topic in a roadmap
#     try:
#         # Update the topic in a thread-safe way
#         await asyncio.to_thread(
#             lambda: db.collection("roadmaps").document(roadmap_id)
#             .collection("topics").document(topic_id)
#             .update({
#                 "title": topic.title,
#                 "description": topic.description,
#                 "duration_days": topic.duration_days,
#                 "resources": topic.resources
#             })
#         )

#         # Update tasks for the topic
#         task_ref = db.collection("roadmaps").document(roadmap_id)\
#             .collection("topics").document(topic_id).collection("tasks")
        
#         for task in topic.tasks:
#             task_id = task.id if task.id else generate_id(task.task)

#             # Update the task in a thread-safe way
#             await asyncio.to_thread(
#                 lambda: task_ref.document(task_id).update(task.model_dump())
#             )

#         return {"message": "Topic updated successfully"}

#     except TopicNotFoundError as e:
#         raise TopicNotFoundError(f"Topic {topic_id} not found: {str(e)}")
  

# async def update_task(roadmap_id: str, topic_id: str, task_id: str, task: Task) -> dict:
#     # Update a specific task in a topic of a roadmap
#     try:
#         # Perform the update in a thread-safe way
#         await asyncio.to_thread(
#             lambda: db.collection("roadmaps").document(roadmap_id)
#             .collection("topics").document(topic_id)
#             .collection("tasks").document(task_id)
#             .update(task.model_dump())
#         )
#         return {"message": "Task updated successfully"}

#     except TaskNotFoundError as e:
#         raise TaskNotFoundError(f"Task {task_id} not found: {str(e)}")
  

# async def delete_topic(roadmap_id: str, topic_id: str) -> dict:
#     # Delete a specific topic in a roadmap
#     try:
#         # Perform the deletion in a thread-safe way
#         await asyncio.to_thread(
#             lambda: db.collection("roadmaps").document(roadmap_id)
#             .collection("topics").document(topic_id).delete()
#         )
#         return {"message": "Topic deleted successfully"}

#     except TopicNotFoundError as e:
#         raise TopicNotFoundError(f"Topic {topic_id} not found: {str(e)}")
  

# async def delete_task(roadmap_id: str, topic_id: str, task_id: str) -> dict:
    # Delete a specific task in a topic of a roadmap
    try:
        # Perform the deletion in a thread-safe way
        await asyncio.to_thread(
            lambda: db.collection("roadmaps").document(roadmap_id)
            .collection("topics").document(topic_id)
            .collection("tasks").document(task_id).delete()
        )
        return {"message": "Task deleted successfully"}

    except TaskNotFoundError as e:
        raise TaskNotFoundError(f"Task {task_id} not found: {str(e)}")