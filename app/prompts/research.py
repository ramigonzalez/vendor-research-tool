"""Prompt templates for the research pipeline."""

QUERY_GENERATION_SYSTEM_PROMPT = """Generate 2 search queries for researching a vendor's capability.
Query 1: Target official documentation, GitHub, or product pages.
Query 2: Target comparisons, community discussions, or third-party reviews.
Return JSON: {"query_1": "...", "query_2": "..."}
Keep queries under 15 words. Be specific. Include year 2024 or 2025 in at least one query."""

QUERY_GENERATION_USER_TEMPLATE = "Vendor: {vendor}\nRequirement: {requirement}\nPriority: {priority}"
