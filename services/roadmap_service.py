import re
from datetime import datetime
from models.roadmap_model import Roadmap, Topic, Task
from core.database import db
from core.exceptions import RoadmapError, TopicNotFoundError, TaskNotFoundError, InvalidRoadmapError, RoadmapNotFoundError
import asyncio


def generate_id(title: str) -> str:
    # Generate ID from title: lowercase, replace spaces with hyphens, remove special chars
    title = re.sub(r'[^\w\s-]', '', title.lower())
    title = re.sub(r'[\s]+', '-', title)
    
    # # Add timestamp to avoid collisions with duplicate titles
    # timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    # return f"{title}-{timestamp}"
    return title


async def create_roadmap(roadmap: Roadmap) -> dict:
    # Create a new roadmap
    try:
        if roadmap.id:
            roadmap_id = roadmap.id
        else:
            roadmap_id = generate_id(roadmap.title)

        # Set roadmap document
        await asyncio.to_thread(
            db.collection("roadmaps").document(roadmap_id).set,
            {
                "title": roadmap.title,
                "description": roadmap.description,
                "total_duration_weeks": roadmap.total_duration_weeks,
            }
        )

        for topic in roadmap.topics:
            topic_id = topic.id if topic.id else generate_id(topic.title)

            # Set topic document
            await asyncio.to_thread(
                db.collection("roadmaps").document(roadmap_id)
                  .collection("topics").document(topic_id).set,
                {
                    "title": topic.title,
                    "description": topic.description,
                    "duration_days": topic.duration_days,
                    "resources": topic.resources
                }
            )

            for task in topic.tasks:
                task_id = task.id if task.id else generate_id(task.task)

                # Set task document
                await asyncio.to_thread(
                    db.collection("roadmaps").document(roadmap_id)
                      .collection("topics").document(topic_id)
                      .collection("tasks").document(task_id).set,
                    task.model_dump()
                )

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
    # Fetch all roadmaps
    try:
        roadmaps = []

        # Fetch all roadmaps (synchronously, wrapped in a thread)
        docs = await asyncio.to_thread(
            lambda: list(db.collection("roadmaps").stream())
            )

        for doc in docs:
            doc_data = doc.to_dict()
            roadmap_id = doc.id

            # Fetch all topics for this roadmap
            topics_ref = db.collection("roadmaps").document(roadmap_id)\
              .collection("topics")
            topic_docs = await asyncio.to_thread(
                lambda: list(topics_ref.stream())
                )
            topics = []

            for topic_doc in topic_docs:
                topic_data = topic_doc.to_dict()
                topic_id = topic_doc.id

                # Fetch all tasks for this topic
                task_docs = await asyncio.to_thread(lambda: list(
                    topics_ref.document(topic_id).collection("tasks").stream()
                ))

                tasks = []
                for task_doc in task_docs:
                    task_data = task_doc.to_dict()
                    task_data.pop("id", None)
                    tasks.append(Task(id=task_doc.id, **task_data))

                topics.append(Topic(id=topic_id, tasks=tasks, **topic_data))

            roadmaps.append(Roadmap(id=roadmap_id, topics=topics, **doc_data))

        return roadmaps

    except RoadmapError as e:
        raise RoadmapError(f"Error fetching roadmaps: {str(e)}")


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
    # Fetch a specific roadmap
    try:
        # Run Firestore get() in a thread-safe way
        doc = await asyncio.to_thread(
            lambda: db.collection("roadmaps").document(roadmap_id).get()
        )
        if not doc.exists:
            raise RoadmapNotFoundError(f"Roadmap {roadmap_id} not found")

        roadmap_data = doc.to_dict()
        roadmap = Roadmap(id=roadmap_id, **roadmap_data)

        # Fetch topics for the roadmap
        topic_ref = db.collection("roadmaps").document(roadmap_id).collection("topics")
        topic_docs = await asyncio.to_thread(lambda: list(topic_ref.stream()))
        topics = []

        for topic_doc in topic_docs:
            topic_data = topic_doc.to_dict()
            topic_id = topic_doc.id
            topic_data.pop("id", None)  # Avoid duplicate key

            # Fetch tasks for each topic
            task_ref = topic_ref.document(topic_id).collection("tasks")
            task_docs = await asyncio.to_thread(lambda: list(task_ref.stream()))
            tasks = []
            for task_doc in task_docs:
                task_data = task_doc.to_dict()
                task_data.pop("id", None)  # Avoid duplicate key
                tasks.append(Task(id=task_doc.id, **task_data))

            topics.append(Topic(id=topic_id, tasks=tasks, **topic_data))

        roadmap.topics = topics
        return roadmap

    except RoadmapNotFoundError as e:
        raise e
    except Exception as e:
        raise Exception(f"Unexpected Error: {str(e)}")



async def delete_roadmap(roadmap_id: str) -> dict:
    # Delete a specific roadmap
    try:
        # Run Firestore delete() in a thread-safe way
        doc = await asyncio.to_thread(
            lambda: db.collection("roadmaps").document(roadmap_id).delete()
        )
        return {"message": "Roadmap deleted successfully"}
    except Exception as e:
        # Handling Firestore errors, such as if the roadmap doesn't exist
        raise RoadmapNotFoundError(f"Roadmap {roadmap_id} not found: {str(e)}")


async def delete_all_roadmaps() -> dict:
    # Delete all roadmaps
    try:
        # Run Firestore stream in a thread-safe way
        docs = await asyncio.to_thread(lambda: list(db.collection("roadmaps").stream()))

        for doc in docs:
            # Run Firestore delete in a thread-safe way
            await asyncio.to_thread(lambda: doc.reference.delete())

        return {"message": "All roadmaps deleted successfully"}

    except Exception as e:
        # Handle any errors (e.g., if no roadmaps exist)
        raise RoadmapNotFoundError(f"Roadmaps not found: {str(e)}")


async def update_roadmap(roadmap_id: str, roadmap: Roadmap) -> dict:
    # Update a specific roadmap
    try:
        # Perform Firestore update in a thread-safe way
        await asyncio.to_thread(
            lambda: db.collection("roadmaps").document(roadmap_id).update({
                "title": roadmap.title,
                "description": roadmap.description,
                "total_duration_weeks": roadmap.total_duration_weeks,
            })
        )

        # Update topics
        topic_ref = db.collection("roadmaps").document(roadmap_id).collection("topics")
        for topic in roadmap.topics:
            topic_id = topic.id if topic.id else generate_id(topic.title)

            # Perform topic update in a thread-safe way
            await asyncio.to_thread(
                lambda: topic_ref.document(topic_id).update({
                    "title": topic.title,
                    "description": topic.description,
                    "duration_days": topic.duration_days,
                    "resources": topic.resources
                })
            )

            # Update tasks for each topic
            task_ref = topic_ref.document(topic_id).collection("tasks")
            for task in topic.tasks:
                task_id = task.id if task.id else generate_id(task.task)

                # Perform task update in a thread-safe way
                await asyncio.to_thread(
                    lambda: task_ref.document(task_id).update(task.model_dump())
                )

        return {"message": "Roadmap updated successfully"}

    except Exception as e:
        # Handle errors, such as if the roadmap doesn't exist
        raise RoadmapNotFoundError(f"Roadmap {roadmap_id} not found: {str(e)}")


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