import pytest
from unittest.mock import MagicMock
mock_firestore = MagicMock()
# mock_redis = MagicMock()


@pytest.fixture(scope="session", autouse=True)
def patch_database():
    import builtins
    original_import = builtins.__import__

    def patched_import(name, *args, **kwargs):
        module = original_import(name, *args, **kwargs)
        if name == "core.database":
            module.get_db = lambda: mock_firestore
            module.get_redis = lambda: mock_redis
        return module
    builtins.__import__ = patched_import
    yield
    builtins.__import__ = original_import


@pytest.fixture
def mock_db():
    return mock_firestore


@pytest.fixture
def mock_redis():
    return mock_redis
