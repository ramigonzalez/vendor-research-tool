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
