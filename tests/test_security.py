import os

import pytest
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError
from fastapi import HTTPException, Depends
from fastapi.security.http import HTTPAuthorizationCredentials

from core.security import create_access_token, hash_password, pwd_context, verify_password, get_current_user, \
    get_current_admin_user
from schemas.user_model import TokenData, UserRole  # Added UserRole import

load_dotenv()

# Corrected environment variable names
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM")


@pytest.fixture
def setup_test_environment(monkeypatch):
    monkeypatch.setattr("core.security.SECRET_KEY", SECRET_KEY)
    monkeypatch.setattr("core.security.ALGORITHM", ALGORITHM)


@pytest.fixture
def mock_get_current_user(mocker):
    return mocker.patch("core.security.get_current_user")


def test_creates_valid_token():
    subject = "test@example.com"
    user_id = "12345"
    token = create_access_token(subject, user_id)
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == subject
    assert payload["id"] == user_id
    assert "iat" in payload
    assert "exp" in payload
    assert payload["exp"] > payload["iat"]
    assert payload["role"] == "user"  # Check default role


def test_creates_valid_token_with_admin_role():
    subject = "admin@example.com"
    user_id = "admin123"
    role = "admin"
    token = create_access_token(subject, user_id, user_role=role)
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == subject
    assert payload["id"] == user_id
    assert payload["role"] == role


def test_fails_with_invalid_secret_key(setup_test_environment):
    subject = "test@example.com"
    user_id = "12345"
    token = create_access_token(subject, user_id)
    with pytest.raises(JWTError):
        jwt.decode(token, "wrong_secret_key", algorithms=[ALGORITHM])


def test_fails_with_expired_token(setup_test_environment):
    subject = "test@example.com"
    user_id = "12345"
    now = datetime.now(timezone.utc)
    expired_time = now - timedelta(minutes=1)
    to_encode = {
        "sub": subject,
        "id": user_id,
        "iat": now,
        "exp": expired_time,
        "role": "user"
    }
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    with pytest.raises(ExpiredSignatureError):
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def test_handles_missing_subject_or_user_id(setup_test_environment):
    with pytest.raises(TypeError):
        create_access_token(None, "12345")
    with pytest.raises(TypeError):
        create_access_token("test@example.com", None)


def test_hashes_password_correctly():
    plain_password = "securepassword123"
    hashed_password = hash_password(plain_password)
    assert hashed_password != plain_password
    assert pwd_context.verify(plain_password, hashed_password)


def test_handles_empty_password():
    plain_password = ""
    hashed_password = hash_password(plain_password)
    assert hashed_password != plain_password
    assert pwd_context.verify(plain_password, hashed_password)


def test_handles_special_characters_in_password():
    plain_password = "!@#$%^&*()_+"
    hashed_password = hash_password(plain_password)
    assert hashed_password != plain_password
    assert pwd_context.verify(plain_password, hashed_password)


def test_handles_long_password():
    plain_password = "a" * 1000
    hashed_password = hash_password(plain_password)
    assert hashed_password != plain_password
    assert pwd_context.verify(plain_password, hashed_password)


def test_verify_correct_password():
    plain_password = "securepassword123"
    hashed_password = hash_password(plain_password)
    assert verify_password(plain_password, hashed_password)


def test_reject_incorrect_password():
    plain_password = "securepassword123"
    hashed_password = hash_password(plain_password)
    assert not verify_password("wrongpassword", hashed_password)


def test_handle_empty_plain_password():
    plain_password = ""
    hashed_password = hash_password(plain_password)
    assert verify_password(plain_password, hashed_password)


def test_reject_empty_hashed_password():
    plain_password = "securepassword123"
    with pytest.raises(ValueError):  # passlib raises ValueError for empty hash
        verify_password(plain_password, "")


def test_handle_special_characters_in_plain_password():
    plain_password = "!@#$%^&*()_+"
    hashed_password = hash_password(plain_password)
    assert verify_password(plain_password, hashed_password)


def test_handle_long_plain_password():
    plain_password = "a" * 1000
    hashed_password = hash_password(plain_password)
    assert verify_password(plain_password, hashed_password)


def test_retrieves_user_data_from_valid_token(setup_test_environment):  # Renamed for clarity
    subject = "test@example.com"
    user_id = "12345"
    user_role = UserRole.USER  # Use UserRole enum
    token_str = create_access_token(subject, user_id, user_role=user_role.value)
    auth_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token_str)
    token_data = get_current_user(auth_creds)
    assert token_data.email == subject
    assert token_data.user_id == user_id
    assert token_data.role == user_role  # Compare with UserRole enum


def test_get_current_user_invalid_scheme(setup_test_environment):
    token_str = create_access_token("test@example.com", "123")
    auth_creds = HTTPAuthorizationCredentials(scheme="Basic", credentials=token_str)  # Invalid scheme
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(auth_creds)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Not authenticated"


def test_get_current_user_no_token():
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(None)  # No token
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Not authenticated"


def test_raises_error_for_expired_token_in_get_current_user(setup_test_environment):  # Renamed for clarity
    subject = "test@example.com"
    user_id = "12345"
    now = datetime.now(timezone.utc)
    expired_time = now - timedelta(minutes=1)
    to_encode = {
        "sub": subject,
        "id": user_id,
        "iat": now,
        "exp": expired_time,
        "role": "user"
    }
    token_str = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    auth_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token_str)
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(auth_creds)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Session Expired"


def test_raises_error_for_invalid_token_in_get_current_user(setup_test_environment):  # Renamed for clarity
    token_str = "invalid.token.value"
    auth_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token_str)
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(auth_creds)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token"


def test_handles_missing_user_id_in_token_for_get_current_user(setup_test_environment):  # Renamed for clarity
    subject = "test@example.com"
    now = datetime.now(timezone.utc)
    expires_delta = timedelta(minutes=30)
    expire = now + expires_delta
    to_encode = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "role": "user"
        # "id" is missing
    }
    token_str = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    auth_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token_str)
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(auth_creds)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token payload"


# Tests for get_current_admin_user
@pytest.mark.asyncio
async def test_get_current_admin_user_success():
    admin_user_data = TokenData(email="admin@example.com", user_id="admin123", role=UserRole.ADMIN)

    # Mock the dependency get_current_user to return our admin_user_data
    async def mock_dependency():
        return admin_user_data

    # Use the Depends mechanism to inject the mocked dependency
    # This is a bit conceptual for a unit test; in integration tests, FastAPI handles this.
    # For unit testing a function that uses Depends, we often test it by providing the dependency's output directly.

    result = await get_current_admin_user(current_user=admin_user_data)
    assert result == admin_user_data


@pytest.mark.asyncio
async def test_get_current_admin_user_not_admin():
    non_admin_user_data = TokenData(email="user@example.com", user_id="user123", role=UserRole.USER)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_admin_user(current_user=non_admin_user_data)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "You do not have permission to perform this action"