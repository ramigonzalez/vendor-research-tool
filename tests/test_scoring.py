"""Tests for confidence score computation."""

from __future__ import annotations

from datetime import datetime, timedelta

from app.models import Evidence, SourceType
from app.scoring.engine import AUTHORITY_WEIGHTS, compute_confidence


def _make_evidence(
    source_type: SourceType = SourceType.official_docs,
    content_date: str | None = None,
    supports: bool = True,
) -> Evidence:
    """Helper to create an Evidence instance with sensible defaults."""
    return Evidence(
        claim="Test claim",
        source_url="https://example.com",
        source_name="Test Source",
        source_type=source_type,
        content_date=content_date,
        relevance=0.9,
        supports_requirement=supports,
    )


def _recent_date() -> str:
    """Return an ISO date string within the last 30 days."""
    return (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d")


def _old_date() -> str:
    """Return an ISO date string older than 1 year."""
    return (datetime.now() - timedelta(days=500)).strftime("%Y-%m-%d")


def _mid_date() -> str:
    """Return an ISO date string 7-12 months ago."""
    return (datetime.now() - timedelta(days=270)).strftime("%Y-%m-%d")


class TestComputeConfidenceEmpty:
    """Empty evidence list returns 0.0."""

    def test_empty_list_returns_zero(self) -> None:
        assert compute_confidence([]) == 0.0


class TestComputeConfidencePerfect:
    """5 official_docs, all recent, all supporting -> near 1.0."""

    def test_perfect_evidence(self) -> None:
        evidence = [
            _make_evidence(
                source_type=SourceType.official_docs,
                content_date=_recent_date(),
                supports=True,
            )
            for _ in range(5)
        ]
        result = compute_confidence(evidence)
        assert result >= 0.95, f"Expected ~1.0, got {result}"


class TestComputeConfidenceLow:
    """1 blog, old, not supporting -> low confidence."""

    def test_low_confidence(self) -> None:
        evidence = [
            _make_evidence(
                source_type=SourceType.blog,
                content_date=_old_date(),
                supports=False,
            )
        ]
        result = compute_confidence(evidence)
        # source_count: 1/5=0.2, authority: 0.4, recency: 0.3, consistency: 0.0
        # 0.30*0.2 + 0.30*0.4 + 0.25*0.3 + 0.15*0.0 = 0.06+0.12+0.075+0 = 0.255
        assert result < 0.35, f"Expected low confidence, got {result}"


class TestComputeConfidenceMixedDates:
    """Mixed dates including None handled gracefully."""

    def test_mixed_dates(self) -> None:
        evidence = [
            _make_evidence(content_date=_recent_date()),
            _make_evidence(content_date=None),
            _make_evidence(content_date=_old_date()),
            _make_evidence(content_date="March 2024"),
        ]
        result = compute_confidence(evidence)
        assert 0.0 <= result <= 1.0


class TestComputeConfidenceCountCap:
    """6 sources — count component capped at 5."""

    def test_count_capped_at_five(self) -> None:
        evidence_5 = [_make_evidence(content_date=_recent_date()) for _ in range(5)]
        evidence_6 = [_make_evidence(content_date=_recent_date()) for _ in range(6)]
        conf_5 = compute_confidence(evidence_5)
        conf_6 = compute_confidence(evidence_6)
        # The count component should be the same (1.0) for both 5 and 6 sources.
        # The overall scores may differ slightly due to rounding, but
        # the 6-source score should not be meaningfully higher than 5-source.
        assert conf_6 >= conf_5 - 0.01, "6 sources should not score less than 5"
        # Both should be high since all are official_docs, recent, supporting
        assert conf_5 >= 0.95
        assert conf_6 >= 0.95


class TestComputeConfidenceAllNotSupporting:
    """All sources not supporting -> consistency = 0.0."""

    def test_all_not_supporting(self) -> None:
        evidence = [_make_evidence(content_date=_recent_date(), supports=False) for _ in range(3)]
        result = compute_confidence(evidence)
        # consistency component is 0, so total is reduced by 15%
        # Still has count, authority, recency contributions
        assert 0.0 < result < 0.90


class TestComputeConfidenceMixedSupport:
    """Mixed support -> consistency = proportion."""

    def test_mixed_support(self) -> None:
        evidence = [
            _make_evidence(content_date=_recent_date(), supports=True),
            _make_evidence(content_date=_recent_date(), supports=True),
            _make_evidence(content_date=_recent_date(), supports=False),
            _make_evidence(content_date=_recent_date(), supports=False),
        ]
        result = compute_confidence(evidence)
        # consistency = 2/4 = 0.5
        # All official_docs, recent -> authority=1.0, recency=1.0, count=4/5=0.8
        # 0.30*0.8 + 0.30*1.0 + 0.25*1.0 + 0.15*0.5 = 0.24+0.30+0.25+0.075 = 0.865
        assert 0.80 <= result <= 0.92, f"Expected ~0.865, got {result}"


class TestAuthorityWeights:
    """Authority weights are exported and correct."""

    def test_authority_weights_complete(self) -> None:
        for source_type in SourceType:
            assert source_type in AUTHORITY_WEIGHTS, f"Missing weight for {source_type}"

    def test_authority_weights_values(self) -> None:
        assert AUTHORITY_WEIGHTS[SourceType.official_docs] == 1.0
        assert AUTHORITY_WEIGHTS[SourceType.github] == 0.8
        assert AUTHORITY_WEIGHTS[SourceType.comparison] == 0.6
        assert AUTHORITY_WEIGHTS[SourceType.blog] == 0.4
        assert AUTHORITY_WEIGHTS[SourceType.community] == 0.3


class TestDateParsing:
    """Various date formats handled correctly."""

    def test_iso_format(self) -> None:
        evidence = [_make_evidence(content_date=_recent_date())]
        result = compute_confidence(evidence)
        assert result > 0.0

    def test_month_year_format(self) -> None:
        evidence = [_make_evidence(content_date="January 2020")]
        result = compute_confidence(evidence)
        assert result > 0.0

    def test_year_only_format(self) -> None:
        evidence = [_make_evidence(content_date="2020")]
        result = compute_confidence(evidence)
        assert result > 0.0

    def test_invalid_date_string(self) -> None:
        evidence = [_make_evidence(content_date="not-a-date")]
        result = compute_confidence(evidence)
        assert result > 0.0

    def test_none_date(self) -> None:
        evidence = [_make_evidence(content_date=None)]
        result = compute_confidence(evidence)
        assert result > 0.0


# ---------------------------------------------------------------------------
# Story 2.3 - Deterministic Score Computation Tests
# ---------------------------------------------------------------------------

import pytest  # noqa: E402

from app.models import CapabilityLevel, LLMAssessment, MaturityLevel  # noqa: E402
from app.scoring.engine import (  # noqa: E402
    CAPABILITY_SCORES,
    MATURITY_SCORES,
    compute_requirement_score,
)


def _make_assessment(
    capability: CapabilityLevel = CapabilityLevel.full,
    maturity: MaturityLevel = MaturityLevel.ga,
    limitations: list[str] | None = None,
) -> LLMAssessment:
    """Helper to create an LLMAssessment with sensible defaults."""
    return LLMAssessment(
        capability_level=capability,
        capability_details="Test details",
        maturity=maturity,
        limitations=limitations or [],
        supports_requirement=True,
    )


class TestComputeRequirementScore:
    """Tests for compute_requirement_score pure function."""

    def test_full_ga_5_supporting_0_limitations(self) -> None:
        """full + ga + 5 supporting + 0 limitations -> score ~ 10.0."""
        assessment = _make_assessment(CapabilityLevel.full, MaturityLevel.ga, [])
        evidence = [_make_evidence(supports=True) for _ in range(5)]
        score = compute_requirement_score(assessment, evidence)
        assert score == 10.0, f"Expected 10.0, got {score}"

    def test_none_unknown_0_supporting_0_limitations(self) -> None:
        """none + unknown + 0 supporting + 0 limitations -> 1.6."""
        assessment = _make_assessment(CapabilityLevel.none, MaturityLevel.unknown, [])
        score = compute_requirement_score(assessment, [])
        # 0.4*0 + 0.3*0 + 0.2*3 + 0.1*10 = 0 + 0 + 0.6 + 1.0 = 1.6
        assert score == 1.6, f"Expected 1.6, got {score}"

    def test_unknown_unknown_0_supporting_0_limitations(self) -> None:
        """unknown + unknown + 0 supporting + 0 limitations -> 2.4."""
        assessment = _make_assessment(CapabilityLevel.unknown, MaturityLevel.unknown, [])
        score = compute_requirement_score(assessment, [])
        # 0.4*2 + 0.3*0 + 0.2*3 + 0.1*10 = 0.8 + 0 + 0.6 + 1.0 = 2.4
        assert score == pytest.approx(2.4), f"Expected 2.4, got {score}"

    def test_limitations_clamped_at_zero(self) -> None:
        """5 limitations -> limitations_score = max(0, 10-10) = 0, not negative."""
        assessment = _make_assessment(CapabilityLevel.full, MaturityLevel.ga, ["a", "b", "c", "d", "e"])
        evidence = [_make_evidence(supports=True) for _ in range(5)]
        score = compute_requirement_score(assessment, evidence)
        # 0.4*10 + 0.3*10 + 0.2*10 + 0.1*0 = 4+3+2+0 = 9.0
        assert score == 9.0, f"Expected 9.0, got {score}"

    def test_evidence_count_capped_at_5(self) -> None:
        """6 supporting evidence should produce same score as 5."""
        assessment = _make_assessment(CapabilityLevel.full, MaturityLevel.ga, [])
        ev_5 = [_make_evidence(supports=True) for _ in range(5)]
        ev_6 = [_make_evidence(supports=True) for _ in range(6)]
        score_5 = compute_requirement_score(assessment, ev_5)
        score_6 = compute_requirement_score(assessment, ev_6)
        assert score_5 == score_6, f"Expected equal scores, got {score_5} vs {score_6}"

    def test_partial_beta_3_supporting_1_limitation(self) -> None:
        """partial + beta + 3 supporting + 1 limitation -> specific calculation."""
        assessment = _make_assessment(CapabilityLevel.partial, MaturityLevel.beta, ["limit1"])
        evidence = [_make_evidence(supports=True) for _ in range(3)]
        score = compute_requirement_score(assessment, evidence)
        # capability: 0.4*7 = 2.8
        # evidence: 0.3*(3/5*10) = 0.3*6 = 1.8
        # maturity: 0.2*7 = 1.4
        # limitations: 0.1*(10-2) = 0.1*8 = 0.8
        # total = 2.8 + 1.8 + 1.4 + 0.8 = 6.8
        assert score == 6.8, f"Expected 6.8, got {score}"


class TestCapabilityAndMaturityScores:
    """Verify lookup table values."""

    def test_capability_scores_values(self) -> None:
        assert CAPABILITY_SCORES[CapabilityLevel.full] == 10.0
        assert CAPABILITY_SCORES[CapabilityLevel.partial] == 7.0
        assert CAPABILITY_SCORES[CapabilityLevel.minimal] == 3.0
        assert CAPABILITY_SCORES[CapabilityLevel.none] == 0.0
        assert CAPABILITY_SCORES[CapabilityLevel.unknown] == 2.0

    def test_capability_scores_complete(self) -> None:
        for level in CapabilityLevel:
            assert level in CAPABILITY_SCORES, f"Missing score for {level}"

    def test_maturity_scores_values(self) -> None:
        assert MATURITY_SCORES[MaturityLevel.ga] == 10.0
        assert MATURITY_SCORES[MaturityLevel.beta] == 7.0
        assert MATURITY_SCORES[MaturityLevel.experimental] == 4.0
        assert MATURITY_SCORES[MaturityLevel.planned] == 2.0
        assert MATURITY_SCORES[MaturityLevel.unknown] == 3.0

    def test_maturity_scores_complete(self) -> None:
        for level in MaturityLevel:
            assert level in MATURITY_SCORES, f"Missing score for {level}"
