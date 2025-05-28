import pytest
from unittest.mock import MagicMock


@pytest.fixture(autouse=True, scope="session")
def mock_database_connections():
    # Create mock objects
    mock_firestore = MagicMock()
    mock_redis = MagicMock()

    with pytest.MonkeyPatch.context() as mp:
        # Patch the getter functions
        mp.setattr("core.database.get_db", lambda: mock_firestore)
        mp.setattr("core.database.get_redis", lambda: mock_redis)
        yield