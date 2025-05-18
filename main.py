from fastapi import FastAPI
from core.database import db, r
from google.cloud import firestore

from routers import roadmaps

app = FastAPI()

# router routes
app.include_router(roadmaps.router, prefix="/roadmaps", tags=["roadmaps"])

@app.get("/")
def read_root():
    return {"message": "FastAPI + Firestore + Redis is running!"}


@app.get("/firestore")
async def read_firestore():
    # test Firestore connection
    doc = db.collection('test').document()
    generated_id = doc.id
    doc.set({"status": "testing id", "timestamp": firestore.SERVER_TIMESTAMP})

    fixed_doc = db.collection('test').document('connection_check')
    fixed_id = fixed_doc.id
    fixed_doc.set({"status": "connected", "timestamp": firestore.SERVER_TIMESTAMP})

    # Retrieve documents and process them to make them serializable
    docs = db.collection("test").stream()
    doc_list = []
    for doc in docs:
        doc_list.append(doc.to_dict())  # convert Firestore doc snapshot to a dict

    return {
        "firestore_status": doc_list,  # Now it's a list of dictionaries that can be serialized
        "generated_id": generated_id,
        "fixed_id": fixed_id
    }


@app.get("/redis")
async def read_redis():
    # test Redis connection
    r.set('connection_check', 'connected')
    return {"redis_status": r.get('connection_check')}