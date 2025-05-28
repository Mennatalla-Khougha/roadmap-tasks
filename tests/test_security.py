import os

import pytest
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError
from core.security import create_access_token, hash_password, pwd_context, verify_password, get_current_user

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM")

@pytest.fixture
def setup_test_environment(monkeypatch):
    monkeypatch.setattr("core.security.SECRET_KEY", SECRET_KEY)
    monkeypatch.setattr("core.security.ALGORITHM", ALGORITHM)

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
        "exp": expired_time
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
    with pytest.raises(Exception):
        verify_password(plain_password, "")

def test_handle_special_characters_in_plain_password():
    plain_password = "!@#$%^&*()_+"
    hashed_password = hash_password(plain_password)
    assert verify_password(plain_password, hashed_password)

def test_handle_long_plain_password():
    plain_password = "a" * 1000
    hashed_password = hash_password(plain_password)
    assert verify_password(plain_password, hashed_password)

import pytest
from fastapi import HTTPException

def test_retrieves_user_id_from_valid_token(setup_test_environment):
    subject = "test@example.com"
    user_id = "12345"
    token = create_access_token(subject, user_id)
    assert get_current_user(token) == user_id

def test_raises_error_for_expired_token(setup_test_environment):
    subject = "test@example.com"
    user_id = "12345"
    now = datetime.now(timezone.utc)
    expired_time = now - timedelta(minutes=1)
    to_encode = {
        "sub": subject,
        "id": user_id,
        "iat": now,
        "exp": expired_time
    }
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Session Expired"

def test_raises_error_for_invalid_token(setup_test_environment):
    token = "invalid.token.value"
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token"

def test_handles_missing_user_id_in_token(setup_test_environment):
    subject = "test@example.com"
    now = datetime.now(timezone.utc)
    expires_delta = timedelta(minutes=30)
    expire = now + expires_delta
    to_encode = {
        "sub": subject,
        "iat": now,
        "exp": expire
    }
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    assert get_current_user(token) is None