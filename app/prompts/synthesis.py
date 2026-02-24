"""Prompt templates for executive summary generation."""

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
