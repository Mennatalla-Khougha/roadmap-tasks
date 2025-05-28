import pytest
from unittest.mock import MagicMock, patch

# Apply these patches for all tests
@pytest.fixture(autouse=True, scope="session")
def mock_database_connections():
    # Create mock objects
    mock_firestore = MagicMock()
    mock_redis = MagicMock()

    # Apply patches
    with patch("core.database.firestore.Client", return_value=mock_firestore), \
         patch("core.database.redis.Redis", return_value=mock_redis), \
         patch("core.database.db", mock_firestore), \
         patch("core.database.r", mock_redis):
        yield