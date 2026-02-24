"""Pytest fixtures for the Vendor Research Tool test suite."""

from __future__ import annotations

from typing import Any

import pytest


class MockResearchRepository:
    """Mock repository for testing.

    This is a minimal placeholder for Story 3.2 (Repository Pattern).
    The actual repository interface will be defined in that story.
    """

    def __init__(self) -> None:
        self._storage: dict[str, Any] = {}

    async def get(self, key: str) -> Any:
        return self._storage.get(key)

    async def save(self, key: str, value: Any) -> None:
        self._storage[key] = value


@pytest.fixture
def mock_repository() -> MockResearchRepository:
    """Provide a fresh mock repository for each test."""
    return MockResearchRepository()
