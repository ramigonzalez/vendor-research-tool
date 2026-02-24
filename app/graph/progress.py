"""SSE progress event helpers for the research pipeline."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.graph.state import ResearchState


async def emit_progress(state: ResearchState, phase: str, pct: int, message: str) -> None:
    """Put a progress event onto the state's progress queue.

    Silently returns if ``progress_queue`` is missing from *state*.
    """
    queue = state.get("progress_queue")  # type: ignore[attr-defined]
    if queue is None:
        return
    await queue.put({"type": "progress", "phase": phase, "pct": pct, "message": message})


async def emit_started(state: ResearchState) -> None:
    """Put a started event onto the state's progress queue.

    Silently returns if ``progress_queue`` is missing from *state*.
    """
    queue = state.get("progress_queue")  # type: ignore[attr-defined]
    if queue is None:
        return
    await queue.put({"type": "started", "job_id": state.get("job_id", "")})


async def emit_completed(state: ResearchState, results: dict[str, Any]) -> None:
    """Put a completed event onto the state's progress queue.

    Silently returns if ``progress_queue`` is missing from *state*.
    """
    queue = state.get("progress_queue")  # type: ignore[attr-defined]
    if queue is None:
        return
    await queue.put({"type": "completed", "results": results})


async def emit_error(state: ResearchState, message: str) -> None:
    """Put an error event onto the state's progress queue.

    Silently returns if ``progress_queue`` is missing from *state*.
    """
    queue = state.get("progress_queue")  # type: ignore[attr-defined]
    if queue is None:
        return
    await queue.put({"type": "error", "message": message})


def format_sse(event: dict[str, Any]) -> str:
    """Format an event dict as an SSE data line with double newline."""
    return f"data: {json.dumps(event)}\n\n"
