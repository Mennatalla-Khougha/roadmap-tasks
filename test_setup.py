# test_setup.py
import os
import sys
from unittest.mock import MagicMock

# Setup test environment variables
os.environ["SECRET_KEY"] = "testing-secret-key"
os.environ["ALGORITHM"] = "HS256"
os.environ["REDIS_HOST"] = "localhost"
os.environ["REDIS_PORT"] = "6379"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

# Mock database modules
sys.modules['google.cloud.firestore'] = MagicMock()
sys.modules['google.cloud.firestore_v1'] = MagicMock()
sys.modules['redis'] = MagicMock()

# Create mock objects for use in tests
mock_firestore = MagicMock()
mock_redis = MagicMock()

# Directly patch core.security constants
try:
    from core import security
    # Override the module constants directly
    security.SECRET_KEY = "testing-secret-key"
    security.ALGORITHM = "HS256"
    security.ACCESS_TOKEN_EXPIRE_MINUTES = 30
except ImportError:
    pass  # Module not loaded yet, environment variables will be used