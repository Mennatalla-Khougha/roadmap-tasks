# patch_modules.py
import os
import sys
from unittest.mock import MagicMock

# Set environment variables first
os.environ["SECRET_KEY"] = "testing-secret-key"
os.environ["ALGORITHM"] = "HS256"
os.environ["REDIS_HOST"] = "localhost"
os.environ["REDIS_PORT"] = "6379"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

# Mock database modules
sys.modules['google.cloud.firestore'] = MagicMock()
sys.modules['google.cloud.firestore_v1'] = MagicMock()
sys.modules['redis'] = MagicMock()

# Force import core.security and modify its module attributes directly
try:
    # Import the module
    from core import security

    # Override module constants directly
    security.SECRET_KEY = "testing-secret-key"
    security.ALGORITHM = "HS256"
    security.ACCESS_TOKEN_EXPIRE_MINUTES = 30

    # Re-export any functions that might have captured the old values at definition time
    original_create_token = security.create_access_token


    def patched_create_token(*args, **kwargs):
        # Force the algorithm in the token creation
        result = original_create_token(*args, **kwargs)
        return result


    # Replace the function
    security.create_access_token = patched_create_token

    print("Successfully patched security module")
except Exception as e:
    print(f"Error patching security module: {e}")