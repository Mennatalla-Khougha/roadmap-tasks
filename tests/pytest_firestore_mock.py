# tests/pytest_firestore_mock.py
from unittest.mock import MagicMock
import sys

# Create mock objects once
mock_firestore = MagicMock()
mock_redis = MagicMock()


# This will run when the module is imported
def pytest_configure(config):
    # Patch the firestore client directly
    sys.modules['google.cloud.firestore'] = MagicMock()
    sys.modules['google.cloud.firestore_v1'] = MagicMock()
    sys.modules['redis'] = MagicMock()

    # Now patch your database module if it's already imported
    if 'core.database' in sys.modules:
        sys.modules['core.database'].get_db = lambda: mock_firestore
        sys.modules['core.database'].get_redis = lambda: mock_redis
        # Also patch the direct variables if they exist
        sys.modules['core.database'].db = mock_firestore
        sys.modules['core.database'].r = mock_redis