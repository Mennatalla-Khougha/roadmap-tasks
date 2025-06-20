from fastapi import FastAPI

from google.cloud import firestore
from fastapi.middleware.cors import CORSMiddleware

from routers import roadmaps, users, topics
from core.database import get_db, get_redis

db = get_db()
r = get_redis()

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# router routes
app.include_router(roadmaps.router, prefix="/roadmaps", tags=["roadmaps"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(topics.router, prefix="/topics", tags=["topics"])


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
    fixed_doc.set({
            "status": "connected",
            "timestamp": firestore.SERVER_TIMESTAMP
        })

    # Retrieve documents and process them to make them serializable
    docs = db.collection("test").stream()
    doc_list = []
    for doc in docs:
        doc_list.append(doc.to_dict())

    return {
        "firestore_status": doc_list,
        "generated_id": generated_id,
        "fixed_id": fixed_id
    }


@app.get("/redis")
async def read_redis():
    # test Redis connection
    r.set('connection_check', 'connected')
    return {"redis_status": r.get('connection_check')}
