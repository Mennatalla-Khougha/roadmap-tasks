import os
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from jose.exceptions import ExpiredSignatureError

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM")

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
oauth2_scheme = HTTPBearer()


# Create a password context with the default hashing ALGORITHM
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def hash_password(password: str) -> str:
    """
    Hash a password using the default hashing ALGORITHM.
    Args:
        password (str): The plain text password to hash.
    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hashed password.
    Args:
        plain_password (str): The plain text password to verify.
        hashed_password (str): The hashed password to compare against.
    Returns:
        bool: True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: str,
    user_id: str,
) -> str:
    """
    Create a JWT access token with a subject and user ID.
    Args:
        subject (str): The subject of the token, typically the user's email.
        user_id (str): The unique identifier for the user.
    Returns:
        str: The encoded JWT token.
    """
    if subject is None or user_id is None:
        raise TypeError("Subject and user_id must be provided")
    now = datetime.now(timezone.utc)
    expires_delta = timedelta(minutes=30)
    expire = now + expires_delta
    to_encode = {
        "sub": subject,
        "id": user_id,
        "iat": now,
        "exp": expire
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> str:
    """
    Get the current user from the JWT token.
    Args:
        token (str): The JWT token from the request.
    Returns:
        str: The user ID extracted from the token.
    """
    try:
        if token is None or token.scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Not authenticated")
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return user_id
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session Expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


