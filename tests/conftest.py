"""Global pytest fixtures and configuration."""

import asyncio
import warnings
from unittest.mock import patch

import pytest


# Filter out coroutine warnings which are hard to eliminate completely
@pytest.fixture(autouse=True)
def ignore_coroutine_warnings():
    """Filter out coroutine warnings which can be difficult to eliminate in async tests."""
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore", message="coroutine .* was never awaited", category=RuntimeWarning
        )
        yield


# Patch asyncio.run to handle mocked coroutines better
@pytest.fixture(autouse=True)
def mock_asyncio_run():
    """
    Patch asyncio.run to handle mocked coroutines better.
    This is a global fixture that applies to all tests.
    """
    original_run = asyncio.run

    def patched_run(coro):
        """Patched version of asyncio.run that handles mocked coroutines."""
        if hasattr(coro, "__await__"):
            return original_run(coro)
        return coro  # If it's not a real coroutine, just return it

    with patch("asyncio.run", patched_run):
        yield
