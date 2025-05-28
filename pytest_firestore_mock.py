# pytest_firestore_mock.py
from unittest.mock import MagicMock
import os
import sys
import importlib


# These module-level mocks can be used if fixtures need to return consistent instances.
# However, for sys.modules patching, new MagicMock() instances are often created directly.
# global_mock_firestore = MagicMock()
# global_mock_redis = MagicMock()

def pytest_configure(config):
    print("pytest_firestore_mock: pytest_configure hook started.")

    # 1. Set environment variables
    os.environ["SECRET_KEY"] = "testing-secret-key"
    os.environ["ALGORITHM"] = "HS256"
    os.environ["REDIS_HOST"] = "localhost"
    os.environ["REDIS_PORT"] = "6379"
    os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
    print(
        f"pytest_firestore_mock: Environment variables set. SECRET_KEY='{os.getenv('SECRET_KEY')}', ALGORITHM='{os.getenv('ALGORITHM')}'")

    # 2. Mock external modules in sys.modules
    sys.modules['google.cloud.firestore'] = MagicMock()
    sys.modules['google.cloud.firestore_v1'] = MagicMock()
    sys.modules['redis'] = MagicMock()
    print("pytest_firestore_mock: External modules (firestore, redis) mocked in sys.modules.")

    # 3. Import, reload, and patch core.security
    try:
        import core.security
        importlib.reload(core.security)  # Reload to ensure it picks up env vars if imported early
        print("pytest_firestore_mock: core.security imported and reloaded.")

        # Explicitly set attributes on the core.security module
        core.security.SECRET_KEY = os.getenv("SECRET_KEY")
        core.security.ALGORITHM = os.getenv("ALGORITHM")
        # Ensure ACCESS_TOKEN_EXPIRE_MINUTES is an int if your code expects that
        core.security.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        print(
            f"pytest_firestore_mock: core.security attributes forcibly set. SECRET_KEY='{core.security.SECRET_KEY}', ALGORITHM='{core.security.ALGORITHM}'")
    except ImportError:
        print(
            "pytest_firestore_mock: core.security module not found. Assuming it will pick up env vars on its first import.")
    except Exception as e:
        print(f"pytest_firestore_mock: Error during core.security handling: {e}")

    # 4. Monkeypatch jose.jwt.encode and jose.jwt.decode
    try:
        import jose.jwt

        # Check if already patched to prevent issues if pytest_configure is somehow called multiple times
        # (though it typically runs once per session for a plugin)
        if not hasattr(jose.jwt, '_original_encode_by_firestore_mock'):
            jose.jwt._original_encode_by_firestore_mock = jose.jwt.encode
            jose.jwt._original_decode_by_firestore_mock = jose.jwt.decode

            def patched_encode_for_tests(claims, key=None, algorithm=None, **kwargs):
                # Forcibly use the test key and algorithm for encoding
                # print(f"Patched jose.jwt.encode called. Original key: {key}, alg: {algorithm}. Overriding with test values.")
                return jose.jwt._original_encode_by_firestore_mock(claims, "testing-secret-key", algorithm="HS256",
                                                                   **kwargs)

            def patched_decode_for_tests(token, key=None, algorithms=None, **kwargs):
                # Forcibly use the test key and algorithm for decoding
                # print(f"Patched jose.jwt.decode called. Original key: {key}, algs: {algorithms}. Overriding with test values.")
                return jose.jwt._original_decode_by_firestore_mock(token, "testing-secret-key", algorithms=["HS256"],
                                                                   **kwargs)

            jose.jwt.encode = patched_encode_for_tests
            jose.jwt.decode = patched_decode_for_tests
            print("pytest_firestore_mock: jose.jwt.encode and jose.jwt.decode have been monkeypatched.")
        else:
            print(
                "pytest_firestore_mock: jose.jwt.encode and jose.jwt.decode appear to be already patched by this plugin.")

    except ImportError:
        print("pytest_firestore_mock: jose.jwt module not found. Cannot patch.")
    except Exception as e:
        print(f"pytest_firestore_mock: Error during jose.jwt patching: {e}")

    print("pytest_firestore_mock: pytest_configure hook finished.")