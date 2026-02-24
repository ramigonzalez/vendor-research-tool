"""Confidence score computation for vendor research evidence."""

from __future__ import annotations

from datetime import datetime

from dateutil import parser as date_parser

from app.models import Evidence, SourceType

AUTHORITY_WEIGHTS: dict[SourceType, float] = {
    SourceType.official_docs: 1.0,
    SourceType.github: 0.8,
    SourceType.comparison: 0.6,
    SourceType.blog: 0.4,
    SourceType.community: 0.3,
}

# Component weights
_WEIGHT_SOURCE_COUNT = 0.30
_WEIGHT_SOURCE_AUTHORITY = 0.30
_WEIGHT_SOURCE_RECENCY = 0.25
_WEIGHT_CONSISTENCY = 0.15


def _compute_source_count(evidence: list[Evidence]) -> float:
    """Source count component: 5+ sources = full score."""
    return min(len(evidence), 5) / 5


def _compute_source_authority(evidence: list[Evidence]) -> float:
    """Source authority component: mean authority weight across all evidence."""
    total = sum(AUTHORITY_WEIGHTS.get(e.source_type, 0.3) for e in evidence)
    return total / len(evidence)


def _compute_recency_score(content_date: str | None) -> float:
    """Compute recency score for a single piece of evidence."""
    if content_date is None:
        return 0.3
    try:
        parsed_date = date_parser.parse(content_date)
        age_days = (datetime.now() - parsed_date).days
        if age_days <= 180:
            return 1.0
        if age_days <= 365:
            return 0.7
        return 0.3
    except (ValueError, OverflowError):
        return 0.3


def _compute_source_recency(evidence: list[Evidence]) -> float:
    """Source recency component: mean recency score across all evidence."""
    total = sum(_compute_recency_score(e.content_date) for e in evidence)
    return total / len(evidence)


def _compute_consistency(evidence: list[Evidence]) -> float:
    """Consistency component: proportion of supporting evidence."""
    supporting = sum(1 for e in evidence if e.supports_requirement)
    return supporting / len(evidence)


def compute_confidence(evidence: list[Evidence]) -> float:
    """Compute a confidence score from a list of evidence.

    The confidence score is a weighted combination of four components:
    - Source count (30%): coverage measured by number of sources (capped at 5)
    - Source authority (30%): mean authority weight of source types
    - Source recency (25%): how recent the evidence is
    - Consistency (15%): proportion of evidence that supports the requirement

    Args:
        evidence: List of Evidence objects to evaluate.

    Returns:
        A float in [0.0, 1.0] representing confidence.
    """
    if not evidence:
        return 0.0

    source_count = _compute_source_count(evidence)
    authority = _compute_source_authority(evidence)
    recency = _compute_source_recency(evidence)
    consistency = _compute_consistency(evidence)

    raw = (
        _WEIGHT_SOURCE_COUNT * source_count
        + _WEIGHT_SOURCE_AUTHORITY * authority
        + _WEIGHT_SOURCE_RECENCY * recency
        + _WEIGHT_CONSISTENCY * consistency
    )

    return max(0.0, min(1.0, raw))


# ---------------------------------------------------------------------------
# Story 2.3 - Deterministic Score Computation
# ---------------------------------------------------------------------------

from app.models import CapabilityLevel, LLMAssessment, MaturityLevel  # noqa: E402

CAPABILITY_SCORES: dict[CapabilityLevel, float] = {
    CapabilityLevel.full: 10.0,
    CapabilityLevel.partial: 7.0,
    CapabilityLevel.minimal: 3.0,
    CapabilityLevel.none: 0.0,
    CapabilityLevel.unknown: 2.0,
}

MATURITY_SCORES: dict[MaturityLevel, float] = {
    MaturityLevel.ga: 10.0,
    MaturityLevel.beta: 7.0,
    MaturityLevel.experimental: 4.0,
    MaturityLevel.planned: 2.0,
    MaturityLevel.unknown: 3.0,
}


def compute_requirement_score(assessment: LLMAssessment, evidence: list[Evidence]) -> float:
    """Compute a 0-10 score from assessment and evidence. Pure function."""
    capability_score = CAPABILITY_SCORES[assessment.capability_level]
    supporting = [e for e in evidence if e.supports_requirement]
    evidence_score = min(len(supporting), 5) / 5 * 10
    maturity_score = MATURITY_SCORES[assessment.maturity]
    limitations_score = max(0.0, 10.0 - len(assessment.limitations) * 2.0)

    score = 0.40 * capability_score + 0.30 * evidence_score + 0.20 * maturity_score + 0.10 * limitations_score
    return max(0.0, min(10.0, score))


# ---------------------------------------------------------------------------
# Story 2.5 - Weighted Vendor Ranking
# ---------------------------------------------------------------------------

from app.config import PRIORITY_WEIGHTS  # noqa: E402, I001
from app.models import Requirement, ScoreResult as _ScoreResult, VendorRanking  # noqa: E402


def compute_vendor_rankings(
    scores: dict[str, dict[str, _ScoreResult]],
    requirements: list[Requirement],
) -> list[VendorRanking]:
    """Compute priority-weighted vendor rankings normalized to 0-100."""
    max_possible = sum(10.0 * PRIORITY_WEIGHTS[req.priority.value] * 1.0 for req in requirements)

    rankings = []
    for vendor, req_scores in scores.items():
        weighted_sum = 0.0
        for req in requirements:
            if req.id in req_scores:
                result = req_scores[req.id]
                weight = PRIORITY_WEIGHTS[req.priority.value]
                weighted_sum += result.score * weight * result.confidence

        normalized = (weighted_sum / max_possible) * 100 if max_possible > 0 else 0.0
        rankings.append({"vendor": vendor, "weighted_score": round(normalized, 2)})

    sorted_rankings = sorted(rankings, key=lambda x: (-x["weighted_score"], x["vendor"]))
    return [
        VendorRanking(vendor=r["vendor"], overall_score=r["weighted_score"], rank=i + 1)
        for i, r in enumerate(sorted_rankings)
    ]
