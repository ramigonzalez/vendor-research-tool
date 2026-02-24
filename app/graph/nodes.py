"""LangGraph node functions for the research pipeline."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser

from app.graph.state import ResearchState
from app.models import Requirement
from app.prompts.research import QUERY_GENERATION_SYSTEM_PROMPT, QUERY_GENERATION_USER_TEMPLATE

logger = logging.getLogger(__name__)


def _build_fallback_queries(vendor: str, requirement_desc: str) -> list[str]:
    """Build fallback queries when LLM response is invalid or unparseable."""
    return [
        f"{vendor} {requirement_desc} official documentation site:docs.{vendor.lower()}.com",
        f"{vendor} {requirement_desc} comparison review 2024",
    ]


async def _generate_query_pair(
    llm: ChatAnthropic,
    parser: JsonOutputParser,
    vendor: str,
    requirement: Requirement,
) -> tuple[str, list[str]]:
    """Generate a pair of search queries for a single vendor-requirement combination.

    Returns a tuple of (key, queries) where key is 'vendor:req_id'.
    """
    key = f"{vendor}:{requirement.id}"
    user_content = QUERY_GENERATION_USER_TEMPLATE.format(
        vendor=vendor,
        requirement=requirement.description,
        priority=requirement.priority.value,
    )

    try:
        messages = [
            SystemMessage(content=QUERY_GENERATION_SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ]
        result = await llm.ainvoke(messages)
        parsed: dict[str, Any] = await parser.ainvoke(result)

        query_1 = parsed.get("query_1", "")
        query_2 = parsed.get("query_2", "")

        if not query_1 or not query_2:
            logger.warning("Incomplete LLM response for %s, using fallback queries", key)
            return key, _build_fallback_queries(vendor, requirement.description)

        return key, [str(query_1), str(query_2)]

    except Exception:
        logger.warning("Failed to parse LLM response for %s, using fallback queries", key, exc_info=True)
        return key, _build_fallback_queries(vendor, requirement.description)


async def generate_queries(state: ResearchState) -> dict:
    """LangGraph node: generate search queries for all vendor-requirement pairs.

    Takes the current research state, generates two search queries per
    vendor-requirement combination using an LLM, and returns a partial
    state update with the queries dict.
    """
    vendors: list[str] = state.get("vendors", [])
    requirements: list[Requirement] = state.get("requirements", [])

    llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0)  # type: ignore[call-arg]
    parser = JsonOutputParser()

    tasks = [_generate_query_pair(llm, parser, vendor, req) for vendor in vendors for req in requirements]

    results = await asyncio.gather(*tasks)

    queries: dict[str, list[str]] = {}
    for key, query_list in results:
        queries[key] = query_list

    return {"queries": queries}


# ---------------------------------------------------------------------------
# Story 1.2 - Parallel Search Execution
# ---------------------------------------------------------------------------

from tavily import AsyncTavilyClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.graph.progress import emit_progress  # noqa: E402


async def execute_searches(state: ResearchState) -> dict:
    """LangGraph node: execute all Tavily searches concurrently with rate limiting."""
    client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)
    semaphore = asyncio.Semaphore(5)
    queries = state.get("queries", {})
    completed_count = 0
    total_searches = sum(len(qs) for qs in queries.values())

    raw_results: dict[str, list[dict]] = {}

    async def search_with_limit(key: str, query_idx: int, query: str) -> tuple[str, list[dict]]:
        nonlocal completed_count
        result_key = f"{key}:{query_idx}"
        async with semaphore:
            try:
                results = await client.search(
                    query=query,
                    max_results=5,
                    search_depth="advanced",
                    include_raw_content=False,
                )
                completed_count += 1
                if completed_count % 5 == 0:
                    pct = 10 + int(35 * completed_count / max(total_searches, 1))
                    await emit_progress(state, "research", pct, f"Searching... ({completed_count}/{total_searches})")
                return result_key, results.get("results", [])
            except Exception as e:
                logger.warning("Search failed for %s: %s", result_key, e)
                completed_count += 1
                return result_key, []

    tasks = []
    for key, query_list in queries.items():
        for idx, query in enumerate(query_list):
            tasks.append(search_with_limit(key, idx, query))

    start_time = asyncio.get_event_loop().time()
    results = await asyncio.gather(*tasks)
    elapsed = asyncio.get_event_loop().time() - start_time
    logger.info("Search phase completed in %.1fs (%d searches)", elapsed, len(tasks))

    for result_key, result_list in results:
        raw_results[result_key] = result_list

    await emit_progress(state, "research", 45, "Search complete, extracting evidence...")
    return {"raw_results": raw_results}


# ---------------------------------------------------------------------------
# Story 1.3 - Structured Evidence Extraction
# ---------------------------------------------------------------------------

from app.models import Evidence, SourceType  # noqa: E402
from app.prompts.extraction import (  # noqa: E402
    EVIDENCE_EXTRACTION_SYSTEM_PROMPT,
    EVIDENCE_EXTRACTION_USER_TEMPLATE,
)


async def _extract_evidence_for_pair(
    llm: ChatAnthropic,
    parser: JsonOutputParser,
    vendor: str,
    requirement: Requirement,
    raw_results: dict[str, list[dict]],
) -> tuple[str, str, list[Evidence]]:
    """Extract evidence for a single vendor-requirement pair."""
    req_id = requirement.id

    # Combine results from both query indices
    combined_results: list[dict] = []
    for idx in range(2):
        key = f"{vendor}:{req_id}:{idx}"
        combined_results.extend(raw_results.get(key, []))

    if not combined_results:
        return vendor, req_id, []

    # Format results, truncating content to 2000 chars
    formatted: list[str] = []
    for i, r in enumerate(combined_results[:10]):  # Cap at 10 results
        content = str(r.get("content", ""))[:2000]
        formatted.append(
            f"Result {i + 1}:\n"
            f"URL: {r.get('url', '')}\n"
            f"Title: {r.get('title', '')}\n"
            f"Content: {content}\n"
            f"Date: {r.get('published_date', 'unknown')}\n"
        )
    formatted_str = "\n".join(formatted)

    user_content = EVIDENCE_EXTRACTION_USER_TEMPLATE.format(
        vendor=vendor,
        requirement=requirement.description,
        priority=requirement.priority.value,
        formatted_results=formatted_str,
    )

    try:
        messages = [
            SystemMessage(content=EVIDENCE_EXTRACTION_SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ]
        result = await llm.ainvoke(messages)
        parsed = await parser.ainvoke(result)

        evidence_list: list[Evidence] = []
        for e in parsed.get("evidence", []):
            try:
                source_type = SourceType(e.get("source_type", "community"))
            except ValueError:
                source_type = SourceType.community
            evidence_list.append(
                Evidence(
                    claim=str(e.get("claim", "")),
                    source_url=str(e.get("source_url", "")),
                    source_name=str(e.get("source_name", "")),
                    source_type=source_type,
                    content_date=e.get("content_date"),
                    relevance=float(e.get("relevance", 0.5)),
                    supports_requirement=bool(e.get("supports_requirement", False)),
                )
            )
        return vendor, req_id, evidence_list
    except Exception:
        logger.warning(
            "Evidence extraction failed for %s:%s, returning empty",
            vendor,
            req_id,
            exc_info=True,
        )
        return vendor, req_id, []


async def extract_evidence(state: ResearchState) -> dict:
    """LangGraph node: extract structured Evidence from raw search results."""
    vendors = state.get("vendors", [])
    requirements = state.get("requirements", [])
    raw_results = state.get("raw_results", {})

    llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0)  # type: ignore[call-arg]
    parser = JsonOutputParser()

    tasks = [
        _extract_evidence_for_pair(llm, parser, vendor, req, raw_results) for vendor in vendors for req in requirements
    ]

    results = await asyncio.gather(*tasks)

    evidence: dict[str, dict[str, list[Evidence]]] = {}
    for vendor, req_id, ev_list in results:
        if vendor not in evidence:
            evidence[vendor] = {}
        evidence[vendor][req_id] = ev_list

    await emit_progress(state, "research", 50, "Evidence extraction complete")
    return {"evidence": evidence}
