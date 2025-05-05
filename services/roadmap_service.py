from datetime import datetime
from operator import ge
from models.roadmap_model import Roadmap, Topic, Task
from core.database import db
import re


def generate_id(title: str) -> str:
    # Generate ID from title: lowercase, replace spaces with hyphens, remove special chars
    title = re.sub(r'[^\w\s-]', '', title.lower())
    title = re.sub(r'[\s]+', '-', title)
    
    # Add timestamp to avoid collisions with duplicate titles
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"{title}-{timestamp}"

async def create_roadmap(roadmap: Roadmap) -> dict:
    # Create a new roadmap in Firestore
    if roadmap.id:
      roadmap_id = roadmap.id
    else:
        roadmap_id = generate_id(roadmap.title)
       
    await db.collection("roadmaps").document(roadmap_id).set({
        "title": roadmap.title,
        "description": roadmap.description,
        "total_estimated_time": roadmap.total_estimated_time,
    })

    for topic in roadmap.topics:
        if topic.id:
          topic_id = topic.id
        else:
            topic_id = generate_id(topic.title)

        await db.collection("roadmaps").document(roadmap_id)\
          .collection("topics").document(topic_id).set({
             "title": topic.title,
             "description": topic.description,
             "estimated_time": topic.estimated_time,
             "resources": topic.resources
        })
           
        for task in topic.tasks:
          if task.id:
              task_id = task.id
          else:
              task_id = generate_id(task.title)

          await db.collection("roadmaps").document(roadmap_id)\
            .collection("topics").document(topic_id)\
            .collection("tasks").document(task_id).set(
               task.model_dump()
            )

    return ({"roadmap_id": roadmap_id, "roadmap_title": roadmap.title})


async def get_all_roadmaps_ids() -> list[str]:
  # get all available roadmaps title
  try:
    docs = await db.collection("roadmaps").stream()

    roadmaps_ids = []

    for doc in docs:
       doc_id = doc.id
       roadmaps_ids.append(doc_id)
    
    return roadmaps_ids
  except Exception as e:
     raise Exception(detail= str(e)) 


async def get_all_roadmaps() -> list[Roadmap]:
  # Get all roadmaps
  try:
      docs = await db.collection("roadmaps").stream()
      roadmaps = []

      for doc in docs:
          doc_data = doc.to_dict()
          roadmap_id = doc.id
          topics_ref = await db.collection("roadmaps").document(roadmap_id).collection("topics")
          topics = []

          for topic_doc in topics_ref.stream():
              topic_data = topic_doc.to_dict()
              topic_id = topic_doc.id
              task_docs = topics_ref.document(topic_id).collection("tasks").stream()
              tasks = [Task(id=task_doc.id, **task_doc.to_dict()) for task_doc in task_docs]
              topics.append(Topic(id=topic_id, Tasks=tasks, **topic_data))

          roadmaps.append(Roadmap(id=roadmap_id, topics=topics, **doc_data))
      
      return roadmaps
  except Exception as e:
      raise Exception(detail=str(e))


async def get_all_roadmap_topics(roadmap_id: str) -> list[Topic]:
  # Get all tasks in a specific roadmap
  try:
      topic_ref = await db.collection("roadmaps").document(roadmap_id).collection("topics")
      topics = []

      for topic_doc in topic_ref.stream():
          topic_data = topic_doc.to_dict()
          topic_id = topic_doc.id
          task_docs = topic_ref.document(topic_id).collection("tasks").stream()
          tasks = [Task(id=task_doc.id, **task_doc.to_dict()) for task_doc in task_docs]
          topics.append(Topic(id=topic_id, Tasks=tasks, **topic_data))
      
      return topics
  except Exception as e:
      raise Exception(detail=str(e))


async def get_all_roadmap_topic_tasks(roadmap_id: str, topic_id: str) -> list[Task]:
  # Get all tasks in a specific topic of a roadmap
  try:
      task_ref = await db.collection("roadmaps").document(roadmap_id)\
        .collection("topics").document(topic_id).collection("tasks")
      tasks = []

      for task_doc in task_ref.stream():
          task_data = task_doc.to_dict()
          task_id = task_doc.id
          tasks.append(Task(id=task_id, **task_data))
      
      return tasks
  except Exception as e:
      raise Exception(detail=str(e))


async def get_roadmap(roadmap_id: str) -> Roadmap:
  # Get a specific roadmap
  try:
      doc = await db.collection("roadmaps").document(roadmap_id).get()
      if not doc.exists:
        raise Exception("Roadmap doesn't exist")
      roadmap_data = doc.to_dict()
      roadmap = Roadmap(id=roadmap_id, **roadmap_data)

      topic_ref = await db.collection("roadmaps").document(roadmap_id).collection("topics")
      topics = []

      for topic_doc in topic_ref.stream():
          topic_data = topic_doc.to_dict()
          topic_id = topic_doc.id
          task_docs = topic_ref.document(topic_id).collection("tasks").stream()
          tasks = [Task(id=task_doc.id, **task_doc.to_dict()) for task_doc in task_docs]
          topics.append(Topic(id=topic_id, Tasks=tasks, **topic_data))
      
      roadmap.topics = topics
      return roadmap
  except Exception as e:
      raise Exception(detail=str(e))


async def delete_roadmap(roadmap_id: str) -> dict:
  # Delete a specific roadmap
  try:
      await db.collection("roadmaps").document(roadmap_id).delete()
      return {"message": "Roadmap deleted successfully"}
  except Exception as e:
      raise Exception(detail=str(e))


async def delete_all_roadmaps() -> dict:
  # Delete all roadmaps
  try:
      docs = await db.collection("roadmaps").stream()
      for doc in docs:
          doc.reference.delete()
      return {"message": "All roadmaps deleted successfully"}
  except Exception as e:
      raise Exception(detail=str(e))


async def update_roadmap(roadmap_id: str, roadmap: Roadmap) -> dict:
  # Update a specific roadmap
  try:
      await db.collection("roadmaps").document(roadmap_id).update({
          "title": roadmap.title,
          "description": roadmap.description,
          "total_estimated_time": roadmap.total_estimated_time,
      })
      topic_ref = await db.collection("roadmaps").document(roadmap_id).collection("topics")
      for topic in roadmap.topics:
          if topic.id:
              topic_id = topic.id
          else:
              topic_id = re.sub(r'[^\w\s-]', '', topic.title.lower())
              topic_id = re.sub(r'[\s]+', '-', topic_id)
              timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
              topic_id = f"{topic_id}-{timestamp}"

          topic_ref.document(topic_id).set({
              "title": topic.title,
              "description": topic.description,
              "estimated_time": topic.estimated_time,
              "resources": topic.resources
          })

          task_ref = topic_ref.document(topic_id).collection("tasks")
          for task in topic.tasks:
              if task.id:
                  task_id = task.id
              else:
                  task_id = re.sub(r'[^\w\s-]', '', task.title.lower())
                  task_id = re.sub(r'[\s]+', '-', task_id)
                  timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                  task_id = f"{task_id}-{timestamp}"

              task_ref.document(task_id).set(task.model_dump())
      return {"message": "Roadmap updated successfully"}
  except Exception as e:
      raise Exception(detail=str(e))


async def update_topic(roadmap_id: str, topic_id: str, topic: Topic) -> dict:
  # Update a specific topic in a roadmap
  try:
      await db.collection("roadmaps").document(roadmap_id)\
        .collection("topics").document(topic_id).update({
          "title": topic.title,
          "description": topic.description,
          "estimated_time": topic.estimated_time,
          "resources": topic.resources
      })
      return {"message": "Topic updated successfully"}
  except Exception as e:
      raise Exception(detail=str(e))


async def update_task(roadmap_id: str, topic_id: str, task_id: str, task: Task) -> dict:
  # Update a specific task in a topic of a roadmap
  try:
      await db.collection("roadmaps").document(roadmap_id)\
        .collection("topics").document(topic_id)\
        .collection("tasks").document(task_id).update(
        task.model_dump()
      )
      return {"message": "Task updated successfully"}
  except Exception as e:
      raise Exception(detail=str(e))


async def delete_topic(roadmap_id: str, topic_id: str) -> dict:
  # Delete a specific topic in a roadmap
  try:
      db.collection("roadmaps").document(roadmap_id)\
        .collection("topics").document(topic_id).delete()
      return {"message": "Topic deleted successfully"}
  except Exception as e:
      raise Exception(detail=str(e))


async def delete_task(roadmap_id: str, topic_id: str, task_id: str) -> dict:
  # Delete a specific task in a topic of a roadmap
  try:
      db.collection("roadmaps").document(roadmap_id)\
        .collection("topics").document(topic_id)\
        .collection("tasks").document(task_id).delete()
      return {"message": "Task deleted successfully"}
  except Exception as e:
      raise Exception(detail=str(e))
