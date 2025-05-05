from fastapi import FastAPI
from core.database import db, r
from google.cloud import firestore

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "FastAPI + Firestore + Redis is running!"}

@app.get("/firestore")
async def read_firestore():
    # test Firestore connection
    doc = db.collection('test').document('connection_check')
    doc.set({"status": "connected", "timestamp": firestore.SERVER_TIMESTAMP})
    return {"firestore_status": doc.get().to_dict()}

@app.get("/redis")
async def read_redis():
    # test Redis connection
    r.set('connection_check', 'connected')
    return {"redis_status": r.get('connection_check')}