import pytest
from unittest.mock import MagicMock

# Create mock objects
mock_firestore = MagicMock()
mock_redis = MagicMock()

# Patch at module level before any imports
pytest.mock.patch("google.cloud.firestore.Client", return_value=mock_firestore).start()
pytest.mock.patch("redis.Redis", return_value=mock_redis).start()
pytest.mock.patch("core.database.db", mock_firestore).start()
pytest.mock.patch("core.database.r", mock_redis).start()

@pytest.fixture(scope="session")
def mock_db():
    return mock_firestore

@pytest.fixture(scope="session")
def mock_redis():
    return mock_redis