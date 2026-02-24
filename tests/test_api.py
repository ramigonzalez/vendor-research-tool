"""Tests for the GET /api/research/{job_id} endpoint."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import (
    CapabilityLevel,
    Evidence,
    JobStatus,
    MaturityLevel,
    ResearchJob,
    ScoreResult,
    SourceType,
    VendorRanking,
)
from app.repository import get_repository
from tests.conftest import MockResearchRepository


@pytest.fixture(autouse=True)
def _override_repo():
    """Override the repository dependency with a fresh mock for each test."""
    mock_repo = MockResearchRepository()
    app.dependency_overrides[get_repository] = lambda: mock_repo
    yield mock_repo
    app.dependency_overrides.clear()


@pytest.fixture()
def client():
    """Provide a TestClient instance."""
    return TestClient(app)


def _make_job(job_id: str, status: JobStatus, **kwargs) -> ResearchJob:
    """Helper to create a ResearchJob with sensible defaults."""
    return ResearchJob(
        id=job_id,
        status=status,
        created_at=datetime.now(UTC),
        **kwargs,
    )


class TestGetResearchResults:
    """Tests for GET /api/research/{job_id}."""

    def test_unknown_job_returns_404(self, client: TestClient):
        response = client.get("/api/research/nonexistent-id")
        assert response.status_code == 404
        assert response.json()["detail"] == "Job not found"

    @pytest.mark.anyio()
    async def test_running_job_returns_progress(self, _override_repo, client: TestClient):
        repo: MockResearchRepository = _override_repo
        job = _make_job("run-1", JobStatus.running, progress_pct=42, progress_message="Searching...")
        await repo.create_job(job)

        response = client.get("/api/research/run-1")
        assert response.status_code == 200
        data = response.json()
        assert data == {"status": "running", "progress_pct": 42}

    @pytest.mark.anyio()
    async def test_pending_job_returns_pending(self, _override_repo, client: TestClient):
        repo: MockResearchRepository = _override_repo
        job = _make_job("pend-1", JobStatus.pending)
        await repo.create_job(job)

        response = client.get("/api/research/pend-1")
        assert response.status_code == 200
        data = response.json()
        assert data == {"status": "pending", "progress_pct": 0}

    @pytest.mark.anyio()
    async def test_failed_job_returns_error(self, _override_repo, client: TestClient):
        repo: MockResearchRepository = _override_repo
        job = _make_job("fail-1", JobStatus.failed, progress_message="LLM rate limit exceeded")
        await repo.create_job(job)

        response = client.get("/api/research/fail-1")
        assert response.status_code == 200
        data = response.json()
        assert data == {"status": "failed", "error": "LLM rate limit exceeded"}

    @pytest.mark.anyio()
    async def test_completed_job_returns_full_results(self, _override_repo, client: TestClient):
        repo: MockResearchRepository = _override_repo
        job = _make_job("done-1", JobStatus.running)
        await repo.create_job(job)

        # Save a score and evidence
        evidence = Evidence(
            claim="Vendor A supports REST APIs",
            source_url="https://example.com/docs",
            source_name="Official Docs",
            source_type=SourceType.official_docs,
            relevance=0.9,
            supports_requirement=True,
        )
        score = ScoreResult(
            score=8.5,
            confidence=0.85,
            capability_level=CapabilityLevel.full,
            maturity=MaturityLevel.ga,
            justification="Strong REST API support",
            limitations=[],
            evidence=[],
        )
        await repo.save_evidence("done-1", "VendorA", "req-1", [evidence])
        await repo.save_score("done-1", "VendorA", "req-1", score)
        await repo.save_final_results(
            "done-1",
            summary="VendorA is the top choice.",
            rankings=[VendorRanking(vendor="VendorA", overall_score=85.0, rank=1)],
        )

        response = client.get("/api/research/done-1")
        assert response.status_code == 200
        data = response.json()

        # Verify top-level structure
        assert data["summary"] == "VendorA is the top choice."
        assert data["vendors"] == ["VendorA"]
        assert len(data["requirements"]) == 1
        assert data["requirements"][0]["id"] == "req-1"
        assert len(data["rankings"]) == 1
        assert data["rankings"][0]["vendor"] == "VendorA"
        assert data["rankings"][0]["rank"] == 1

        # Verify matrix structure
        assert "VendorA" in data["matrix"]
        assert "req-1" in data["matrix"]["VendorA"]
        vendor_score = data["matrix"]["VendorA"]["req-1"]
        assert vendor_score["score"] == 8.5
        assert vendor_score["confidence"] == 0.85
        assert vendor_score["capability_level"] == "full"
        assert len(vendor_score["evidence"]) == 1
        assert vendor_score["evidence"][0]["claim"] == "Vendor A supports REST APIs"


class TestListJobs:
    """Tests for GET /api/jobs."""

    def test_empty_repo_returns_empty_list(self, client: TestClient):
        response = client.get("/api/jobs")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.anyio()
    async def test_jobs_returned_when_repo_has_jobs(self, _override_repo, client: TestClient):
        repo: MockResearchRepository = _override_repo
        job1 = _make_job("job-1", JobStatus.pending)
        job2 = _make_job("job-2", JobStatus.running, progress_pct=50)
        await repo.create_job(job1)
        await repo.create_job(job2)

        response = client.get("/api/jobs")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        ids = [j["id"] for j in data]
        assert "job-1" in ids
        assert "job-2" in ids

    def test_response_is_json_array(self, client: TestClient):
        response = client.get("/api/jobs")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
