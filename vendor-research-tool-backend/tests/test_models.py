"""Tests for Pydantic domain models."""

import asyncio
from datetime import datetime, timezone

import pytest

from app.models import (
    CapabilityLevel,
    Evidence,
    JobStatus,
    LLMAssessment,
    MaturityLevel,
    Priority,
    Requirement,
    ResearchJob,
    ResearchResults,
    ScoreResult,
    SourceType,
    VendorRanking,
)


# --- Enum Tests ---


class TestSourceType:
    def test_all_values(self) -> None:
        assert SourceType.official_docs == "official_docs"
        assert SourceType.github == "github"
        assert SourceType.comparison == "comparison"
        assert SourceType.blog == "blog"
        assert SourceType.community == "community"

    def test_enum_count(self) -> None:
        assert len(SourceType) == 5


class TestCapabilityLevel:
    def test_all_values(self) -> None:
        assert CapabilityLevel.full == "full"
        assert CapabilityLevel.partial == "partial"
        assert CapabilityLevel.minimal == "minimal"
        assert CapabilityLevel.none == "none"
        assert CapabilityLevel.unknown == "unknown"

    def test_enum_count(self) -> None:
        assert len(CapabilityLevel) == 5


class TestMaturityLevel:
    def test_all_values(self) -> None:
        assert MaturityLevel.ga == "ga"
        assert MaturityLevel.beta == "beta"
        assert MaturityLevel.experimental == "experimental"
        assert MaturityLevel.planned == "planned"
        assert MaturityLevel.unknown == "unknown"

    def test_enum_count(self) -> None:
        assert len(MaturityLevel) == 5


class TestJobStatus:
    def test_all_values(self) -> None:
        assert JobStatus.pending == "pending"
        assert JobStatus.running == "running"
        assert JobStatus.completed == "completed"
        assert JobStatus.failed == "failed"

    def test_enum_count(self) -> None:
        assert len(JobStatus) == 4


class TestPriority:
    def test_all_values(self) -> None:
        assert Priority.high == "high"
        assert Priority.medium == "medium"
        assert Priority.low == "low"

    def test_enum_count(self) -> None:
        assert len(Priority) == 3


# --- Model Tests ---


def _make_evidence(**overrides) -> Evidence:  # type: ignore[no-untyped-def]
    defaults = {
        "claim": "Supports REST API",
        "source_url": "https://example.com/docs",
        "source_name": "Official Docs",
        "source_type": SourceType.official_docs,
        "relevance": 0.85,
        "supports_requirement": True,
    }
    defaults.update(overrides)
    return Evidence(**defaults)


def _make_score_result(**overrides) -> ScoreResult:  # type: ignore[no-untyped-def]
    defaults = {
        "score": 8.5,
        "confidence": 0.9,
        "capability_level": CapabilityLevel.full,
        "maturity": MaturityLevel.ga,
        "justification": "Strong REST API support with comprehensive docs.",
        "limitations": [],
        "evidence": [_make_evidence()],
    }
    defaults.update(overrides)
    return ScoreResult(**defaults)


class TestEvidence:
    def test_valid_creation(self) -> None:
        e = _make_evidence()
        assert e.claim == "Supports REST API"
        assert e.source_type == SourceType.official_docs
        assert e.relevance == 0.85
        assert e.content_date is None

    def test_with_content_date(self) -> None:
        e = _make_evidence(content_date="2025-01-15")
        assert e.content_date == "2025-01-15"

    def test_relevance_clamped_above_1(self) -> None:
        e = _make_evidence(relevance=1.5)
        assert e.relevance == 1.0

    def test_relevance_clamped_below_0(self) -> None:
        e = _make_evidence(relevance=-0.3)
        assert e.relevance == 0.0

    def test_relevance_at_boundaries(self) -> None:
        assert _make_evidence(relevance=0.0).relevance == 0.0
        assert _make_evidence(relevance=1.0).relevance == 1.0

    def test_serialization(self) -> None:
        e = _make_evidence()
        data = e.model_dump()
        assert data["source_type"] == "official_docs"
        assert isinstance(data["relevance"], float)


class TestLLMAssessment:
    def test_valid_creation(self) -> None:
        a = LLMAssessment(
            capability_level=CapabilityLevel.partial,
            capability_details="Supports basic operations only.",
            maturity=MaturityLevel.beta,
            limitations=["No streaming support"],
            supports_requirement=True,
        )
        assert a.capability_level == CapabilityLevel.partial
        assert len(a.limitations) == 1

    def test_empty_limitations(self) -> None:
        a = LLMAssessment(
            capability_level=CapabilityLevel.full,
            capability_details="Full support.",
            maturity=MaturityLevel.ga,
            limitations=[],
            supports_requirement=True,
        )
        assert a.limitations == []


class TestScoreResult:
    def test_valid_creation(self) -> None:
        sr = _make_score_result()
        assert sr.score == 8.5
        assert sr.confidence == 0.9
        assert len(sr.evidence) == 1

    def test_score_clamped_above_10(self) -> None:
        sr = _make_score_result(score=15.0)
        assert sr.score == 10.0

    def test_score_clamped_below_0(self) -> None:
        sr = _make_score_result(score=-2.0)
        assert sr.score == 0.0

    def test_confidence_clamped_above_1(self) -> None:
        sr = _make_score_result(confidence=1.5)
        assert sr.confidence == 1.0

    def test_confidence_clamped_below_0(self) -> None:
        sr = _make_score_result(confidence=-0.1)
        assert sr.confidence == 0.0

    def test_score_at_boundaries(self) -> None:
        assert _make_score_result(score=0.0).score == 0.0
        assert _make_score_result(score=10.0).score == 10.0

    def test_confidence_at_boundaries(self) -> None:
        assert _make_score_result(confidence=0.0).confidence == 0.0
        assert _make_score_result(confidence=1.0).confidence == 1.0


class TestResearchJob:
    def test_valid_creation(self) -> None:
        now = datetime.now(tz=timezone.utc)
        job = ResearchJob(
            id="job-123",
            status=JobStatus.pending,
            created_at=now,
        )
        assert job.id == "job-123"
        assert job.status == JobStatus.pending
        assert job.completed_at is None
        assert job.progress_pct == 0
        assert job.progress_message == ""

    def test_completed_job(self) -> None:
        now = datetime.now(tz=timezone.utc)
        job = ResearchJob(
            id="job-456",
            status=JobStatus.completed,
            created_at=now,
            completed_at=now,
            progress_pct=100,
            progress_message="Done",
        )
        assert job.status == JobStatus.completed
        assert job.progress_pct == 100


class TestRequirement:
    def test_valid_creation(self) -> None:
        r = Requirement(id="REQ-001", description="Must support REST API", priority=Priority.high)
        assert r.id == "REQ-001"
        assert r.priority == Priority.high

    def test_no_weight_field(self) -> None:
        """Priority-based weighting is derived from config, not stored on model."""
        r = Requirement(id="REQ-002", description="Test", priority=Priority.low)
        assert not hasattr(r, "weight")


class TestVendorRanking:
    def test_valid_creation(self) -> None:
        vr = VendorRanking(vendor="Acme Corp", overall_score=85.5, rank=1)
        assert vr.vendor == "Acme Corp"
        assert vr.overall_score == 85.5
        assert vr.rank == 1


class TestResearchResults:
    def test_valid_creation(self) -> None:
        req = Requirement(id="REQ-001", description="REST API", priority=Priority.high)
        sr = _make_score_result()
        vr = VendorRanking(vendor="Acme", overall_score=85.0, rank=1)

        results = ResearchResults(
            vendors=["Acme"],
            requirements=[req],
            matrix={"Acme": {"REQ-001": sr}},
            rankings=[vr],
            summary="Acme ranked first.",
        )
        assert len(results.vendors) == 1
        assert results.matrix["Acme"]["REQ-001"].score == 8.5
        assert results.rankings[0].rank == 1


# --- ResearchState Tests ---


class TestResearchState:
    def test_typed_dict_creation(self) -> None:
        from app.graph.state import ResearchState

        state: ResearchState = {
            "job_id": "job-001",
            "vendors": ["Acme", "Beta"],
            "requirements": [Requirement(id="R1", description="Test", priority=Priority.high)],
            "iteration": 0,
        }
        assert state["job_id"] == "job-001"
        assert len(state["vendors"]) == 2

    def test_partial_state(self) -> None:
        """ResearchState uses total=False so all fields are optional."""
        from app.graph.state import ResearchState

        state: ResearchState = {}
        assert isinstance(state, dict)

    def test_with_queue(self) -> None:
        from app.graph.state import ResearchState

        q: asyncio.Queue[str] = asyncio.Queue()
        state: ResearchState = {"progress_queue": q}
        assert state["progress_queue"] is q
