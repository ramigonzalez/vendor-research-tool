"""Optional integration test for OpenRouter.

Skipped automatically when OPENROUTER_API_KEY is not set.
Run manually with: pytest tests/test_openrouter_integration.py -v

Manual smoke-test procedure:
1. Set OPENROUTER_API_KEY in .env
2. Set LLM_PROVIDER=openrouter and LLM_MODEL=meta-llama/llama-3.3-70b-instruct:free
3. Run: pytest tests/test_openrouter_integration.py -v
4. Or start the server and run a full research pipeline via the UI

Known compatible free OpenRouter models:
- meta-llama/llama-3.3-70b-instruct:free  (recommended — best JSON output)
- google/gemma-2-9b-it:free               (smaller, less reliable JSON)
- mistralai/mistral-7b-instruct:free      (basic, may struggle with structured output)

Note: Free models have rate limits and may produce less reliable JSON for
the structured prompts used in evidence extraction and assessment.
"""

from __future__ import annotations

import os

import pytest

requires_openrouter = pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY"),
    reason="OPENROUTER_API_KEY not set",
)


@requires_openrouter
@pytest.mark.asyncio
async def test_openrouter_basic_completion() -> None:
    """Verify OpenRouter returns a response for a simple prompt."""
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model="meta-llama/llama-3.3-70b-instruct:free",
        temperature=0,
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )
    result = await llm.ainvoke("Reply with exactly: hello")
    assert result.content  # non-empty response


@requires_openrouter
@pytest.mark.asyncio
async def test_openrouter_json_output() -> None:
    """Verify OpenRouter model can produce parseable JSON."""
    import json

    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model="meta-llama/llama-3.3-70b-instruct:free",
        temperature=0,
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )
    result = await llm.ainvoke(
        'Return a JSON object with keys "query_1" and "query_2", each containing a search query string. '
        "Output only valid JSON, no other text."
    )
    parsed = json.loads(str(result.content))
    assert "query_1" in parsed
    assert "query_2" in parsed
