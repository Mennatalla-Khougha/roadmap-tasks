import firebase_admin
import redis
from google.cloud import firestore
import os
from dotenv import load_dotenv
from firebase_admin import credentials, firestore
import ssl

load_dotenv()

# Create connection objects but lazy initialize them
db = None
r = None

firebase_credentials = {
  "type": os.getenv("FIREBASE_TYPE"),
  "project_id": os.getenv("FIREBASE_PROJECT_ID"),
  "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
  "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
  "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
  "client_id": os.getenv("FIREBASE_CLIENT_ID"),
  "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
  "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
  "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
  "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL"),
  "universe_domain": os.getenv("FIREBASE_UNIVERSE_DOMAIN")
}

cred = credentials.Certificate(firebase_credentials)
firebase_admin.initialize_app(cred)


def get_db():
    global db
    if db is None:
        db = firestore.client()
    return db


def get_redis():
    global r
    if r is None:
        # Retrieve environment variables for Redis
        redis_host = os.getenv("REDIS_HOST")
        redis_port_str = os.getenv("REDIS_PORT")
        redis_username = os.getenv("REDIS_USERNAME")
        redis_password = os.getenv("REDIS_PASSWORD")
        redis_ssl_str = os.getenv("REDIS_SSL", "False")

        # Validate and convert port to int
        if not redis_port_str:
            raise ValueError("REDIS_PORT environment variable not set.")
        try:
            redis_port = int(redis_port_str)
        except ValueError:
            raise ValueError(f"REDIS_PORT environment variable must be an integer, got: {redis_port_str}")

        # Convert SSL string to boolean
        redis_ssl = redis_ssl_str.lower() == "true"

        if redis_ssl:
            r = redis.Redis(
                host=redis_host,
                port=redis_port,
                username=redis_username,
                password=redis_password,
                ssl=True,
                ssl_cert_reqs=ssl.CERT_NONE,
                decode_responses=True
            )
        else:
            r = redis.Redis(
                host=redis_host,
                port=redis_port,
                username=redis_username,
                password=redis_password,
                ssl=False,
                decode_responses=True
            )

        # Ping to verify connection
        try:
            r.ping()
            print("Successfully connected to Redis!")
        except redis.exceptions.ConnectionError as e:
            print(f"Failed to ping Redis after connection attempt: {e}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred during Redis connection test: {e}")
            raise

    return r