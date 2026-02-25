"""Tests for LangGraph node functions."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.graph.nodes import _build_fallback_queries, execute_searches, generate_queries
from app.graph.state import ResearchState
from app.models import Priority, Requirement

# --- Fixtures ---

VENDORS = ["LangSmith", "Langfuse", "Braintrust", "PostHog"]

REQUIREMENTS = [
    Requirement(id="R1", description="Framework-agnostic tracing", priority=Priority.high),
    Requirement(id="R2", description="Self-hosting support", priority=Priority.high),
    Requirement(id="R3", description="Evaluation framework", priority=Priority.medium),
    Requirement(id="R4", description="OpenTelemetry integration", priority=Priority.medium),
    Requirement(id="R5", description="Custom metrics", priority=Priority.low),
    Requirement(id="R6", description="Cost transparency", priority=Priority.low),
]


def _make_state(vendors: list[str] | None = None, requirements: list[Requirement] | None = None) -> ResearchState:
    """Create a minimal ResearchState for testing."""
    state: ResearchState = {
        "vendors": vendors if vendors is not None else VENDORS,
        "requirements": requirements if requirements is not None else REQUIREMENTS,
    }
    return state


def _mock_ai_message(content: str) -> MagicMock:
    """Create a mock AI message with the given content."""
    msg = MagicMock()
    msg.content = content
    return msg


# --- Tests ---


class TestBuildFallbackQueries:
    def test_returns_two_queries(self) -> None:
        queries = _build_fallback_queries("LangSmith", "Framework-agnostic tracing")
        assert len(queries) == 2

    def test_first_query_targets_docs(self) -> None:
        queries = _build_fallback_queries("LangSmith", "Framework-agnostic tracing")
        assert "official documentation" in queries[0]
        assert "site:docs.langsmith.com" in queries[0]

    def test_second_query_targets_reviews(self) -> None:
        queries = _build_fallback_queries("LangSmith", "Framework-agnostic tracing")
        assert "comparison review 2024" in queries[1]

    def test_vendor_lowercased_in_docs_url(self) -> None:
        queries = _build_fallback_queries("PostHog", "Custom metrics")
        assert "site:docs.posthog.com" in queries[0]


class TestGenerateQueries:
    @pytest.mark.asyncio
    async def test_generates_24_query_pairs(self) -> None:
        """4 vendors x 6 requirements = 24 query pairs."""
        state = _make_state()

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(
            return_value=_mock_ai_message('{"query_1": "test query 1", "query_2": "test query 2"}')
        )

        mock_parser = AsyncMock()
        mock_parser.ainvoke = AsyncMock(return_value={"query_1": "test query 1", "query_2": "test query 2"})

        with (
            patch("app.graph.nodes.get_llm", return_value=mock_llm),
            patch("app.graph.nodes.JsonOutputParser", return_value=mock_parser),
        ):
            result = await generate_queries(state)

        queries = result["queries"]
        assert len(queries) == 24

        # Verify all vendor:requirement keys exist
        for vendor in VENDORS:
            for req in REQUIREMENTS:
                key = f"{vendor}:{req.id}"
                assert key in queries, f"Missing key: {key}"
                assert len(queries[key]) == 2

    @pytest.mark.asyncio
    async def test_returns_partial_state_dict(self) -> None:
        """Node must return dict with only 'queries' key (LangGraph pattern)."""
        state = _make_state()

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=_mock_ai_message('{"query_1": "q1", "query_2": "q2"}'))

        mock_parser = AsyncMock()
        mock_parser.ainvoke = AsyncMock(return_value={"query_1": "q1", "query_2": "q2"})

        with (
            patch("app.graph.nodes.get_llm", return_value=mock_llm),
            patch("app.graph.nodes.JsonOutputParser", return_value=mock_parser),
        ):
            result = await generate_queries(state)

        assert isinstance(result, dict)
        assert list(result.keys()) == ["queries"]

    @pytest.mark.asyncio
    async def test_fallback_on_invalid_llm_response(self) -> None:
        """When LLM returns unparseable response, fallback queries are used."""
        state = _make_state(
            vendors=["LangSmith"],
            requirements=[Requirement(id="R1", description="Framework-agnostic tracing", priority=Priority.high)],
        )

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=_mock_ai_message("This is not valid JSON"))

        mock_parser = AsyncMock()
        mock_parser.ainvoke = AsyncMock(side_effect=Exception("Failed to parse"))

        with (
            patch("app.graph.nodes.get_llm", return_value=mock_llm),
            patch("app.graph.nodes.JsonOutputParser", return_value=mock_parser),
        ):
            result = await generate_queries(state)

        queries = result["queries"]
        key = "LangSmith:R1"
        assert key in queries
        assert len(queries[key]) == 2
        assert "official documentation" in queries[key][0]
        assert "comparison review 2024" in queries[key][1]

    @pytest.mark.asyncio
    async def test_fallback_on_incomplete_response(self) -> None:
        """When LLM returns JSON missing query_2, fallback queries are used."""
        state = _make_state(
            vendors=["Langfuse"],
            requirements=[Requirement(id="R2", description="Self-hosting support", priority=Priority.high)],
        )

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=_mock_ai_message('{"query_1": "some query"}'))

        mock_parser = AsyncMock()
        mock_parser.ainvoke = AsyncMock(return_value={"query_1": "some query"})

        with (
            patch("app.graph.nodes.get_llm", return_value=mock_llm),
            patch("app.graph.nodes.JsonOutputParser", return_value=mock_parser),
        ):
            result = await generate_queries(state)

        queries = result["queries"]
        key = "Langfuse:R2"
        assert key in queries
        assert "official documentation" in queries[key][0]
        assert "comparison review 2024" in queries[key][1]

    @pytest.mark.asyncio
    async def test_empty_vendors(self) -> None:
        """When no vendors provided, returns empty queries dict."""
        state = _make_state(vendors=[], requirements=REQUIREMENTS)

        with (
            patch("app.graph.nodes.get_llm"),
            patch("app.graph.nodes.JsonOutputParser"),
        ):
            result = await generate_queries(state)

        assert result == {"queries": {}}

    @pytest.mark.asyncio
    async def test_empty_requirements(self) -> None:
        """When no requirements provided, returns empty queries dict."""
        state = _make_state(vendors=VENDORS, requirements=[])

        with (
            patch("app.graph.nodes.get_llm"),
            patch("app.graph.nodes.JsonOutputParser"),
        ):
            result = await generate_queries(state)

        assert result == {"queries": {}}

    @pytest.mark.asyncio
    async def test_queries_are_strings(self) -> None:
        """All query values should be lists of strings."""
        state = _make_state(
            vendors=["PostHog"],
            requirements=[Requirement(id="R5", description="Custom metrics", priority=Priority.low)],
        )

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(
            return_value=_mock_ai_message(
                '{"query_1": "PostHog custom metrics docs 2025", "query_2": "PostHog metrics review comparison 2024"}'
            )
        )

        mock_parser = AsyncMock()
        mock_parser.ainvoke = AsyncMock(
            return_value={
                "query_1": "PostHog custom metrics docs 2025",
                "query_2": "PostHog metrics review comparison 2024",
            }
        )

        with (
            patch("app.graph.nodes.get_llm", return_value=mock_llm),
            patch("app.graph.nodes.JsonOutputParser", return_value=mock_parser),
        ):
            result = await generate_queries(state)

        queries = result["queries"]
        for key, query_list in queries.items():
            assert isinstance(key, str)
            assert isinstance(query_list, list)
            for q in query_list:
                assert isinstance(q, str)


# ---------------------------------------------------------------------------
# Story 1.2 - execute_searches tests
# ---------------------------------------------------------------------------


def _make_search_state(
    queries: dict[str, list[str]] | None = None,
) -> ResearchState:
    """Create a minimal ResearchState with queries for search tests."""
    state: ResearchState = {
        "vendors": VENDORS,
        "requirements": REQUIREMENTS,
        "queries": queries if queries is not None else {},
    }
    return state


class TestExecuteSearches:
    @pytest.mark.asyncio
    async def test_all_searches_scheduled(self) -> None:
        """Each query in every pair produces one search call."""
        queries = {
            "LangSmith:R1": ["query a", "query b"],
            "Langfuse:R2": ["query c", "query d"],
        }
        state = _make_search_state(queries)

        mock_client = AsyncMock()
        mock_client.search = AsyncMock(return_value={"results": [{"title": "r"}]})

        with patch("app.graph.nodes.AsyncTavilyClient", return_value=mock_client), patch("app.graph.nodes.settings"):
            result = await execute_searches(state)

        assert mock_client.search.call_count == 4
        assert len(result["raw_results"]) == 4

    @pytest.mark.asyncio
    async def test_raw_results_keyed_correctly(self) -> None:
        """Keys follow the vendor:req_id:query_idx pattern."""
        queries = {
            "LangSmith:R1": ["query a", "query b"],
        }
        state = _make_search_state(queries)

        mock_client = AsyncMock()
        mock_client.search = AsyncMock(return_value={"results": [{"url": "http://example.com"}]})

        with patch("app.graph.nodes.AsyncTavilyClient", return_value=mock_client), patch("app.graph.nodes.settings"):
            result = await execute_searches(state)

        raw = result["raw_results"]
        assert "LangSmith:R1:0" in raw
        assert "LangSmith:R1:1" in raw

    @pytest.mark.asyncio
    async def test_individual_failure_does_not_abort(self) -> None:
        """A single search failure returns [] for that key; others succeed."""
        queries = {
            "LangSmith:R1": ["good query"],
            "Langfuse:R2": ["bad query"],
        }
        state = _make_search_state(queries)

        mock_client = AsyncMock()

        async def _side_effect(**kwargs: object) -> dict:
            query = kwargs.get("query", "")
            if query == "bad query":
                raise RuntimeError("Tavily error")
            return {"results": [{"title": "ok"}]}

        mock_client.search = AsyncMock(side_effect=_side_effect)

        with patch("app.graph.nodes.AsyncTavilyClient", return_value=mock_client), patch("app.graph.nodes.settings"):
            result = await execute_searches(state)

        raw = result["raw_results"]
        assert raw["LangSmith:R1:0"] == [{"title": "ok"}]
        assert raw["Langfuse:R2:0"] == []

    @pytest.mark.asyncio
    async def test_empty_queries_returns_empty(self) -> None:
        """No queries produces empty raw_results."""
        state = _make_search_state(queries={})

        with patch("app.graph.nodes.AsyncTavilyClient", return_value=AsyncMock()), patch("app.graph.nodes.settings"):
            result = await execute_searches(state)

        assert result == {"raw_results": {}}

    @pytest.mark.asyncio
    async def test_semaphore_limits_concurrency(self) -> None:
        """Verify the semaphore caps concurrent searches at 5."""
        import asyncio

        queries = {f"V{i}:R1": ["q"] for i in range(10)}
        state = _make_search_state(queries)

        peak_concurrent = 0
        current_concurrent = 0
        lock = asyncio.Lock()

        async def _tracking_search(**kwargs: object) -> dict:
            nonlocal peak_concurrent, current_concurrent
            async with lock:
                current_concurrent += 1
                if current_concurrent > peak_concurrent:
                    peak_concurrent = current_concurrent
            await asyncio.sleep(0.01)
            async with lock:
                current_concurrent -= 1
            return {"results": []}

        mock_client = AsyncMock()
        mock_client.search = AsyncMock(side_effect=_tracking_search)

        with patch("app.graph.nodes.AsyncTavilyClient", return_value=mock_client), patch("app.graph.nodes.settings"):
            await execute_searches(state)

        assert peak_concurrent <= 5

    @pytest.mark.asyncio
    async def test_returns_partial_state_dict(self) -> None:
        """Node must return dict with only 'raw_results' key (LangGraph pattern)."""
        state = _make_search_state(queries={"V:R1": ["q"]})

        mock_client = AsyncMock()
        mock_client.search = AsyncMock(return_value={"results": []})

        with patch("app.graph.nodes.AsyncTavilyClient", return_value=mock_client), patch("app.graph.nodes.settings"):
            result = await execute_searches(state)

        assert isinstance(result, dict)
        assert list(result.keys()) == ["raw_results"]


# ---------------------------------------------------------------------------
# Story 1.3 - extract_evidence tests
# ---------------------------------------------------------------------------

from app.graph.nodes import _extract_evidence_for_pair, extract_evidence  # noqa: E402
from app.models import Evidence, SourceType  # noqa: E402


def _make_evidence_state(
    raw_results: dict[str, list[dict]] | None = None,
    vendors: list[str] | None = None,
    requirements: list[Requirement] | None = None,
) -> ResearchState:
    """Create a minimal ResearchState for evidence extraction tests."""
    state: ResearchState = {
        "vendors": vendors if vendors is not None else ["LangSmith"],
        "requirements": requirements
        if requirements is not None
        else [Requirement(id="R1", description="Framework-agnostic tracing", priority=Priority.high)],
        "raw_results": raw_results if raw_results is not None else {},
    }
    return state


_MOCK_LLM_EVIDENCE_RESPONSE = {
    "evidence": [
        {
            "claim": "LangSmith supports framework-agnostic tracing via OpenTelemetry",
            "source_url": "https://docs.langsmith.com/tracing",
            "source_name": "LangSmith Docs",
            "source_type": "official_docs",
            "content_date": "2025-01",
            "relevance": 0.9,
            "supports_requirement": True,
        },
        {
            "claim": "LangSmith tracing works with any Python framework",
            "source_url": "https://github.com/langchain-ai/langsmith-sdk",
            "source_name": "LangSmith SDK",
            "source_type": "github",
            "content_date": "2025-02",
            "relevance": 0.8,
            "supports_requirement": True,
        },
    ]
}


class TestExtractEvidence:
    @pytest.mark.asyncio
    async def test_correct_evidence_objects_extracted(self) -> None:
        """LLM response is parsed into correct Evidence objects."""
        raw_results = {
            "LangSmith:R1:0": [
                {"url": "https://docs.langsmith.com/tracing", "title": "Tracing", "content": "tracing info"},
            ],
            "LangSmith:R1:1": [
                {"url": "https://github.com/langchain-ai/langsmith-sdk", "title": "SDK", "content": "sdk info"},
            ],
        }
        state = _make_evidence_state(raw_results=raw_results)

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=_mock_ai_message("{}"))

        mock_parser = AsyncMock()
        mock_parser.ainvoke = AsyncMock(return_value=_MOCK_LLM_EVIDENCE_RESPONSE)

        with (
            patch("app.graph.nodes.get_llm", return_value=mock_llm),
            patch("app.graph.nodes.JsonOutputParser", return_value=mock_parser),
        ):
            result = await extract_evidence(state)

        evidence = result["evidence"]
        assert "LangSmith" in evidence
        assert "R1" in evidence["LangSmith"]
        ev_list = evidence["LangSmith"]["R1"]
        assert len(ev_list) == 2
        assert isinstance(ev_list[0], Evidence)
        assert ev_list[0].claim == "LangSmith supports framework-agnostic tracing via OpenTelemetry"
        assert ev_list[0].source_type == SourceType.official_docs
        assert ev_list[0].relevance == 0.9
        assert ev_list[0].supports_requirement is True
        assert ev_list[1].source_type == SourceType.github

    @pytest.mark.asyncio
    async def test_empty_search_results_produce_empty_evidence(self) -> None:
        """When no raw_results exist for a pair, evidence list is empty (no error)."""
        state = _make_evidence_state(raw_results={})

        mock_llm = AsyncMock()
        mock_parser = AsyncMock()

        with (
            patch("app.graph.nodes.get_llm", return_value=mock_llm),
            patch("app.graph.nodes.JsonOutputParser", return_value=mock_parser),
        ):
            result = await extract_evidence(state)

        evidence = result["evidence"]
        assert evidence["LangSmith"]["R1"] == []
        # LLM should NOT have been called since there were no results
        mock_llm.ainvoke.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalid_llm_response_returns_empty(self) -> None:
        """When LLM raises an exception, evidence list is empty (graceful failure)."""
        raw_results = {
            "LangSmith:R1:0": [{"url": "https://example.com", "title": "Test", "content": "content"}],
        }
        state = _make_evidence_state(raw_results=raw_results)

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("LLM failure"))

        mock_parser = AsyncMock()

        with (
            patch("app.graph.nodes.get_llm", return_value=mock_llm),
            patch("app.graph.nodes.JsonOutputParser", return_value=mock_parser),
        ):
            result = await extract_evidence(state)

        evidence = result["evidence"]
        assert evidence["LangSmith"]["R1"] == []

    @pytest.mark.asyncio
    async def test_source_type_classified_correctly(self) -> None:
        """Valid SourceType enum values are correctly mapped."""
        raw_results = {
            "LangSmith:R1:0": [{"url": "https://example.com", "title": "T", "content": "c"}],
        }
        state = _make_evidence_state(raw_results=raw_results)

        all_types_response = {
            "evidence": [
                {
                    "claim": "claim1",
                    "source_url": "u1",
                    "source_name": "n1",
                    "source_type": "official_docs",
                    "relevance": 0.9,
                    "supports_requirement": True,
                },
                {
                    "claim": "claim2",
                    "source_url": "u2",
                    "source_name": "n2",
                    "source_type": "github",
                    "relevance": 0.8,
                    "supports_requirement": True,
                },
                {
                    "claim": "claim3",
                    "source_url": "u3",
                    "source_name": "n3",
                    "source_type": "comparison",
                    "relevance": 0.7,
                    "supports_requirement": False,
                },
                {
                    "claim": "claim4",
                    "source_url": "u4",
                    "source_name": "n4",
                    "source_type": "blog",
                    "relevance": 0.6,
                    "supports_requirement": False,
                },
                {
                    "claim": "claim5",
                    "source_url": "u5",
                    "source_name": "n5",
                    "source_type": "community",
                    "relevance": 0.5,
                    "supports_requirement": False,
                },
                {
                    "claim": "claim6",
                    "source_url": "u6",
                    "source_name": "n6",
                    "source_type": "invalid_type",
                    "relevance": 0.4,
                    "supports_requirement": False,
                },
            ]
        }

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=_mock_ai_message("{}"))

        mock_parser = AsyncMock()
        mock_parser.ainvoke = AsyncMock(return_value=all_types_response)

        with (
            patch("app.graph.nodes.get_llm", return_value=mock_llm),
            patch("app.graph.nodes.JsonOutputParser", return_value=mock_parser),
        ):
            result = await extract_evidence(state)

        ev_list = result["evidence"]["LangSmith"]["R1"]
        assert ev_list[0].source_type == SourceType.official_docs
        assert ev_list[1].source_type == SourceType.github
        assert ev_list[2].source_type == SourceType.comparison
        assert ev_list[3].source_type == SourceType.blog
        assert ev_list[4].source_type == SourceType.community
        # Invalid type falls back to community
        assert ev_list[5].source_type == SourceType.community

    @pytest.mark.asyncio
    async def test_returns_partial_state_dict(self) -> None:
        """Node must return dict with only 'evidence' key (LangGraph pattern)."""
        state = _make_evidence_state(raw_results={})

        mock_llm = AsyncMock()
        mock_parser = AsyncMock()

        with (
            patch("app.graph.nodes.get_llm", return_value=mock_llm),
            patch("app.graph.nodes.JsonOutputParser", return_value=mock_parser),
        ):
            result = await extract_evidence(state)

        assert isinstance(result, dict)
        assert list(result.keys()) == ["evidence"]

    @pytest.mark.asyncio
    async def test_content_truncated_to_2000_chars(self) -> None:
        """Content in formatted results is truncated to 2000 characters."""
        long_content = "x" * 5000
        raw_results = {
            "LangSmith:R1:0": [
                {"url": "https://example.com", "title": "T", "content": long_content},
            ],
        }

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=_mock_ai_message("{}"))

        mock_parser = AsyncMock()
        mock_parser.ainvoke = AsyncMock(return_value={"evidence": []})

        req = Requirement(id="R1", description="Framework-agnostic tracing", priority=Priority.high)
        parser_instance = mock_parser

        # Provide a minimal state dict with no progress_queue
        mock_state: dict = {"vendors": [], "requirements": [], "progress_queue": None}
        _vendor, _req_id, _ev_list = await _extract_evidence_for_pair(
            mock_llm, parser_instance, "LangSmith", req, raw_results, mock_state
        )

        # Verify the LLM was called and the content in the message is truncated
        call_args = mock_llm.ainvoke.call_args[0][0]
        user_msg_content = call_args[1].content
        # The formatted content should contain truncated text (2000 x's, not 5000)
        assert "x" * 2000 in user_msg_content
        assert "x" * 2001 not in user_msg_content


# ---------------------------------------------------------------------------
# Story 2.2 - assess_capabilities tests
# ---------------------------------------------------------------------------

from app.graph.nodes import assess_capabilities  # noqa: E402
from app.models import CapabilityLevel, LLMAssessment, MaturityLevel  # noqa: E402


def _make_evidence(
    relevance: float = 0.8,
    claim: str = "Vendor supports this feature",
    supports: bool = True,
) -> Evidence:
    """Create a test Evidence object."""
    return Evidence(
        claim=claim,
        source_url="https://example.com/doc",
        source_name="Example Docs",
        source_type=SourceType.official_docs,
        content_date="2025-01",
        relevance=relevance,
        supports_requirement=supports,
    )


def _make_assessment_state(
    vendors: list[str] | None = None,
    requirements: list[Requirement] | None = None,
    evidence: dict | None = None,
) -> ResearchState:
    """Create a minimal ResearchState for assessment tests."""
    state: ResearchState = {
        "vendors": vendors if vendors is not None else VENDORS,
        "requirements": requirements if requirements is not None else REQUIREMENTS,
        "evidence": evidence if evidence is not None else {},
    }
    return state


_MOCK_LLM_ASSESSMENT_RESPONSE = {
    "capability_level": "full",
    "capability_details": "Fully supported with native integration",
    "maturity": "ga",
    "limitations": ["Requires v2.0+"],
    "supports_requirement": True,
}


class TestAssessCapabilities:
    @pytest.mark.asyncio
    async def test_all_24_pairs_assessed(self) -> None:
        """4 vendors x 6 requirements = 24 assessment pairs."""
        # Build evidence so every pair has at least one relevant item
        evidence: dict[str, dict[str, list[Evidence]]] = {}
        for vendor in VENDORS:
            evidence[vendor] = {}
            for req in REQUIREMENTS:
                evidence[vendor][req.id] = [_make_evidence()]

        state = _make_assessment_state(evidence=evidence)

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=_mock_ai_message("{}"))

        mock_parser = AsyncMock()
        mock_parser.ainvoke = AsyncMock(return_value=_MOCK_LLM_ASSESSMENT_RESPONSE)

        with (
            patch("app.graph.nodes.get_llm", return_value=mock_llm),
            patch("app.graph.nodes.JsonOutputParser", return_value=mock_parser),
        ):
            result = await assess_capabilities(state)

        assessments = result["assessments"]
        total_pairs = sum(len(reqs) for reqs in assessments.values())
        assert total_pairs == 24

        for vendor in VENDORS:
            assert vendor in assessments
            for req in REQUIREMENTS:
                assert req.id in assessments[vendor]

    @pytest.mark.asyncio
    async def test_fallback_on_llm_exception(self) -> None:
        """When LLM raises an exception, the default assessment is used."""
        evidence = {"LangSmith": {"R1": [_make_evidence()]}}
        state = _make_assessment_state(
            vendors=["LangSmith"],
            requirements=[Requirement(id="R1", description="Framework-agnostic tracing", priority=Priority.high)],
            evidence=evidence,
        )

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("LLM failure"))

        mock_parser = AsyncMock()

        with (
            patch("app.graph.nodes.get_llm", return_value=mock_llm),
            patch("app.graph.nodes.JsonOutputParser", return_value=mock_parser),
        ):
            result = await assess_capabilities(state)

        assessment = result["assessments"]["LangSmith"]["R1"]
        assert assessment.capability_level == CapabilityLevel.unknown
        assert assessment.capability_details == "Assessment failed"
        assert assessment.maturity == MaturityLevel.unknown
        assert assessment.supports_requirement is False

    @pytest.mark.asyncio
    async def test_low_relevance_evidence_filtered(self) -> None:
        """Evidence with relevance < 0.3 is filtered out; if none remain, default is used."""
        low_relevance_evidence = [_make_evidence(relevance=0.1), _make_evidence(relevance=0.2)]
        evidence = {"LangSmith": {"R1": low_relevance_evidence}}
        state = _make_assessment_state(
            vendors=["LangSmith"],
            requirements=[Requirement(id="R1", description="Framework-agnostic tracing", priority=Priority.high)],
            evidence=evidence,
        )

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=_mock_ai_message("{}"))

        mock_parser = AsyncMock()
        mock_parser.ainvoke = AsyncMock(return_value=_MOCK_LLM_ASSESSMENT_RESPONSE)

        with (
            patch("app.graph.nodes.get_llm", return_value=mock_llm),
            patch("app.graph.nodes.JsonOutputParser", return_value=mock_parser),
        ):
            result = await assess_capabilities(state)

        assessment = result["assessments"]["LangSmith"]["R1"]
        # Should be default since all evidence was below 0.3
        assert assessment.capability_level == CapabilityLevel.unknown
        assert assessment.capability_details == "Assessment failed"
        # LLM should NOT have been called
        mock_llm.ainvoke.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_partial_state_dict(self) -> None:
        """Node must return dict with only 'assessments' key (LangGraph pattern)."""
        state = _make_assessment_state(vendors=["LangSmith"], requirements=[], evidence={})

        with (
            patch("app.graph.nodes.get_llm"),
            patch("app.graph.nodes.JsonOutputParser"),
        ):
            result = await assess_capabilities(state)

        assert isinstance(result, dict)
        assert list(result.keys()) == ["assessments"]

    @pytest.mark.asyncio
    async def test_valid_llm_assessment_structure(self) -> None:
        """Result contains valid LLMAssessment objects with correct fields."""
        evidence = {"LangSmith": {"R1": [_make_evidence()]}}
        state = _make_assessment_state(
            vendors=["LangSmith"],
            requirements=[Requirement(id="R1", description="Framework-agnostic tracing", priority=Priority.high)],
            evidence=evidence,
        )

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=_mock_ai_message("{}"))

        mock_parser = AsyncMock()
        mock_parser.ainvoke = AsyncMock(return_value=_MOCK_LLM_ASSESSMENT_RESPONSE)

        with (
            patch("app.graph.nodes.get_llm", return_value=mock_llm),
            patch("app.graph.nodes.JsonOutputParser", return_value=mock_parser),
        ):
            result = await assess_capabilities(state)

        assessment = result["assessments"]["LangSmith"]["R1"]
        assert isinstance(assessment, LLMAssessment)
        assert assessment.capability_level == CapabilityLevel.full
        assert assessment.capability_details == "Fully supported with native integration"
        assert assessment.maturity == MaturityLevel.ga
        assert assessment.limitations == ["Requires v2.0+"]
        assert assessment.supports_requirement is True


# ---------------------------------------------------------------------------
# Story 4.4 - generate_summary tests
# ---------------------------------------------------------------------------

from app.graph.nodes import generate_summary  # noqa: E402
from app.models import ScoreResult, VendorRanking  # noqa: E402


def _make_summary_state(
    vendors: list[str] | None = None,
    requirements: list[Requirement] | None = None,
    rankings: list[VendorRanking] | None = None,
    scores: dict | None = None,
) -> ResearchState:
    """Create a minimal ResearchState for summary generation tests."""
    state: ResearchState = {
        "vendors": vendors if vendors is not None else ["LangSmith", "Langfuse"],
        "requirements": requirements
        if requirements is not None
        else [
            Requirement(id="R1", description="Framework-agnostic tracing", priority=Priority.high),
            Requirement(id="R2", description="Self-hosting support", priority=Priority.high),
        ],
        "rankings": rankings
        if rankings is not None
        else [
            VendorRanking(vendor="LangSmith", overall_score=82.5, rank=1),
            VendorRanking(vendor="Langfuse", overall_score=78.0, rank=2),
        ],
        "scores": scores
        if scores is not None
        else {
            "LangSmith": {
                "R1": ScoreResult(
                    score=8.5,
                    confidence=0.9,
                    capability_level=CapabilityLevel.full,
                    maturity=MaturityLevel.ga,
                    justification="Strong tracing support",
                    limitations=[],
                    evidence=[],
                ),
                "R2": ScoreResult(
                    score=6.0,
                    confidence=0.7,
                    capability_level=CapabilityLevel.partial,
                    maturity=MaturityLevel.ga,
                    justification="Limited self-hosting",
                    limitations=["Cloud-only primary"],
                    evidence=[],
                ),
            },
            "Langfuse": {
                "R1": ScoreResult(
                    score=7.5,
                    confidence=0.85,
                    capability_level=CapabilityLevel.full,
                    maturity=MaturityLevel.ga,
                    justification="Good tracing",
                    limitations=[],
                    evidence=[],
                ),
                "R2": ScoreResult(
                    score=9.0,
                    confidence=0.95,
                    capability_level=CapabilityLevel.full,
                    maturity=MaturityLevel.ga,
                    justification="Full self-hosting",
                    limitations=[],
                    evidence=[],
                ),
            },
        },
    }
    return state


class TestGenerateSummary:
    @pytest.mark.asyncio
    async def test_returns_partial_state_dict(self) -> None:
        """generate_summary returns {'summary': str} partial state dict."""
        state = _make_summary_state()

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=_mock_ai_message("This is an executive summary of the evaluation."))

        with patch("app.graph.nodes.get_llm", return_value=mock_llm):
            result = await generate_summary(state)

        assert isinstance(result, dict)
        assert list(result.keys()) == ["summary"]
        assert isinstance(result["summary"], str)

    @pytest.mark.asyncio
    async def test_fallback_on_llm_failure(self) -> None:
        """When LLM raises an exception, fallback text is returned."""
        state = _make_summary_state()

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("LLM failure"))

        with patch("app.graph.nodes.get_llm", return_value=mock_llm):
            result = await generate_summary(state)

        assert "summary" in result
        assert result["summary"] == "Executive summary not available \u2014 see matrix for detailed scores."

    @pytest.mark.asyncio
    async def test_summary_is_nonempty_on_success(self) -> None:
        """Summary is a non-empty string when LLM succeeds."""
        state = _make_summary_state()

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(
            return_value=_mock_ai_message(
                "Based on our evaluation, LangSmith leads with an overall score of 82.5. "
                "Langfuse follows closely at 78.0, excelling in self-hosting capabilities."
            )
        )

        with patch("app.graph.nodes.get_llm", return_value=mock_llm):
            result = await generate_summary(state)

        assert len(result["summary"]) > 0
        assert "LangSmith" in result["summary"]
