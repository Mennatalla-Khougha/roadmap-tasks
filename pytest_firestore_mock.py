# pytest_firestore_mock.py
from unittest.mock import MagicMock
import os
import sys

# Create mock objects once
mock_firestore = MagicMock()
mock_redis = MagicMock()


def pytest_configure(config):
    # Patch the modules before any tests are imported
    sys.modules['google.cloud.firestore'] = MagicMock()
    sys.modules['google.cloud.firestore_v1'] = MagicMock()
    sys.modules['redis'] = MagicMock()

    # Mock environment variables for Redis
    os.environ["REDIS_HOST"] = "localhost"
    os.environ["REDIS_PORT"] = "6379"

    # Mock environment variables for JWT
    os.environ["SECRET_KEY"] = "testing-secret-key"
    os.environ["ALGORITHM"] = "HS256"  # Common JWT algorithm

    # Set any other environment variables your app needs
    os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

    # Export the mocks for tests to use
    global mock_firestore, mock_redis
    mock_firestore = MagicMock()
    mock_redis = MagicMock()