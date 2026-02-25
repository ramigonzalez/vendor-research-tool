"""SSE progress event helpers for the research pipeline."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.graph.state import ResearchState


def _get_queue(state: ResearchState):
    """Extract the progress queue from state, or None."""
    return state.get("progress_queue")  # type: ignore[attr-defined]


async def _emit(state: ResearchState, event: dict[str, Any]) -> None:
    """Put an event onto the state's progress queue and persist as audit event."""
    queue = _get_queue(state)
    if queue is not None:
        await queue.put(event)

    audit_callback = state.get("audit_callback")  # type: ignore[attr-defined]
    if audit_callback is not None:
        try:
            await audit_callback(event.get("type", "unknown"), event)
        except Exception:
            pass  # Don't let audit persistence failures break the pipeline


# --- Original event types (backward-compatible) ---


async def emit_progress(state: ResearchState, phase: str, pct: int, message: str) -> None:
    """Put a progress event onto the state's progress queue."""
    await _emit(state, {"type": "progress", "phase": phase, "pct": pct, "message": message})


async def emit_started(state: ResearchState) -> None:
    """Put a started event onto the state's progress queue."""
    await _emit(state, {"type": "started", "job_id": state.get("job_id", "")})


async def emit_completed(state: ResearchState, results: dict[str, Any]) -> None:
    """Put a completed event onto the state's progress queue."""
    await _emit(state, {"type": "completed", "results": results})


async def emit_error(state: ResearchState, message: str) -> None:
    """Put an error event onto the state's progress queue."""
    await _emit(state, {"type": "error", "message": message})


# --- New granular event types (Story 8.1) ---


async def emit_phase_start(state: ResearchState, phase: str) -> None:
    """Emit when a pipeline phase begins."""
    await _emit(state, {
        "type": "phase_start",
        "phase": phase,
        "timestamp": datetime.now(UTC).isoformat(),
    })


async def emit_phase_end(state: ResearchState, phase: str) -> None:
    """Emit when a pipeline phase completes."""
    await _emit(state, {
        "type": "phase_end",
        "phase": phase,
        "timestamp": datetime.now(UTC).isoformat(),
    })


async def emit_query_generated(
    state: ResearchState, vendor: str, requirement_id: str, queries: list[str]
) -> None:
    """Emit when queries are generated for a vendor-requirement pair."""
    await _emit(state, {
        "type": "query_generated",
        "vendor": vendor,
        "requirement_id": requirement_id,
        "queries": queries,
    })


async def emit_search_result(
    state: ResearchState, vendor: str, requirement_id: str,
    source_url: str, source_name: str, domain: str,
) -> None:
    """Emit when a search result is found."""
    await _emit(state, {
        "type": "search_result",
        "vendor": vendor,
        "requirement_id": requirement_id,
        "source_url": source_url,
        "source_name": source_name,
        "domain": domain,
    })


async def emit_evidence_extracted(
    state: ResearchState, vendor: str, requirement_id: str,
    count: int, claims: list[str],
) -> None:
    """Emit when evidence is extracted for a vendor-requirement pair."""
    await _emit(state, {
        "type": "evidence_extracted",
        "vendor": vendor,
        "requirement_id": requirement_id,
        "count": count,
        "claims": claims[:3],  # Limit to first 3 for brevity
    })


async def emit_score_computed(
    state: ResearchState, vendor: str, requirement_id: str,
    score: float, confidence: float,
) -> None:
    """Emit when a score is computed for a vendor-requirement pair."""
    await _emit(state, {
        "type": "score_computed",
        "vendor": vendor,
        "requirement_id": requirement_id,
        "score": round(score, 2),
        "confidence": round(confidence, 2),
    })


async def emit_vendor_ranked(
    state: ResearchState, vendor: str, rank: int, overall_score: float,
) -> None:
    """Emit when a vendor is ranked."""
    await _emit(state, {
        "type": "vendor_ranked",
        "vendor": vendor,
        "rank": rank,
        "overall_score": round(overall_score, 2),
    })


async def emit_warning(
    state: ResearchState, vendor: str, requirement_id: str, message: str,
) -> None:
    """Emit a warning (e.g. extraction failure)."""
    await _emit(state, {
        "type": "warning",
        "vendor": vendor,
        "requirement_id": requirement_id,
        "message": message,
    })


async def emit_iteration_start(
    state: ResearchState, iteration: int, total_searches: int, gap_count: int,
) -> None:
    """Emit when a gap-filling iteration starts."""
    await _emit(state, {
        "type": "iteration_start",
        "iteration": iteration,
        "total_searches": total_searches,
        "gap_count": gap_count,
    })


def format_sse(event: dict[str, Any]) -> str:
    """Format an event dict as an SSE data line with double newline."""
    return f"data: {json.dumps(event)}\n\n"
