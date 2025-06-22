# pytest_firestore_mock.py
from unittest.mock import MagicMock
import os
import sys
import importlib
import core.security


def pytest_configure(config):
    # 1. Set environment variables
    os.environ["SECRET_KEY"] = "testing-secret-key"
    os.environ["ALGORITHM"] = "HS256"
    os.environ["REDIS_HOST"] = "localhost"
    os.environ["REDIS_PORT"] = "6379"
    os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

    # 2. Mock external modules in sys.modules
    sys.modules['google.cloud.firestore'] = MagicMock()
    sys.modules['google.cloud.firestore_v1'] = MagicMock()
    sys.modules['redis'] = MagicMock()

    # 3. Import, reload, and patch core.security
    try:
        importlib.reload(core.security)

        # Explicitly set attributes on the core.security module
        core.security.SECRET_KEY = os.getenv("SECRET_KEY")
        core.security.ALGORITHM = os.getenv("ALGORITHM")
        core.security.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv(
            "ACCESS_TOKEN_EXPIRE_MINUTES", "30"
        ))
    except ImportError:
        print(
            "pytest_firestore_mock: "
            "core.security module not found. "
            "Assuming it will pick up env vars on its first import."
        )
    except Exception as e:
        print(
            f"pytest_firestore_mock: Error during core.security handling: {e}"
        )

    # 4. Monkeypatch jose.jwt.encode and jose.jwt.decode
    try:
        import jose.jwt

        if not hasattr(jose.jwt, '_original_encode_by_firestore_mock'):
            jose.jwt._original_encode_by_firestore_mock = jose.jwt.encode
            jose.jwt._original_decode_by_firestore_mock = jose.jwt.decode

            def patched_encode_for_tests(claims, key_from_call_site, **kwargs):
                kwargs_for_original = {k: v for k,
                                       v in kwargs.items() if k != 'algorithm'}

                return jose.jwt._original_encode_by_firestore_mock(
                    claims,
                    "testing-secret-key",  # Force key
                    algorithm="HS256",  # Force algorithm
                    **kwargs_for_original  # Pass other kwargs
                )

            def patched_decode_for_tests(
                    token, key=None, algorithms=None, **kwargs
            ):
                effective_key = "testing-secret-key" if key is None else key
                effective_algorithms = ["HS256"] if (
                    algorithms is None or algorithms == [None]
                ) else algorithms

                return jose.jwt._original_decode_by_firestore_mock(
                    token, effective_key,
                    algorithms=effective_algorithms, **kwargs
                )

            jose.jwt.encode = patched_encode_for_tests
            jose.jwt.decode = patched_decode_for_tests
            print(
                "pytest_firestore_mock:"
                " jose.jwt.encode and jose.jwt.decode have been monkeypatched."
            )
        else:
            print(
                "pytest_firestore_mock: "
                "jose.jwt.encode and jose."
                "jwt.decode appear to be already patched by this plugin."
            )

    except ImportError:
        print(
            "pytest_firestore_mock: jose.jwt module not found. Cannot patch."
        )
    except Exception as e:
        print(f"pytest_firestore_mock: Error during jose.jwt patching: {e}")

    print("pytest_firestore_mock: pytest_configure hook finished.")
