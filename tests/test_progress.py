"""Tests for SSE progress event helpers."""

from __future__ import annotations

import asyncio
import json

import pytest

from app.graph.progress import (
    emit_completed,
    emit_error,
    emit_progress,
    emit_started,
    format_sse,
)


@pytest.fixture
def queue() -> asyncio.Queue:
    return asyncio.Queue()


def _state_with_queue(queue: asyncio.Queue) -> dict:
    return {"job_id": "job-1", "progress_queue": queue}


def _state_without_queue() -> dict:
    return {"job_id": "job-1"}


# --- emit_progress ---


async def test_emit_progress_puts_event(queue: asyncio.Queue) -> None:
    state = _state_with_queue(queue)
    await emit_progress(state, "research", 42, "Searching...")
    event = queue.get_nowait()
    assert event == {"type": "progress", "phase": "research", "pct": 42, "message": "Searching..."}


async def test_emit_progress_no_queue() -> None:
    state = _state_without_queue()
    await emit_progress(state, "research", 10, "msg")  # should not raise


# --- emit_started ---


async def test_emit_started_puts_event(queue: asyncio.Queue) -> None:
    state = _state_with_queue(queue)
    await emit_started(state)
    event = queue.get_nowait()
    assert event == {"type": "started", "job_id": "job-1"}


async def test_emit_started_no_queue() -> None:
    state = _state_without_queue()
    await emit_started(state)  # should not raise


# --- emit_completed ---


async def test_emit_completed_puts_event(queue: asyncio.Queue) -> None:
    state = _state_with_queue(queue)
    await emit_completed(state, {"vendors": 4})
    event = queue.get_nowait()
    assert event == {"type": "completed", "results": {"vendors": 4}}


async def test_emit_completed_no_queue() -> None:
    state = _state_without_queue()
    await emit_completed(state, {})  # should not raise


# --- emit_error ---


async def test_emit_error_puts_event(queue: asyncio.Queue) -> None:
    state = _state_with_queue(queue)
    await emit_error(state, "something broke")
    event = queue.get_nowait()
    assert event == {"type": "error", "message": "something broke"}


async def test_emit_error_no_queue() -> None:
    state = _state_without_queue()
    await emit_error(state, "err")  # should not raise


# --- format_sse ---


def test_format_sse_basic() -> None:
    result = format_sse({"type": "progress", "pct": 50})
    assert result == 'data: {"type": "progress", "pct": 50}\n\n'


def test_format_sse_roundtrip() -> None:
    event = {"type": "completed", "results": {"key": "value"}}
    sse = format_sse(event)
    assert sse.startswith("data: ")
    assert sse.endswith("\n\n")
    payload = json.loads(sse.removeprefix("data: ").strip())
    assert payload == event
