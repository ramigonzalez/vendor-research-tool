"""Tests for the regenerate-summary endpoint and supporting components (Story 14.1)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import (
    CapabilityLevel,
    JobStatus,
    MaturityLevel,
    Priority,
    Requirement,
    ResearchJob,
    ScoreResult,
    SummaryFormat,
    VendorRanking,
)
from app.prompts.synthesis import SUMMARY_FORMAT_PROMPTS, build_summary_context
from app.repository import SQLiteResearchRepository, create_db_and_tables, get_repository
from tests.conftest import MockResearchRepository

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _override_repo():
    """Override the repository dependency with a fresh mock for each test."""
    mock_repo = MockResearchRepository()
    app.dependency_overrides[get_repository] = lambda: mock_repo
    yield mock_repo
    app.dependency_overrides.clear()


@pytest.fixture()
def client():
    return TestClient(app)


def _make_job(job_id: str, status: JobStatus, **kwargs) -> ResearchJob:
    return ResearchJob(id=job_id, status=status, created_at=datetime.now(UTC), **kwargs)


def _make_score(score: float = 8.5) -> ScoreResult:
    return ScoreResult(
        score=score,
        confidence=0.85,
        capability_level=CapabilityLevel.full,
        maturity=MaturityLevel.ga,
        justification="Strong support",
        limitations=[],
        evidence=[],
    )


async def _setup_completed_job(repo: MockResearchRepository, job_id: str = "job-1") -> None:
    """Create a completed job with scores, rankings, and summary in the mock repo."""
    job = _make_job(job_id, JobStatus.running)
    await repo.create_job(job)
    await repo.save_score(job_id, "VendorA", "R1", _make_score(8.5))
    await repo.save_score(job_id, "VendorA", "R2", _make_score(7.0))
    await repo.save_score(job_id, "VendorB", "R1", _make_score(6.0))
    await repo.save_score(job_id, "VendorB", "R2", _make_score(9.0))
    await repo.save_final_results(
        job_id,
        summary="Original summary.",
        rankings=[
            VendorRanking(vendor="VendorA", overall_score=85.0, rank=1),
            VendorRanking(vendor="VendorB", overall_score=72.0, rank=2),
        ],
    )


# ---------------------------------------------------------------------------
# SummaryFormat enum tests
# ---------------------------------------------------------------------------


class TestSummaryFormatEnum:
    def test_enum_values(self):
        assert SummaryFormat.formal.value == "formal"
        assert SummaryFormat.informal.value == "informal"
        assert SummaryFormat.concise.value == "concise"
        assert SummaryFormat.direct.value == "direct"

    def test_enum_count(self):
        assert len(SummaryFormat) == 4

    def test_enum_is_str(self):
        assert isinstance(SummaryFormat.formal, str)


# ---------------------------------------------------------------------------
# Format prompt tests
# ---------------------------------------------------------------------------


class TestFormatPrompts:
    def test_all_formats_have_prompts(self):
        for fmt in SummaryFormat:
            assert fmt.value in SUMMARY_FORMAT_PROMPTS
            assert len(SUMMARY_FORMAT_PROMPTS[fmt.value]) > 0

    def test_formal_matches_original(self):
        from app.prompts.synthesis import SUMMARY_GENERATION_SYSTEM_PROMPT

        assert SUMMARY_FORMAT_PROMPTS["formal"] == SUMMARY_GENERATION_SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# build_summary_context tests
# ---------------------------------------------------------------------------


class TestBuildSummaryContext:
    def test_produces_expected_output(self):
        vendors = ["VendorA", "VendorB"]
        requirements = [
            Requirement(id="R1", description="Tracing support", priority=Priority.high),
        ]
        rankings = [
            VendorRanking(vendor="VendorA", overall_score=85.0, rank=1),
        ]
        scores = {
            "VendorA": {"R1": _make_score(8.5)},
        }
        result = build_summary_context(vendors, requirements, rankings, scores)
        assert "VendorA" in result
        assert "VendorB" in result
        assert "R1" in result
        assert "8.5" in result
        assert "Tracing support" in result

    def test_empty_inputs(self):
        result = build_summary_context([], [], [], {})
        assert "Evaluation Results:" in result


# ---------------------------------------------------------------------------
# update_summary repository tests
# ---------------------------------------------------------------------------


class TestUpdateSummaryRepo:
    @pytest.fixture
    async def repo(self, tmp_path: Path) -> SQLiteResearchRepository:
        db_path = tmp_path / "test.db"
        await create_db_and_tables(db_path)
        return SQLiteResearchRepository(str(db_path))

    async def test_updates_only_summary(self, repo: SQLiteResearchRepository):
        job = ResearchJob(id="job-1", status=JobStatus.pending, created_at=datetime(2026, 1, 15))
        await repo.create_job(job)
        await repo.save_final_results(
            "job-1",
            summary="Original",
            rankings=[VendorRanking(vendor="A", overall_score=80.0, rank=1)],
        )

        original_job = await repo.get_job("job-1")
        assert original_job is not None
        original_completed_at = original_job.completed_at

        await repo.update_summary("job-1", "New summary text")

        updated_job = await repo.get_job("job-1")
        assert updated_job is not None
        assert updated_job.status == JobStatus.completed  # unchanged
        assert updated_job.completed_at == original_completed_at  # unchanged

        results = await repo.get_results("job-1")
        assert results is not None
        assert results.summary == "New summary text"


# ---------------------------------------------------------------------------
# Endpoint tests
# ---------------------------------------------------------------------------


class TestRegenerateSummaryEndpoint:
    def test_404_for_missing_job(self, client: TestClient):
        response = client.post(
            "/api/research/nonexistent/regenerate-summary",
            json={"format": "formal"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Job not found"

    @pytest.mark.anyio()
    async def test_400_for_non_completed_job(self, _override_repo, client: TestClient):
        repo: MockResearchRepository = _override_repo
        await repo.create_job(_make_job("job-1", JobStatus.running))

        response = client.post(
            "/api/research/job-1/regenerate-summary",
            json={"format": "formal"},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Job is not completed"

    @pytest.mark.anyio()
    @patch("app.api.router.get_llm")
    async def test_200_with_valid_regeneration(self, mock_get_llm, _override_repo, client: TestClient):
        repo: MockResearchRepository = _override_repo
        await _setup_completed_job(repo, "job-1")

        mock_llm = AsyncMock()
        mock_result = MagicMock()
        mock_result.content = "Regenerated summary in formal format."
        mock_llm.ainvoke.return_value = mock_result
        mock_get_llm.return_value = mock_llm

        response = client.post(
            "/api/research/job-1/regenerate-summary",
            json={"format": "formal"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["summary"] == "Regenerated summary in formal format."

        # Verify summary was persisted
        assert repo._summaries["job-1"] == "Regenerated summary in formal format."

    @pytest.mark.anyio()
    @patch("app.api.router.get_llm")
    async def test_defaults_to_formal(self, mock_get_llm, _override_repo, client: TestClient):
        repo: MockResearchRepository = _override_repo
        await _setup_completed_job(repo, "job-1")

        mock_llm = AsyncMock()
        mock_result = MagicMock()
        mock_result.content = "Default formal summary."
        mock_llm.ainvoke.return_value = mock_result
        mock_get_llm.return_value = mock_llm

        response = client.post(
            "/api/research/job-1/regenerate-summary",
            json={},
        )
        assert response.status_code == 200
        assert response.json()["summary"] == "Default formal summary."

    @pytest.mark.anyio()
    @patch("app.api.router.get_llm")
    async def test_500_on_llm_error(self, mock_get_llm, _override_repo, client: TestClient):
        repo: MockResearchRepository = _override_repo
        await _setup_completed_job(repo, "job-1")

        mock_get_llm.side_effect = RuntimeError("LLM unavailable")

        response = client.post(
            "/api/research/job-1/regenerate-summary",
            json={"format": "concise"},
        )
        assert response.status_code == 500
        assert "LLM error" in response.json()["detail"]

    def test_invalid_format_returns_422(self, client: TestClient):
        response = client.post(
            "/api/research/some-id/regenerate-summary",
            json={"format": "invalid_format"},
        )
        assert response.status_code == 422
