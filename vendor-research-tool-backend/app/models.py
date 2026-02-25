"""Pydantic v2 domain models for the SignalCore Vendor Research Tool."""

from datetime import datetime
from enum import Enum

from typing import Literal

from pydantic import BaseModel, field_validator


class SourceType(str, Enum):
    """Types of research sources."""

    official_docs = "official_docs"
    github = "github"
    comparison = "comparison"
    blog = "blog"
    community = "community"


class CapabilityLevel(str, Enum):
    """Capability assessment levels."""

    full = "full"
    partial = "partial"
    minimal = "minimal"
    none = "none"
    unknown = "unknown"


class MaturityLevel(str, Enum):
    """Maturity assessment levels."""

    ga = "ga"
    beta = "beta"
    experimental = "experimental"
    planned = "planned"
    unknown = "unknown"


class JobStatus(str, Enum):
    """Research job status."""

    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class Priority(str, Enum):
    """Requirement priority levels."""

    high = "high"
    medium = "medium"
    low = "low"


class GapType(str, Enum):
    """Types of evidence gaps."""

    no_evidence = "no_evidence"
    no_authoritative_source = "no_authoritative_source"
    low_relevance = "low_relevance"
    insufficient_count = "insufficient_count"


class Evidence(BaseModel):
    """A piece of evidence supporting or refuting a claim about a vendor."""

    claim: str
    source_url: str
    source_name: str
    source_type: SourceType
    content_date: str | None = None
    relevance: float
    supports_requirement: bool

    @field_validator("relevance")
    @classmethod
    def validate_relevance(cls, v: float) -> float:
        """Clamp relevance to 0-1 range."""
        return max(0.0, min(1.0, v))


class LLMAssessment(BaseModel):
    """LLM-generated assessment of a vendor's capability for a requirement."""

    capability_level: CapabilityLevel
    capability_details: str
    maturity: MaturityLevel
    limitations: list[str]
    supports_requirement: bool


class ScoreResult(BaseModel):
    """Scored result for a vendor-requirement pair."""

    score: float
    confidence: float
    capability_level: CapabilityLevel
    maturity: MaturityLevel
    justification: str
    limitations: list[str]
    evidence: list[Evidence]
    status: Literal["ok", "degraded", "error"] = "ok"
    status_detail: str | None = None

    @field_validator("score")
    @classmethod
    def validate_score(cls, v: float) -> float:
        """Clamp score to 0-10 range."""
        return max(0.0, min(10.0, v))

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Clamp confidence to 0-1 range."""
        return max(0.0, min(1.0, v))


class ResearchJob(BaseModel):
    """Tracks the status of a research job."""

    id: str
    status: JobStatus
    created_at: datetime
    completed_at: datetime | None = None
    progress_pct: int = 0
    progress_message: str = ""


class Requirement(BaseModel):
    """A research requirement with priority-based weighting."""

    id: str
    description: str
    priority: Priority


class VendorRanking(BaseModel):
    """Ranking result for a single vendor."""

    vendor: str
    overall_score: float
    rank: int


class ResearchResults(BaseModel):
    """Complete research results for a set of vendors and requirements."""

    vendors: list[str]
    requirements: list[Requirement]
    matrix: dict[str, dict[str, ScoreResult]]
    rankings: list[VendorRanking]
    summary: str
