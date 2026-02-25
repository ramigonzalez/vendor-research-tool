"""Complete LangGraph pipeline assembly for the research workflow."""

from __future__ import annotations

import logging
import time
from typing import cast

from langgraph.graph import END, StateGraph

from app.graph.nodes import (
    assess_capabilities,
    compute_rankings,
    compute_scores,
    execute_searches,
    extract_evidence,
    generate_queries,
    generate_summary,
    prepare_gap_filling,
    should_continue_research,
)
from app.graph.progress import emit_completed, emit_error, emit_progress
from app.graph.state import ResearchState
from app.models import JobStatus
from app.repository import ResearchRepository

logger = logging.getLogger(__name__)


def build_research_graph() -> StateGraph:
    """Build the complete research pipeline graph."""
    graph = StateGraph(ResearchState)

    # Register all nodes
    graph.add_node("generate_queries", generate_queries)
    graph.add_node("execute_searches", execute_searches)
    graph.add_node("extract_evidence", extract_evidence)
    graph.add_node("prepare_gap_filling", prepare_gap_filling)
    graph.add_node("assess_capabilities", assess_capabilities)
    graph.add_node("compute_scores", compute_scores)
    graph.add_node("compute_rankings", compute_rankings)
    graph.add_node("generate_summary", generate_summary)

    # Set entry point
    graph.set_entry_point("generate_queries")

    # Wire edges
    graph.add_edge("generate_queries", "execute_searches")
    graph.add_edge("execute_searches", "extract_evidence")

    # Conditional: gap analysis loop
    graph.add_conditional_edges(
        "extract_evidence",
        should_continue_research,
        {
            "continue": "prepare_gap_filling",
            "proceed": "assess_capabilities",
        },
    )
    graph.add_edge("prepare_gap_filling", "execute_searches")

    # Scoring pipeline
    graph.add_edge("assess_capabilities", "compute_scores")
    graph.add_edge("compute_scores", "compute_rankings")
    graph.add_edge("compute_rankings", "generate_summary")
    graph.add_edge("generate_summary", END)

    return graph


async def run_pipeline(state: ResearchState, repo: ResearchRepository) -> ResearchState:
    """Execute the complete research pipeline."""
    graph = build_research_graph()
    compiled = graph.compile()

    job_id = state.get("job_id", "")

    try:
        logger.info("Pipeline started job_id=%s", job_id)
        start_time = time.monotonic()
        await emit_progress(state, "research", 5, "Starting research pipeline...")

        # Run the graph
        final_state = await compiled.ainvoke(state)

        # Persist final results
        summary = final_state.get("summary", "")
        rankings = final_state.get("rankings", [])
        await repo.save_final_results(job_id, summary, rankings)

        # Save scores to repository
        scores = final_state.get("scores", {})
        score_count = 0
        for vendor, req_scores in scores.items():
            for req_id, score_result in req_scores.items():
                await repo.save_score(job_id, vendor, req_id, score_result)
                score_count += 1

        # Save evidence to repository
        evidence = final_state.get("evidence", {})
        evidence_count = 0
        for vendor, req_evidence in evidence.items():
            for req_id, ev_list in req_evidence.items():
                await repo.save_evidence(job_id, vendor, req_id, ev_list)
                evidence_count += len(ev_list)

        logger.info(
            "Results persisted job_id=%s scores=%d evidence=%d",
            job_id, score_count, evidence_count,
        )

        elapsed = time.monotonic() - start_time
        logger.info("Pipeline completed job_id=%s elapsed=%.1fs", job_id, elapsed)
        await emit_completed(state, {})
        return cast(ResearchState, final_state)

    except Exception as e:
        logger.error("Pipeline failed: %s", e, exc_info=True)
        await emit_error(state, str(e))
        await repo.update_job_status(job_id, JobStatus.failed, 100, str(e))
        raise
