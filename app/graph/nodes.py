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

from app.models import Evidence, GapType, SourceType  # noqa: E402
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


# ---------------------------------------------------------------------------
# Story 1.4 - Evidence Gap Analysis & Research Loop
# ---------------------------------------------------------------------------


def check_evidence_sufficiency(evidence: list[Evidence]) -> bool:
    """Check if evidence meets minimum quality thresholds."""
    if len(evidence) < 2:
        return False
    has_authoritative = any(e.source_type in (SourceType.official_docs, SourceType.github) for e in evidence)
    if not has_authoritative:
        return False
    has_relevant = any(e.relevance >= 0.5 for e in evidence)
    return has_relevant


def diagnose_gap(evidence: list[Evidence]) -> GapType:
    """Classify the type of evidence gap."""
    if not evidence:
        return GapType.no_evidence
    if not any(e.source_type in (SourceType.official_docs, SourceType.github) for e in evidence):
        return GapType.no_authoritative_source
    if not any(e.relevance >= 0.5 for e in evidence):
        return GapType.low_relevance
    return GapType.insufficient_count


def find_evidence_gaps(state: ResearchState) -> list[tuple[str, str]]:
    """Find vendor-requirement pairs that need more evidence."""
    evidence = state.get("evidence", {})
    gaps: list[tuple[str, str]] = []
    vendors = state.get("vendors", [])
    requirements = state.get("requirements", [])
    for vendor in vendors:
        for req in requirements:
            ev_list = evidence.get(vendor, {}).get(req.id, [])
            if not check_evidence_sufficiency(ev_list):
                gaps.append((vendor, req.id))
    return gaps


def should_continue_research(state: ResearchState) -> str:
    """LangGraph conditional edge: continue research or proceed to scoring."""
    iteration = state.get("iteration", 0)
    if iteration >= 2:
        return "proceed"
    gaps = find_evidence_gaps(state)
    if gaps:
        return "continue"
    return "proceed"


def generate_refined_queries(vendor: str, requirement_desc: str, gap_type: GapType) -> list[str]:
    """Generate refined queries based on gap type."""
    if gap_type == GapType.no_evidence:
        return [
            f"{vendor} {requirement_desc} overview features",
            f"{vendor} {requirement_desc} monitoring observability alternative terms",
        ]
    elif gap_type == GapType.no_authoritative_source:
        return [
            f"{vendor} {requirement_desc} site:github.com",
            f"{vendor} {requirement_desc} site:docs.{vendor.lower()}.com",
        ]
    elif gap_type == GapType.low_relevance:
        words = requirement_desc.split()[:3]
        specific = " ".join(words)
        return [
            f"{vendor} {specific} detailed documentation",
            f"{vendor} {specific} technical specification",
        ]
    else:  # insufficient_count
        return [
            f"{vendor} {requirement_desc} changelog release notes",
            f"{vendor} {requirement_desc} community discussion forum",
        ]


async def prepare_gap_filling(state: ResearchState) -> dict:
    """LangGraph node: prepare refined queries for gap-filling iteration."""
    gaps = find_evidence_gaps(state)
    requirements = state.get("requirements", [])
    req_map = {r.id: r for r in requirements}

    gap_metadata: list[dict] = []
    new_queries: dict[str, list[str]] = {}

    for vendor, req_id in gaps:
        ev_list = state.get("evidence", {}).get(vendor, {}).get(req_id, [])
        gap_type = diagnose_gap(ev_list)
        gap_metadata.append({"vendor": vendor, "requirement_id": req_id, "gap_type": gap_type.value})

        req = req_map.get(req_id)
        if req:
            key = f"{vendor}:{req_id}"
            new_queries[key] = generate_refined_queries(vendor, req.description, gap_type)

    iteration = state.get("iteration", 0)
    return {
        "queries": new_queries,
        "gaps": gap_metadata,
        "iteration": iteration + 1,
    }


# ---------------------------------------------------------------------------
# Story 2.2 - LLM Capability Assessment
# ---------------------------------------------------------------------------

from app.models import CapabilityLevel, LLMAssessment, MaturityLevel  # noqa: E402
from app.prompts.assessment import (  # noqa: E402
    CAPABILITY_ASSESSMENT_SYSTEM_PROMPT,
    CAPABILITY_ASSESSMENT_USER_TEMPLATE,
)


def _format_evidence_for_llm(evidence: list[Evidence]) -> str:
    """Format evidence list for LLM consumption, sorted by relevance."""
    lines: list[str] = []
    for i, e in enumerate(sorted(evidence, key=lambda x: -x.relevance)):
        lines.append(f"{i + 1}. [{e.source_type.value}] (relevance: {e.relevance:.2f})")
        lines.append(f"   Claim: {e.claim[:500]}")
        lines.append(f"   Source: {e.source_name} ({e.source_url[:80]})")
        lines.append(f"   Supports: {e.supports_requirement}")
    return "\n".join(lines)


_DEFAULT_ASSESSMENT = LLMAssessment(
    capability_level=CapabilityLevel.unknown,
    capability_details="Assessment failed",
    maturity=MaturityLevel.unknown,
    limitations=[],
    supports_requirement=False,
)


async def _assess_single_pair(
    llm: ChatAnthropic,
    parser: JsonOutputParser,
    vendor: str,
    requirement: Requirement,
    evidence: list[Evidence],
) -> tuple[str, str, LLMAssessment]:
    """Assess a single vendor-requirement pair."""
    req_id = requirement.id

    # Filter evidence to relevance >= 0.3
    filtered = [e for e in evidence if e.relevance >= 0.3]

    if not filtered:
        return vendor, req_id, _DEFAULT_ASSESSMENT

    formatted = _format_evidence_for_llm(filtered)
    user_content = CAPABILITY_ASSESSMENT_USER_TEMPLATE.format(
        vendor=vendor,
        requirement=requirement.description,
        priority=requirement.priority.value,
        formatted_evidence=formatted,
    )

    try:
        messages = [
            SystemMessage(content=CAPABILITY_ASSESSMENT_SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ]
        result = await llm.ainvoke(messages)
        parsed = await parser.ainvoke(result)

        assessment = LLMAssessment(
            capability_level=CapabilityLevel(parsed.get("capability_level", "unknown")),
            capability_details=str(parsed.get("capability_details", "")),
            maturity=MaturityLevel(parsed.get("maturity", "unknown")),
            limitations=list(parsed.get("limitations", [])),
            supports_requirement=bool(parsed.get("supports_requirement", False)),
        )
        return vendor, req_id, assessment
    except Exception:
        logger.warning("Assessment failed for %s:%s, using default", vendor, req_id, exc_info=True)
        return vendor, req_id, _DEFAULT_ASSESSMENT


async def assess_capabilities(state: ResearchState) -> dict:
    """LangGraph node: produce LLMAssessment for all vendor-requirement pairs."""
    vendors = state.get("vendors", [])
    requirements = state.get("requirements", [])
    evidence_map = state.get("evidence", {})

    llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0)  # type: ignore[call-arg]
    parser = JsonOutputParser()

    tasks = []
    for vendor in vendors:
        for req in requirements:
            ev = evidence_map.get(vendor, {}).get(req.id, [])
            tasks.append(_assess_single_pair(llm, parser, vendor, req, ev))

    results = await asyncio.gather(*tasks)

    assessments: dict[str, dict[str, LLMAssessment]] = {}
    for vendor, req_id, assessment in results:
        if vendor not in assessments:
            assessments[vendor] = {}
        assessments[vendor][req_id] = assessment

    await emit_progress(state, "scoring", 65, "Capability assessments complete")
    return {"assessments": assessments}


# ---------------------------------------------------------------------------
# Story 2.3 - Deterministic Score Computation
# ---------------------------------------------------------------------------

from app.models import ScoreResult  # noqa: E402
from app.scoring.engine import compute_confidence, compute_requirement_score  # noqa: E402


async def compute_scores(state: ResearchState) -> dict:
    """LangGraph node: compute scores for all vendor-requirement pairs."""
    vendors = state.get("vendors", [])
    requirements = state.get("requirements", [])
    evidence_map = state.get("evidence", {})
    assessments_map = state.get("assessments", {})

    scores: dict[str, dict[str, ScoreResult]] = {}

    for vendor in vendors:
        scores[vendor] = {}
        for req in requirements:
            ev = evidence_map.get(vendor, {}).get(req.id, [])
            assessment = assessments_map.get(vendor, {}).get(req.id, _DEFAULT_ASSESSMENT)

            score = compute_requirement_score(assessment, ev)
            confidence = compute_confidence(ev)

            scores[vendor][req.id] = ScoreResult(
                score=score,
                confidence=confidence,
                capability_level=assessment.capability_level,
                maturity=assessment.maturity,
                justification=assessment.capability_details,
                limitations=assessment.limitations,
                evidence=ev,
            )

    await emit_progress(state, "scoring", 80, "Score computation complete")
    return {"scores": scores}


# ---------------------------------------------------------------------------
# Story 2.5 - Weighted Vendor Ranking
# ---------------------------------------------------------------------------

from app.scoring.engine import compute_vendor_rankings  # noqa: E402


async def compute_rankings(state: ResearchState) -> dict:
    """LangGraph node: compute weighted vendor rankings."""
    scores = state.get("scores", {})
    requirements = state.get("requirements", [])
    rankings = compute_vendor_rankings(scores, requirements)
    await emit_progress(state, "scoring", 85, "Rankings computed")
    return {"rankings": rankings}


# ---------------------------------------------------------------------------
# Story 4.4 - Executive Summary Generation
# ---------------------------------------------------------------------------

from app.prompts.synthesis import SUMMARY_GENERATION_SYSTEM_PROMPT, SUMMARY_GENERATION_USER_TEMPLATE  # noqa: E402


async def generate_summary(state: ResearchState) -> dict:
    """LangGraph node: generate executive summary from evaluation results."""
    vendors = state.get("vendors", [])
    requirements = state.get("requirements", [])
    rankings = state.get("rankings", [])
    scores = state.get("scores", {})

    # Build score highlights
    highlights: list[str] = []
    for r in rankings:
        vendor = r.vendor
        vendor_scores = scores.get(vendor, {})
        top_reqs = sorted(vendor_scores.items(), key=lambda x: -x[1].score)[:3]
        for req_id, sr in top_reqs:
            highlights.append(f"{vendor} - {req_id}: {sr.score:.1f}/10 (confidence: {sr.confidence:.2f})")

    req_summary = ", ".join(f"{r.id}: {r.description} ({r.priority.value})" for r in requirements)
    rank_summary = ", ".join(f"#{r.rank} {r.vendor} ({r.overall_score:.1f})" for r in rankings)

    user_content = SUMMARY_GENERATION_USER_TEMPLATE.format(
        vendors=", ".join(vendors),
        requirements=req_summary,
        rankings=rank_summary,
        score_highlights="\n".join(highlights[:12]),
    )

    try:
        llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0)  # type: ignore[call-arg]
        messages = [
            SystemMessage(content=SUMMARY_GENERATION_SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ]
        result = await llm.ainvoke(messages)
        summary = str(result.content)
    except Exception:
        logger.warning("Summary generation failed, using fallback", exc_info=True)
        summary = "Executive summary not available — see matrix for detailed scores."

    await emit_progress(state, "synthesis", 95, "Summary generated")
    return {"summary": summary}
