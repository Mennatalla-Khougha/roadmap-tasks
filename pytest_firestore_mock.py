# pytest_firestore_mock.py (at project root)
from unittest.mock import MagicMock
import sys

# Create mock objects once
mock_firestore = MagicMock()
mock_redis = MagicMock()


def pytest_configure(config):
    # Patch the modules before any tests are imported
    import sys
    from unittest.mock import MagicMock

    # Create mock modules
    mock_firestore_module = MagicMock()
    mock_redis_module = MagicMock()

    # Patch the modules
    sys.modules['google.cloud.firestore'] = mock_firestore_module
    sys.modules['google.cloud.firestore_v1'] = mock_firestore_module
    sys.modules['redis'] = mock_redis_module

    # Export the mocks for tests to use
    global mock_firestore, mock_redis
    mock_firestore = mock_firestore_module.Client.return_value
    mock_redis = mock_redis_module.Redis.return_value