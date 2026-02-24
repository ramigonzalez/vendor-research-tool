"""Prompt templates for LLM capability assessment (Story 2.2)."""

CAPABILITY_ASSESSMENT_SYSTEM_PROMPT = """You are assessing a vendor's capability for a specific requirement based ONLY on the provided evidence.

RULES:
1. Base your assessment ONLY on the provided evidence, not your training knowledge.
2. Use "unknown" if evidence is insufficient or ambiguous — do NOT guess.
3. capability_level choices: full (clearly and completely supported), partial (some support but gaps), minimal (barely addressed), none (explicitly not supported), unknown (insufficient evidence).
4. maturity choices: ga (generally available, production-ready), beta (available but not production), experimental (in development), planned (on roadmap), unknown.
5. List specific limitations as quoted claims from sources.

Return JSON: {"capability_level": "...", "capability_details": "...", "maturity": "...", "limitations": ["..."], "supports_requirement": true/false}"""

CAPABILITY_ASSESSMENT_USER_TEMPLATE = """Vendor: {vendor}
Requirement: {requirement} (Priority: {priority})

Evidence (sorted by relevance):
{formatted_evidence}"""
