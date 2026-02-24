"""Tests for the research pipeline assembly and execution."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.graph.pipeline import build_research_graph, run_pipeline
from app.models import CapabilityLevel, Evidence, JobStatus, MaturityLevel, ScoreResult, SourceType, VendorRanking

from tests.conftest import MockResearchRepository


# --- build_research_graph ---


def test_build_research_graph_returns_state_graph() -> None:
    graph = build_research_graph()
    assert graph is not None


def test_build_research_graph_has_all_nodes() -> None:
    graph = build_research_graph()
    expected_nodes = {
        "generate_queries",
        "execute_searches",
        "extract_evidence",
        "prepare_gap_filling",
        "assess_capabilities",
        "compute_scores",
        "compute_rankings",
        "generate_summary",
    }
    assert expected_nodes.issubset(set(graph.nodes))


def test_build_research_graph_compiles() -> None:
    graph = build_research_graph()
    compiled = graph.compile()
    assert compiled is not None


def test_build_research_graph_entry_point() -> None:
    graph = build_research_graph()
    # The entry point is wired via __start__ -> generate_queries edge
    compiled = graph.compile()
    graph_dict = compiled.get_graph().to_json()
    assert graph_dict is not None


# --- run_pipeline ---


@pytest.fixture
def mock_repo() -> MockResearchRepository:
    return MockResearchRepository()


@pytest.fixture
def queue() -> asyncio.Queue:
    return asyncio.Queue()


def _base_state(queue: asyncio.Queue) -> dict:
    return {
        "job_id": "job-123",
        "vendors": ["VendorA"],
        "requirements": [],
        "progress_queue": queue,
    }


async def test_run_pipeline_success(mock_repo: MockResearchRepository, queue: asyncio.Queue) -> None:
    state = _base_state(queue)

    final = {
        **state,
        "summary": "VendorA is great",
        "rankings": [VendorRanking(vendor="VendorA", overall_score=0.9, rank=1, strengths=[], weaknesses=[])],
        "scores": {
            "VendorA": {
                "R1": ScoreResult(
                    score=8,
                    confidence=0.9,
                    capability_level=CapabilityLevel.full,
                    maturity=MaturityLevel.ga,
                    justification="solid",
                    limitations=[],
                    evidence=[],
                ),
            },
        },
        "evidence": {},
    }

    mock_compiled = AsyncMock()
    mock_compiled.ainvoke.return_value = final

    with patch("app.graph.pipeline.build_research_graph") as mock_build:
        mock_graph = MagicMock()
        mock_graph.compile.return_value = mock_compiled
        mock_build.return_value = mock_graph

        result = await run_pipeline(state, mock_repo)

    assert result["summary"] == "VendorA is great"
    assert mock_compiled.ainvoke.await_count == 1

    # Verify repo persistence
    assert mock_repo._summaries.get("job-123") == "VendorA is great"
    assert len(mock_repo._rankings.get("job-123", [])) == 1
    assert len(mock_repo._scores.get("job-123", [])) == 1


async def test_run_pipeline_persists_evidence(mock_repo: MockResearchRepository, queue: asyncio.Queue) -> None:
    state = _base_state(queue)

    ev = Evidence(
        claim="Supports tracing",
        source_url="https://example.com",
        source_name="Example Docs",
        source_type=SourceType.official_docs,
        relevance=0.8,
        supports_requirement=True,
    )
    final = {
        **state,
        "summary": "",
        "rankings": [],
        "scores": {},
        "evidence": {"VendorA": {"R1": [ev]}},
    }

    mock_compiled = AsyncMock()
    mock_compiled.ainvoke.return_value = final

    with patch("app.graph.pipeline.build_research_graph") as mock_build:
        mock_graph = MagicMock()
        mock_graph.compile.return_value = mock_compiled
        mock_build.return_value = mock_graph

        await run_pipeline(state, mock_repo)

    saved = mock_repo._evidence.get("job-123", [])
    assert len(saved) == 1
    assert saved[0][0] == "VendorA"
    assert saved[0][1] == "R1"


async def test_run_pipeline_emits_progress_and_completed(mock_repo: MockResearchRepository, queue: asyncio.Queue) -> None:
    state = _base_state(queue)

    final = {**state, "summary": "", "rankings": [], "scores": {}, "evidence": {}}

    mock_compiled = AsyncMock()
    mock_compiled.ainvoke.return_value = final

    with patch("app.graph.pipeline.build_research_graph") as mock_build:
        mock_graph = MagicMock()
        mock_graph.compile.return_value = mock_compiled
        mock_build.return_value = mock_graph

        await run_pipeline(state, mock_repo)

    events = []
    while not queue.empty():
        events.append(queue.get_nowait())

    types = [e["type"] for e in events]
    assert "progress" in types
    assert "completed" in types


async def test_run_pipeline_failure_emits_error_and_raises(mock_repo: MockResearchRepository, queue: asyncio.Queue) -> None:
    from app.models import ResearchJob
    # Pre-create the job so update_job_status works
    from datetime import UTC, datetime
    job = ResearchJob(id="job-123", status=JobStatus.running, created_at=datetime.now(UTC), progress_pct=0)
    await mock_repo.create_job(job)

    state = _base_state(queue)

    mock_compiled = AsyncMock()
    mock_compiled.ainvoke.side_effect = RuntimeError("LLM timeout")

    with patch("app.graph.pipeline.build_research_graph") as mock_build:
        mock_graph = MagicMock()
        mock_graph.compile.return_value = mock_compiled
        mock_build.return_value = mock_graph

        with pytest.raises(RuntimeError, match="LLM timeout"):
            await run_pipeline(state, mock_repo)

    # Verify error event emitted
    events = []
    while not queue.empty():
        events.append(queue.get_nowait())
    error_events = [e for e in events if e["type"] == "error"]
    assert len(error_events) == 1
    assert "LLM timeout" in error_events[0]["message"]

    # Verify job status set to failed
    updated_job = await mock_repo.get_job("job-123")
    assert updated_job is not None
    assert updated_job.status == JobStatus.failed


async def test_run_pipeline_no_queue_still_works(mock_repo: MockResearchRepository) -> None:
    state = {"job_id": "job-456", "vendors": ["VendorA"], "requirements": []}

    final = {**state, "summary": "done", "rankings": [], "scores": {}, "evidence": {}}

    mock_compiled = AsyncMock()
    mock_compiled.ainvoke.return_value = final

    with patch("app.graph.pipeline.build_research_graph") as mock_build:
        mock_graph = MagicMock()
        mock_graph.compile.return_value = mock_compiled
        mock_build.return_value = mock_graph

        result = await run_pipeline(state, mock_repo)

    assert result["summary"] == "done"
