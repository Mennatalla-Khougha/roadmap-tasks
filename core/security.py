import os
from dotenv import load_dotenv
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from jose.exceptions import ExpiredSignatureError

load_dotenv()

secrete_key = os.getenv("JWT_SECRET_KEY")

# Create a password context with the default hashing algorithm
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def hash_password(password: str) -> str:
    """
    Hash a password using the default hashing algorithm.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hashed password.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """
    Create a JWT access token.
    """
    expiration = datetime.now(timezone.utc) + timedelta(minutes=30)
    token = jwt.encode({"exp": expiration, **data}, secrete_key, algorithm="HS256")
    return token


def decode_access_token(token: str) -> dict:
    """
    Decode a JWT access token.
    """
    try:
        payload = jwt.decode(token, secrete_key, algorithms=["HS256"])
        return payload
    except ExpiredSignatureError:
        raise ValueError("Token has expired")
    except JWTError:
        raise ValueError("Invalid token")


