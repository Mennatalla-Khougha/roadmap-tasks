import os
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from jose.exceptions import ExpiredSignatureError

load_dotenv()

secrete_key = os.getenv("JWT_SECRET_KEY")
algorithm = os.getenv("JWT_ALGORITHM")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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
    token = jwt.encode({"exp": expiration, **data}, secrete_key, algorithm=algorithm)
    return token


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> str:
    """
    Get the current user from the JWT token.
    """
    try:
        payload = jwt.decode(token, secrete_key, algorithms=[algorithm])
        return payload.get("id")
    except ExpiredSignatureError:
        raise ValueError("Token has expired")
    except JWTError:
        raise ValueError("Invalid token")
