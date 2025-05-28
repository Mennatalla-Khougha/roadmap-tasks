# tests/conftest.py
import pytest
from unittest.mock import MagicMock
import sys

# Create mock objects
mock_firestore = MagicMock()
mock_redis = MagicMock()


# Patch the module before it's imported
@pytest.fixture(scope="session", autouse=True)
def patch_database():
    # This function needs to run before any tests are collected
    import builtins
    original_import = builtins.__import__

    def patched_import(name, *args, **kwargs):
        module = original_import(name, *args, **kwargs)

        # Patch database getters after importing but before they're used elsewhere
        if name == "core.database":
            module.get_db = lambda: mock_firestore
            module.get_redis = lambda: mock_redis

        return module

    builtins.__import__ = patched_import

    yield

    # Restore original import behavior
    builtins.__import__ = original_import


# Make the mocks available as fixtures too
@pytest.fixture
def mock_db():
    return mock_firestore


@pytest.fixture
def mock_redis():
    return mock_redis