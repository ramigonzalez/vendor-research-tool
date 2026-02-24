"""Tests for the get_llm() factory function."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.config import get_llm


def _patch_settings(**overrides: str | float):
    """Return a context manager that patches settings fields."""
    defaults = {
        "LLM_PROVIDER": "openrouter",
        "LLM_MODEL": "meta-llama/llama-3.3-70b-instruct:free",
        "LLM_TEMPERATURE": 0.0,
        "ANTHROPIC_API_KEY": "",
        "OPENAI_API_KEY": "",
        "OPENROUTER_API_KEY": "",
        "OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
    }
    defaults.update(overrides)

    class FakeSettings:
        pass

    s = FakeSettings()
    for k, v in defaults.items():
        setattr(s, k, v)
    return patch("app.config.settings", s)


class TestGetLlmOpenRouter:
    def test_default_returns_chatopenai_with_base_url(self) -> None:
        """Default (openrouter) returns ChatOpenAI with OpenRouter base_url."""
        with _patch_settings(OPENROUTER_API_KEY="sk-or-test"):
            llm = get_llm()
        from langchain_openai import ChatOpenAI

        assert isinstance(llm, ChatOpenAI)
        assert str(llm.openai_api_base) == "https://openrouter.ai/api/v1"

    def test_missing_key_raises(self) -> None:
        """OpenRouter with empty key raises ValueError."""
        with _patch_settings(OPENROUTER_API_KEY=""), pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
            get_llm()


class TestGetLlmAnthropic:
    def test_returns_chatanthropic(self) -> None:
        """Anthropic provider returns ChatAnthropic."""
        with _patch_settings(LLM_PROVIDER="anthropic", ANTHROPIC_API_KEY="sk-ant-test", LLM_MODEL="claude-sonnet-4-5"):
            llm = get_llm()
        from langchain_anthropic import ChatAnthropic

        assert isinstance(llm, ChatAnthropic)

    def test_missing_key_raises(self) -> None:
        """Anthropic with empty key raises ValueError."""
        with _patch_settings(LLM_PROVIDER="anthropic", ANTHROPIC_API_KEY=""), pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            get_llm()


class TestGetLlmOpenAI:
    def test_returns_chatopenai_without_custom_base_url(self) -> None:
        """OpenAI provider returns ChatOpenAI without custom base_url."""
        with _patch_settings(LLM_PROVIDER="openai", OPENAI_API_KEY="sk-test", LLM_MODEL="gpt-4o"):
            llm = get_llm()
        from langchain_openai import ChatOpenAI

        assert isinstance(llm, ChatOpenAI)
        # Should NOT have OpenRouter base URL
        base = str(llm.openai_api_base or "")
        assert "openrouter" not in base

    def test_missing_key_raises(self) -> None:
        """OpenAI with empty key raises ValueError."""
        with _patch_settings(LLM_PROVIDER="openai", OPENAI_API_KEY=""), pytest.raises(ValueError, match="OPENAI_API_KEY"):
            get_llm()


class TestGetLlmEdgeCases:
    def test_unknown_provider_raises(self) -> None:
        """Unknown provider raises ValueError listing valid providers."""
        with _patch_settings(LLM_PROVIDER="gemini"), pytest.raises(ValueError, match="Unknown LLM_PROVIDER"):
            get_llm()

    def test_multiple_keys_only_active_checked(self) -> None:
        """All keys set, only active provider's key is validated."""
        with _patch_settings(
            LLM_PROVIDER="openrouter",
            OPENROUTER_API_KEY="sk-or-test",
            ANTHROPIC_API_KEY="sk-ant-test",
            OPENAI_API_KEY="sk-test",
        ):
            llm = get_llm()
        from langchain_openai import ChatOpenAI

        assert isinstance(llm, ChatOpenAI)

    def test_provider_case_insensitive(self) -> None:
        """Provider name is case-insensitive."""
        with _patch_settings(LLM_PROVIDER="OpenRouter", OPENROUTER_API_KEY="sk-or-test"):
            llm = get_llm()
        from langchain_openai import ChatOpenAI

        assert isinstance(llm, ChatOpenAI)
