# patch_modules.py
import os
import sys
import importlib
from unittest.mock import MagicMock

# 1. Set env vars before any imports
os.environ["SECRET_KEY"] = "testing-secret-key"
os.environ["ALGORITHM"] = "HS256"
os.environ["REDIS_HOST"] = "localhost"
os.environ["REDIS_PORT"] = "6379"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

# 2. Mock Firestore/Redis
sys.modules['google.cloud.firestore'] = MagicMock()
sys.modules['google.cloud.firestore_v1'] = MagicMock()
sys.modules['redis'] = MagicMock()

# 3. Import & reload core.security so it picks up new env vars
import core.security
importlib.reload(core.security)
core.security.SECRET_KEY = "testing-secret-key"
core.security.ALGORITHM = "HS256"
core.security.ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 4. Patch jose.jwt.encode/decode
import jose.jwt

_original_encode = jose.jwt.encode
_original_decode = jose.jwt.decode

def patched_encode(claims, key=None, algorithm=None, **kwargs):
    return _original_encode(claims, "testing-secret-key", algorithm="HS256", **kwargs)

def patched_decode(token, key=None, algorithms=None, **kwargs):
    return _original_decode(token, "testing-secret-key", algorithms=["HS256"], **kwargs)

jose.jwt.encode = patched_encode
jose.jwt.decode = patched_decode

print("patch_modules applied: security reloaded; jwt.encode/decode patched")