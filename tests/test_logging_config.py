"""Tests for centralized logging configuration."""

from __future__ import annotations

import json
import logging
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _reset_root_logger():
    """Reset root logger state before and after each test."""
    root = logging.getLogger()
    original_handlers = root.handlers[:]
    original_level = root.level
    yield
    root.handlers = original_handlers
    root.setLevel(original_level)


def _make_settings(**overrides):
    """Create a mock settings object with defaults."""
    defaults = {"LOG_LEVEL": "INFO", "LOG_FORMAT": "text"}
    defaults.update(overrides)

    class FakeSettings:
        pass

    s = FakeSettings()
    for k, v in defaults.items():
        setattr(s, k, v)
    return s


def test_setup_logging_text_format():
    """setup_logging() with text format configures a Formatter on root."""
    with patch("app.logging_config.settings", _make_settings(LOG_FORMAT="text")):
        from app.logging_config import setup_logging

        setup_logging()

    root = logging.getLogger()
    assert root.level == logging.INFO
    assert len(root.handlers) == 1
    fmt = root.handlers[0].formatter
    assert fmt is not None
    assert "[%(levelname)s]" in fmt._fmt


def test_setup_logging_json_format():
    """setup_logging() with json format uses JsonFormatter."""
    with patch("app.logging_config.settings", _make_settings(LOG_FORMAT="json")):
        from app.logging_config import setup_logging

        setup_logging()

    root = logging.getLogger()
    assert len(root.handlers) == 1
    handler = root.handlers[0]
    # Verify JSON output by formatting a record
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg="hello", args=(), exc_info=None,
    )
    output = handler.formatter.format(record)
    parsed = json.loads(output)
    assert parsed["message"] == "hello"
    assert parsed["level"] == "INFO"


def test_setup_logging_respects_log_level():
    """LOG_LEVEL=DEBUG sets root logger to DEBUG."""
    with patch("app.logging_config.settings", _make_settings(LOG_LEVEL="DEBUG")):
        from app.logging_config import setup_logging

        setup_logging()

    root = logging.getLogger()
    assert root.level == logging.DEBUG


def test_setup_logging_quiets_third_party():
    """Third-party loggers are set to WARNING."""
    with patch("app.logging_config.settings", _make_settings()):
        from app.logging_config import setup_logging

        setup_logging()

    for name in ("uvicorn.access", "httpx", "httpcore"):
        assert logging.getLogger(name).level == logging.WARNING
