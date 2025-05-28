# patch_modules.py
import os
import sys
from unittest.mock import MagicMock, patch

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

# Force import and patch core.security
try:
    # Import the modules
    from core import security
    import jose.jwt

    # Override module constants
    security.SECRET_KEY = "testing-secret-key"
    security.ALGORITHM = "HS256"

    # Store original functions
    original_decode = jose.jwt.decode


    # Patch JWT decode to use hardcoded algorithm
    def patched_decode(token, key, algorithms=None, **kwargs):
        # Force HS256 algorithm regardless of what's passed in
        return original_decode(token, "testing-secret-key", algorithms=["HS256"], **kwargs)


    # Replace the function
    jose.jwt.decode = patched_decode
    print("Successfully patched JWT decode function")
except Exception as e:
    print(f"Error patching modules: {e}")