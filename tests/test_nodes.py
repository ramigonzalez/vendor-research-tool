"""Tests for LangGraph node functions."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.graph.nodes import _build_fallback_queries, generate_queries
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
            patch("app.graph.nodes.ChatAnthropic", return_value=mock_llm),
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
            patch("app.graph.nodes.ChatAnthropic", return_value=mock_llm),
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
            patch("app.graph.nodes.ChatAnthropic", return_value=mock_llm),
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
            patch("app.graph.nodes.ChatAnthropic", return_value=mock_llm),
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
            patch("app.graph.nodes.ChatAnthropic"),
            patch("app.graph.nodes.JsonOutputParser"),
        ):
            result = await generate_queries(state)

        assert result == {"queries": {}}

    @pytest.mark.asyncio
    async def test_empty_requirements(self) -> None:
        """When no requirements provided, returns empty queries dict."""
        state = _make_state(vendors=VENDORS, requirements=[])

        with (
            patch("app.graph.nodes.ChatAnthropic"),
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
            patch("app.graph.nodes.ChatAnthropic", return_value=mock_llm),
            patch("app.graph.nodes.JsonOutputParser", return_value=mock_parser),
        ):
            result = await generate_queries(state)

        queries = result["queries"]
        for key, query_list in queries.items():
            assert isinstance(key, str)
            assert isinstance(query_list, list)
            for q in query_list:
                assert isinstance(q, str)
