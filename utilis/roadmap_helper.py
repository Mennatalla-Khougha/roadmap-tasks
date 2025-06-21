import asyncio
import re

from google.cloud import firestore

from core.exceptions import InvalidRoadmapError, RoadmapNotFoundError
from schemas.roadmap_model import Roadmap, Task, Topic


def generate_id(title: str) -> str:
    """
    Generate a unique ID for the roadmap based on its title.
    This function converts the title to lowercase,
    replaces spaces with hyphens,
    and removes special characters.
    """
    title = title.lower()
    title = re.sub(r'[^\w\s-]', '', title)
    title = re.sub(r'\s+', '-', title)
    return title


async def write_roadmap(
        parent: firestore.CollectionReference,
        roadmap: Roadmap,
        batch: firestore.WriteBatch,
        roadmap_id: str = None,
) -> str:
    """
    Write a roadmap to Firestore.
    Args:
        parent: Firestore collection reference where the roadmap will be stored
        roadmap: Roadmap object to be written
        batch: Firestore write batch for atomic operations
        roadmap_id: Optional ID for the roadmap, if not provided, it will be
                    generated
    Returns:
        The ID of the written roadmap
    Raises:
        InvalidRoadmapError: If the provided roadmap object is invalid
    """
    try:
        if not isinstance(roadmap, Roadmap):
            raise InvalidRoadmapError("Invalid roadmap object provided")
        if not roadmap_id:
            roadmap_id = generate_id(roadmap.title)
        roadmap_data = roadmap.model_dump(exclude={"topics"})
        roadmap_data["id"] = roadmap_id
        roadmap_data["description"] = roadmap_data.get("description", "")
        roadmap_ref = parent.document(roadmap_id)
        batch.set(roadmap_ref, roadmap_data)

        for topic in roadmap.topics:
            topic_id = topic.id if topic.id else generate_id(topic.title)
            topic_data = topic.model_dump(exclude={"tasks"})
            topic_data["id"] = topic_id
            topic_data["description"] = topic_data.get("description", "")
            topic_ref = roadmap_ref.collection("topics").document(topic_id)
            batch.set(topic_ref, topic_data)

            for task in topic.tasks:
                task_id = task.id if task.id else generate_id(task.task)
                task_ref = topic_ref.collection("tasks").document(task_id)
                task_data = task.model_dump()
                task_data["id"] = task_id
                task_data["description"] = task_data.get("description", "")
                task_data["topic_id"] = topic_id
                batch.set(task_ref, task_data)

        return roadmap_id
    except InvalidRoadmapError as e:
        raise InvalidRoadmapError(f"Invalid data: {str(e)}")


async def fetch_topic_tasks(
        parent: firestore.CollectionReference,
        topic_id: str
) -> list[Task]:
    """
    Fetch tasks for a specific topic from Firestore.
    Args:
        parent: Firestore collection reference where the topic is stored
        topic_id: ID of the topic whose tasks are to be fetched
    Returns:
        A list of Task objects
    """
    try:
        task_ref = parent.document(topic_id).collection("tasks")
        task_docs = await asyncio.to_thread(lambda: list(task_ref.stream()))
        tasks = []
        for task_doc in task_docs:
            task_data = task_doc.to_dict()
            task_data.pop("id", None)
            task = Task(id=task_doc.id, **task_data)
            tasks.append(task)
        return tasks
    except Exception as e:
        raise Exception(f"Unexpected Error while fetching tasks: {str(e)}")


async def fetch_roadmap_topics(
    parent: firestore.CollectionReference,
    roadmap_id: str
) -> list[Topic]:
    """
    Fetch topics for a specific roadmap from Firestore.
    Args:
        parent: Firestore collection reference where the roadmap is stored
        roadmap_id: ID of the roadmap whose topics are to be fetched
    Returns:
        A list of Topic objects
    """
    try:
        topic_ref = parent.document(roadmap_id).collection("topics")
        topic_docs = await asyncio.to_thread(lambda: list(topic_ref.stream()))
        topics = []

        async def get_topics_tasks(
                topic_doc: firestore.DocumentSnapshot) -> Topic:
            """
            Fetch tasks for a topic concurrently.
            """
            topic_data = topic_doc.to_dict()
            topic_data.pop("id", None)
            tasks = await fetch_topic_tasks(topic_ref, topic_doc.id)
            return Topic(id=topic_doc.id, tasks=tasks, **topic_data)
        topics_list = [get_topics_tasks(doc) for doc in topic_docs]
        topics = await asyncio.gather(*topics_list)
        return list(topics)
    except Exception as e:
        raise Exception(
            f"Unexpected Error while fetching topics: {str(e)}")


async def fetch_roadmap_from_firestore(
        parent: firestore.CollectionReference,
        roadmap_id: str
) -> Roadmap:
    """
    Fetch a specific roadmap from Firestore.
    Args:
        parent: Firestore collection reference where the roadmap is stored
        roadmap_id: ID of the roadmap to be fetched
    Returns:
        A Roadmap object
    Raises:
        RoadmapNotFoundError: If the roadmap does not exist
    """
    try:
        doc_ref = parent.document(roadmap_id)
        doc = await asyncio.to_thread(doc_ref.get)
        if not doc.exists:
            raise RoadmapNotFoundError(
                f"Roadmap with id {roadmap_id} not found.")
        roadmap_data = doc.to_dict()
        roadmap_data.pop("id", None)
        topics = await fetch_roadmap_topics(parent, roadmap_id)
        roadmap = Roadmap(id=roadmap_id, topics=topics, **roadmap_data)
        return roadmap
    except RoadmapNotFoundError:
        raise RoadmapNotFoundError(f"Roadmap with id {roadmap_id} not found.")
    except Exception as e:
        raise Exception(f"Unexpected Error while fetching roadmap: {str(e)}")


async def delete_roadmap_helper(
    parent: firestore.CollectionReference,
    roadmap_id: str
) -> dict:
    """
    Helper function to delete a roadmap and its associated topics and tasks.
    Args:
        parent: Firestore collection reference where the roadmap is stored
        roadmap_id: ID of the roadmap to be deleted
    Raises:
        RoadmapNotFoundError: If the roadmap does not exist
        TopicNotFoundError: If a topic under the roadmap does not exist
        TaskNotFoundError: If a task under a topic does not exist
    Returns:
        A success message indicating the roadmap has been deleted
    """
    try:
        doc_ref = parent.document(roadmap_id)
        doc = await asyncio.to_thread(doc_ref.get)
        if not doc.exists:
            raise RoadmapNotFoundError(f"Roadmap {roadmap_id} not found")
        topic_docs = await asyncio.to_thread(
            lambda: list(doc_ref.collection("topics").stream()))

        async def delete_topic_and_tasks(
                topic_doc: firestore.DocumentSnapshot):
            """
            Delete a topic and all its tasks concurrently.
            """
            topic_id = topic_doc.id
            topic_ref = doc_ref.collection("topics").document(topic_id)

            task_docs = await asyncio.to_thread(
                lambda: list(topic_ref.collection("tasks").stream()))
            await asyncio.gather(*[
                asyncio.to_thread(lambda: topic_ref.collection(
                    "tasks").document(task.id).delete())
                for task in task_docs
            ])
            await asyncio.to_thread(topic_ref.delete)

        await asyncio.gather(
            *[delete_topic_and_tasks(topic) for topic in topic_docs])
        await asyncio.to_thread(doc_ref.delete)
        return {"message": "Roadmap and all related data deleted successfully"}
    except RoadmapNotFoundError as e:
        raise RoadmapNotFoundError(
            f"Roadmap {roadmap_id} not found: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected Error while deleting roadmap: {str(e)}")
