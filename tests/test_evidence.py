"""Tests for evidence gap analysis and research loop (Story 1.4)."""

from __future__ import annotations

import pytest

from app.graph.nodes import (
    check_evidence_sufficiency,
    diagnose_gap,
    find_evidence_gaps,
    generate_refined_queries,
    prepare_gap_filling,
    should_continue_research,
)
from app.graph.state import ResearchState
from app.models import Evidence, GapType, Priority, Requirement, SourceType

# --- Helpers ---


def _ev(
    source_type: SourceType = SourceType.community,
    relevance: float = 0.5,
) -> Evidence:
    """Create a minimal Evidence instance for testing."""
    return Evidence(
        claim="test claim",
        source_url="https://example.com",
        source_name="Test",
        source_type=source_type,
        relevance=relevance,
        supports_requirement=True,
    )


REQUIREMENTS = [
    Requirement(id="R1", description="Framework-agnostic tracing", priority=Priority.high),
    Requirement(id="R2", description="Self-hosting support", priority=Priority.medium),
]


def _make_state(
    vendors: list[str] | None = None,
    requirements: list[Requirement] | None = None,
    evidence: dict[str, dict[str, list[Evidence]]] | None = None,
    iteration: int = 0,
) -> ResearchState:
    """Create a ResearchState for gap analysis tests."""
    state: ResearchState = {
        "vendors": vendors if vendors is not None else ["VendorA"],
        "requirements": requirements if requirements is not None else REQUIREMENTS,
        "evidence": evidence if evidence is not None else {},
        "iteration": iteration,
    }
    return state


# --- check_evidence_sufficiency ---


class TestCheckEvidenceSufficiency:
    def test_empty_list_returns_false(self) -> None:
        assert check_evidence_sufficiency([]) is False

    def test_single_source_returns_false(self) -> None:
        assert check_evidence_sufficiency([_ev(SourceType.github, 0.9)]) is False

    def test_two_community_sources_returns_false(self) -> None:
        """No authoritative source present."""
        evidence = [
            _ev(SourceType.community, 0.9),
            _ev(SourceType.community, 0.8),
        ]
        assert check_evidence_sufficiency(evidence) is False

    def test_two_official_docs_low_relevance_returns_false(self) -> None:
        """Authoritative but all relevance < 0.5."""
        evidence = [
            _ev(SourceType.official_docs, 0.3),
            _ev(SourceType.official_docs, 0.4),
        ]
        assert check_evidence_sufficiency(evidence) is False

    def test_sufficient_evidence_returns_true(self) -> None:
        """Two sources, one github (authoritative), one with relevance >= 0.5."""
        evidence = [
            _ev(SourceType.github, 0.6),
            _ev(SourceType.blog, 0.8),
        ]
        assert check_evidence_sufficiency(evidence) is True

    def test_official_docs_with_relevant_returns_true(self) -> None:
        evidence = [
            _ev(SourceType.official_docs, 0.5),
            _ev(SourceType.community, 0.1),
        ]
        assert check_evidence_sufficiency(evidence) is True


# --- diagnose_gap ---


class TestDiagnoseGap:
    def test_empty_evidence(self) -> None:
        assert diagnose_gap([]) == GapType.no_evidence

    def test_community_sources_only(self) -> None:
        evidence = [_ev(SourceType.community, 0.9), _ev(SourceType.blog, 0.8)]
        assert diagnose_gap(evidence) == GapType.no_authoritative_source

    def test_low_relevance(self) -> None:
        """Has authoritative source but all relevance < 0.5."""
        evidence = [_ev(SourceType.github, 0.3), _ev(SourceType.community, 0.2)]
        assert diagnose_gap(evidence) == GapType.low_relevance

    def test_insufficient_count(self) -> None:
        """One source that is authoritative and relevant -> insufficient_count."""
        evidence = [_ev(SourceType.official_docs, 0.9)]
        assert diagnose_gap(evidence) == GapType.insufficient_count


# --- should_continue_research ---


class TestShouldContinueResearch:
    def test_proceed_when_iteration_at_max(self) -> None:
        """Returns 'proceed' when iteration >= 2 regardless of gaps."""
        state = _make_state(
            vendors=["VendorA"],
            evidence={},
            iteration=2,
        )
        assert should_continue_research(state) == "proceed"

    def test_proceed_when_no_gaps(self) -> None:
        """Returns 'proceed' when all evidence is sufficient."""
        evidence = {
            "VendorA": {
                "R1": [_ev(SourceType.github, 0.9), _ev(SourceType.blog, 0.7)],
                "R2": [_ev(SourceType.official_docs, 0.8), _ev(SourceType.community, 0.6)],
            },
        }
        state = _make_state(vendors=["VendorA"], evidence=evidence, iteration=0)
        assert should_continue_research(state) == "proceed"

    def test_continue_when_gaps_exist(self) -> None:
        """Returns 'continue' when gaps exist and iteration < 2."""
        state = _make_state(
            vendors=["VendorA"],
            evidence={},
            iteration=0,
        )
        assert should_continue_research(state) == "continue"

    def test_continue_at_iteration_1(self) -> None:
        state = _make_state(vendors=["VendorA"], evidence={}, iteration=1)
        assert should_continue_research(state) == "continue"


# --- generate_refined_queries ---


class TestGenerateRefinedQueries:
    def test_no_evidence_returns_two_queries(self) -> None:
        queries = generate_refined_queries("VendorA", "tracing support", GapType.no_evidence)
        assert len(queries) == 2

    def test_no_authoritative_source_returns_two_queries(self) -> None:
        queries = generate_refined_queries("VendorA", "tracing", GapType.no_authoritative_source)
        assert len(queries) == 2

    def test_no_authoritative_includes_github(self) -> None:
        queries = generate_refined_queries("VendorA", "tracing", GapType.no_authoritative_source)
        assert any("site:github.com" in q for q in queries)

    def test_low_relevance_returns_two_queries(self) -> None:
        queries = generate_refined_queries("VendorA", "tracing support feature", GapType.low_relevance)
        assert len(queries) == 2

    def test_insufficient_count_returns_two_queries(self) -> None:
        queries = generate_refined_queries("VendorA", "metrics", GapType.insufficient_count)
        assert len(queries) == 2

    def test_queries_contain_vendor_name(self) -> None:
        for gap_type in GapType:
            queries = generate_refined_queries("TestVendor", "some requirement", gap_type)
            for q in queries:
                assert "TestVendor" in q


# --- find_evidence_gaps ---


class TestFindEvidenceGaps:
    def test_identifies_gaps(self) -> None:
        """Pairs below threshold are returned."""
        state = _make_state(
            vendors=["VendorA"],
            evidence={},
        )
        gaps = find_evidence_gaps(state)
        # VendorA x R1, VendorA x R2 -> both missing evidence
        assert len(gaps) == 2
        assert ("VendorA", "R1") in gaps
        assert ("VendorA", "R2") in gaps

    def test_empty_when_all_sufficient(self) -> None:
        """No gaps when all pairs have sufficient evidence."""
        evidence = {
            "VendorA": {
                "R1": [_ev(SourceType.github, 0.9), _ev(SourceType.blog, 0.7)],
                "R2": [_ev(SourceType.official_docs, 0.8), _ev(SourceType.community, 0.6)],
            },
        }
        state = _make_state(vendors=["VendorA"], evidence=evidence)
        gaps = find_evidence_gaps(state)
        assert gaps == []

    def test_partial_gaps(self) -> None:
        """Only insufficient pairs are returned."""
        evidence = {
            "VendorA": {
                "R1": [_ev(SourceType.github, 0.9), _ev(SourceType.blog, 0.7)],
                "R2": [],  # gap
            },
        }
        state = _make_state(vendors=["VendorA"], evidence=evidence)
        gaps = find_evidence_gaps(state)
        assert gaps == [("VendorA", "R2")]


# --- prepare_gap_filling ---


class TestPrepareGapFilling:
    @pytest.mark.asyncio
    async def test_returns_incremented_iteration(self) -> None:
        state = _make_state(vendors=["VendorA"], evidence={}, iteration=0)
        result = await prepare_gap_filling(state)
        assert result["iteration"] == 1

    @pytest.mark.asyncio
    async def test_generates_queries_for_gaps(self) -> None:
        state = _make_state(vendors=["VendorA"], evidence={}, iteration=0)
        result = await prepare_gap_filling(state)
        assert "VendorA:R1" in result["queries"]
        assert "VendorA:R2" in result["queries"]
        for _key, queries in result["queries"].items():
            assert len(queries) == 2

    @pytest.mark.asyncio
    async def test_gap_metadata_populated(self) -> None:
        state = _make_state(vendors=["VendorA"], evidence={}, iteration=0)
        result = await prepare_gap_filling(state)
        assert len(result["gaps"]) == 2
        for gap in result["gaps"]:
            assert "vendor" in gap
            assert "requirement_id" in gap
            assert "gap_type" in gap

    @pytest.mark.asyncio
    async def test_no_gaps_returns_empty(self) -> None:
        evidence = {
            "VendorA": {
                "R1": [_ev(SourceType.github, 0.9), _ev(SourceType.blog, 0.7)],
                "R2": [_ev(SourceType.official_docs, 0.8), _ev(SourceType.community, 0.6)],
            },
        }
        state = _make_state(vendors=["VendorA"], evidence=evidence, iteration=0)
        result = await prepare_gap_filling(state)
        assert result["queries"] == {}
        assert result["gaps"] == []
        assert result["iteration"] == 1
