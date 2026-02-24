"""LangGraph state definition for the research pipeline."""

import asyncio
from typing import TypedDict

from app.models import Evidence, LLMAssessment, Requirement, ScoreResult, VendorRanking


class ResearchState(TypedDict, total=False):
    """State object for the LangGraph research pipeline."""

    job_id: str
    vendors: list[str]
    requirements: list[Requirement]
    queries: dict[str, list[str]]  # vendor -> list of queries
    raw_results: dict[str, list[dict]]  # vendor -> search results
    evidence: dict[str, dict[str, list[Evidence]]]  # vendor -> req_id -> evidence
    assessments: dict[str, dict[str, LLMAssessment]]  # vendor -> req_id -> assessment
    scores: dict[str, dict[str, ScoreResult]]  # vendor -> req_id -> score
    rankings: list[VendorRanking]
    summary: str
    iteration: int
    gaps: list[dict]
    progress_queue: asyncio.Queue  # type: ignore[type-arg]


def build_initial_state(job_id: str, queue: asyncio.Queue) -> ResearchState:  # type: ignore[type-arg]
    """Create the initial ResearchState for a new pipeline run."""
    from app.config import REQUIREMENTS, VENDORS

    return ResearchState(
        job_id=job_id,
        vendors=VENDORS,
        requirements=REQUIREMENTS,
        queries={},
        raw_results={},
        evidence={},
        assessments={},
        scores={},
        rankings=[],
        summary="",
        iteration=0,
        gaps=[],
        progress_queue=queue,
    )
