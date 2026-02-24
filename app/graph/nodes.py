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
