"""Prompt templates for executive summary generation."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models import Requirement, ScoreResult, VendorRanking

SUMMARY_GENERATION_SYSTEM_PROMPT = """You are writing an executive summary for an LLM observability platform evaluation.

Write a 3-4 paragraph executive summary. Include:
1. Overall recommendation (which vendor and why)
2. Key differentiators between top 2 vendors
3. Notable strengths/weaknesses per vendor
4. Confidence gaps that warrant further investigation

Write in prose (no bullet points). Be specific and cite evidence-based scores.
Max 400 words."""

SUMMARY_GENERATION_USER_TEMPLATE = """Evaluation Results:
- Vendors evaluated: {vendors}
- Requirements (with priorities): {requirements}
- Rankings: {rankings}
- Score highlights: {score_highlights}
"""

# ---------------------------------------------------------------------------
# Format-specific system prompts (Story 14.1)
# ---------------------------------------------------------------------------

SUMMARY_FORMAT_PROMPTS: dict[str, str] = {
    "formal": SUMMARY_GENERATION_SYSTEM_PROMPT,
    "informal": """You are writing an executive summary for an LLM observability platform evaluation.

Write a 3-4 paragraph executive summary in a conversational, accessible tone. Include:
1. Overall recommendation (which vendor and why)
2. Key differentiators between top 2 vendors
3. Notable strengths/weaknesses per vendor
4. Confidence gaps that warrant further investigation

Use approachable language and analogies where helpful. Keep it readable and engaging.
Max 400 words.""",
    "concise": """You are writing an executive summary for an LLM observability platform evaluation.

Write a 1-2 short paragraph executive summary covering only the key takeaways:
1. Top recommendation with rationale
2. Critical differentiators
3. Any major red flags

Be extremely brief and focused. No filler.
Max 200 words.""",
    "direct": """You are writing an executive summary for an LLM observability platform evaluation.

Write the summary as bullet-point actionable recommendations. No prose. Include:
- Top recommendation and why
- Key differentiator per vendor (one bullet each)
- Critical limitations or gaps to investigate
- Clear next steps

Be specific, cite scores, and keep each bullet to one line.
Max 300 words.""",
}


def build_summary_context(
    vendors: list[str],
    requirements: list[Requirement],
    rankings: list[VendorRanking],
    scores: dict[str, dict[str, ScoreResult]],
) -> str:
    """Build the user-facing context string for summary generation.

    Extracts the top-3 requirement scores per vendor (max 12 total highlights)
    and formats them alongside vendors, requirements, and rankings into the
    standard user template.

    This is shared by the pipeline node (generate_summary) and the
    regenerate-summary API endpoint.
    """
    highlights: list[str] = []
    for r in rankings:
        vendor = r.vendor
        vendor_scores = scores.get(vendor, {})
        top_reqs = sorted(vendor_scores.items(), key=lambda x: -x[1].score)[:3]
        for req_id, sr in top_reqs:
            highlights.append(f"{vendor} - {req_id}: {sr.score:.1f}/10 (confidence: {sr.confidence:.2f})")

    req_summary = ", ".join(f"{r.id}: {r.description} ({r.priority.value})" for r in requirements)
    rank_summary = ", ".join(f"#{r.rank} {r.vendor} ({r.overall_score:.1f})" for r in rankings)

    return SUMMARY_GENERATION_USER_TEMPLATE.format(
        vendors=", ".join(vendors),
        requirements=req_summary,
        rankings=rank_summary,
        score_highlights="\n".join(highlights[:12]),
    )
