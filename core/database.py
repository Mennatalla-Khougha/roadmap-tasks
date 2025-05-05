import redis
from google.cloud import firestore
import os

# Firestore
db = firestore.Client()

# Redis
r = redis.Redis(host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")), decode_responses=True)
