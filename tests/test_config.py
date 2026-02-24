"""Tests for app.config module."""

from app.models import Priority, Requirement


def test_priority_weights_defined() -> None:
    """PRIORITY_WEIGHTS maps all priority levels to floats."""
    from app.config import PRIORITY_WEIGHTS

    assert PRIORITY_WEIGHTS["high"] == 3.0
    assert PRIORITY_WEIGHTS["medium"] == 2.0
    assert PRIORITY_WEIGHTS["low"] == 1.0


def test_vendors_list() -> None:
    """VENDORS contains the four expected vendors."""
    from app.config import VENDORS

    assert VENDORS == ["LangSmith", "Langfuse", "Braintrust", "PostHog"]


def test_requirements_list() -> None:
    """REQUIREMENTS contains 6 requirements with correct priorities."""
    from app.config import REQUIREMENTS

    assert len(REQUIREMENTS) == 6
    assert all(isinstance(r, Requirement) for r in REQUIREMENTS)
    high_count = sum(1 for r in REQUIREMENTS if r.priority == Priority.high)
    medium_count = sum(1 for r in REQUIREMENTS if r.priority == Priority.medium)
    low_count = sum(1 for r in REQUIREMENTS if r.priority == Priority.low)
    assert high_count == 2
    assert medium_count == 2
    assert low_count == 2
