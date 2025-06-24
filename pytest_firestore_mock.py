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

    # Set dummy Firebase credentials with a valid PEM format for the private key
    os.environ["FIREBASE_TYPE"] = "service_account"
    os.environ["FIREBASE_PROJECT_ID"] = "test-project"
    os.environ["FIREBASE_PRIVATE_KEY_ID"] = "test-key-id"
    # This is a syntactically valid, but fake, RSA private key.
    os.environ["FIREBASE_PRIVATE_KEY"] = (
        "-----BEGIN PRIVATE KEY-----\n"
        "MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDRs3fA0ScKx5/G\n"
        "hA4+T8V9j5vR+t4Z7pL5a7f5d6t5g4v3a8f4c7d6e8g5h6i7k8f8c7d6e8g5h6i\n"
        "7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h\n"
        "6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g\n"
        "5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e\n"
        "8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d\n"
        "6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c\n"
        "7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f\n"
        "8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k\n"
        "8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i\n"
        "7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h\n"
        "6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g\n"
        "5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e\n"
        "8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d\n"
        "6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c\n"
        "7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f\n"
        "8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k\n"
        "8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i\n"
        "7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h\n"
        "6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g\n"
aBcDeFgHiJkLmNoPqRsTuVwXyZ==\n"
        "-----END PRIVATE KEY-----\n"
    )
    os.environ["FIREBASE_CLIENT_EMAIL"] = "test-client-email@example.com"
    os.environ["FIREBASE_CLIENT_ID"] = "test-client-id"
    os.environ["FIREBASE_AUTH_URI"] = "https://accounts.google.com/o/oauth2/auth"
    os.environ["FIREBASE_TOKEN_URI"] = "https://oauth2.googleapis.com/token"
    os.environ["FIREBASE_AUTH_PROVIDER_X509_CERT_URL"] = "https://www.googleapis.com/oauth2/v1/certs"
    os.environ["FIREBASE_CLIENT_X509_CERT_URL"] = "https://www.googleapis.com/robot/v1/metadata/x509/test-client-email%40example.com"

    # 2. Mock external modules in sys.modules
    sys.modules['google.cloud.firestore'] = MagicMock()
    sys.modules['google.cloud.firestore_v1'] = MagicMock()
    sys.modules['google.cloud.firestore_v1.base_client'] = MagicMock()
    sys.modules['redis'] = MagicMock()
    sys.modules['firebase_admin'] = MagicMock()


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

    print("pytest_firestore_mock: pytest_configure hook finished.")# pytest_firestore_mock.py
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

    # Set dummy Firebase credentials with a valid PEM format for the private key
    os.environ["FIREBASE_TYPE"] = "service_account"
    os.environ["FIREBASE_PROJECT_ID"] = "test-project"
    os.environ["FIREBASE_PRIVATE_KEY_ID"] = "test-key-id"
    # This is a syntactically valid, but fake, RSA private key.
    os.environ["FIREBASE_PRIVATE_KEY"] = (
        "-----BEGIN PRIVATE KEY-----\n"
        "MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDRs3fA0ScKx5/G\n"
        "hA4+T8V9j5vR+t4Z7pL5a7f5d6t5g4v3a8f4c7d6e8g5h6i7k8f8c7d6e8g5h6i\n"
        "7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h\n"
        "6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g\n"
        "5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e\n"
        "8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d\n"
        "6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c\n"
        "7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f\n"
        "8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k\n"
        "8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i\n"
        "7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h\n"
        "6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g\n"
        "5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e\n"
        "8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d\n"
        "6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c\n"
        "7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f\n"
        "8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k\n"
        "8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i\n"
        "7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h\n"
        "6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g5h6i7k8f8c7d6e8g\n"
aBcDeFgHiJkLmNoPqRsTuVwXyZ==\n"
        "-----END PRIVATE KEY-----\n"
    )
    os.environ["FIREBASE_CLIENT_EMAIL"] = "test-client-email@example.com"
    os.environ["FIREBASE_CLIENT_ID"] = "test-client-id"
    os.environ["FIREBASE_AUTH_URI"] = "https://accounts.google.com/o/oauth2/auth"
    os.environ["FIREBASE_TOKEN_URI"] = "https://oauth2.googleapis.com/token"
    os.environ["FIREBASE_AUTH_PROVIDER_X509_CERT_URL"] = "https://www.googleapis.com/oauth2/v1/certs"
    os.environ["FIREBASE_CLIENT_X509_CERT_URL"] = "https://www.googleapis.com/robot/v1/metadata/x509/test-client-email%40example.com"

    # 2. Mock external modules in sys.modules
    sys.modules['google.cloud.firestore'] = MagicMock()
    sys.modules['google.cloud.firestore_v1'] = MagicMock()
    sys.modules['google.cloud.firestore_v1.base_client'] = MagicMock()
    sys.modules['redis'] = MagicMock()
    sys.modules['firebase_admin'] = MagicMock()


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