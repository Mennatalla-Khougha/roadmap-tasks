import redis
from google.cloud import firestore
import os
from dotenv import load_dotenv

load_dotenv()

# Create connection objects but lazy initialize them
db = None
r = None

def get_db():
    global db
    if db is None:
        db = firestore.Client()
    return db

def get_redis():
    global r
    if r is None:
        r = redis.Redis(host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")), decode_responses=True)
    return r

