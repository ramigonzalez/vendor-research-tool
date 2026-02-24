"""Centralized logging configuration for the Vendor Research Tool."""

from __future__ import annotations

import logging
import sys

from app.config import settings


def setup_logging() -> None:
    """Configure the root logger based on LOG_LEVEL and LOG_FORMAT settings.

    Call once at application startup before any other logging.
    """
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    fmt = settings.LOG_FORMAT.lower()

    root = logging.getLogger()
    root.setLevel(level)

    # Remove any existing handlers to avoid duplicates on reload
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)

    if fmt == "json":
        from pythonjsonlogger.json import JsonFormatter

        formatter = JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger"},
        )
    else:
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    handler.setFormatter(formatter)
    root.addHandler(handler)

    # Quiet noisy third-party loggers
    for name in ("uvicorn.access", "httpx", "httpcore"):
        logging.getLogger(name).setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info("Logging configured level=%s format=%s", settings.LOG_LEVEL.upper(), fmt)
