"""Application configuration loaded from environment variables."""

from __future__ import annotations

from pydantic import SecretStr
from pydantic_settings import BaseSettings

from app.models import Priority, Requirement


class Settings(BaseSettings):
    """API keys and environment configuration."""

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "text"  # "text" or "json"

    # LLM provider selection
    LLM_PROVIDER: str = "openrouter"
    LLM_MODEL: str = "openrouter/auto"
    LLM_TEMPERATURE: float = 0.0
    LLM_CONCURRENCY: int = 6  # Max concurrent LLM calls (semaphore limit)

    # API keys — all optional, validated at runtime by get_llm()
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    TAVILY_API_KEY: str

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()  # type: ignore[call-arg]


def get_llm():
    """Return a BaseChatModel instance based on the active LLM_PROVIDER setting.

    Imports are lazy so neither langchain-anthropic nor langchain-openai
    is required unless that provider is selected.
    """
    provider = settings.LLM_PROVIDER.lower()

    if provider == "openrouter":
        if not settings.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is required when LLM_PROVIDER=openrouter")
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            base_url=settings.OPENROUTER_BASE_URL,
            api_key=SecretStr(settings.OPENROUTER_API_KEY),
        )

    if provider == "anthropic":
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=settings.LLM_MODEL,  # type: ignore[arg-type]
            temperature=settings.LLM_TEMPERATURE,
        )

    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            api_key=SecretStr(settings.OPENAI_API_KEY),
        )

    raise ValueError(f"Unknown LLM_PROVIDER '{provider}'. Valid providers: openrouter, anthropic, openai")

VENDORS: list[str] = ["LangSmith", "Langfuse", "Braintrust", "PostHog"]

PRIORITY_WEIGHTS: dict[str, float] = {
    "high": 3.0,
    "medium": 2.0,
    "low": 1.0,
}

REQUIREMENTS: list[Requirement] = [
    Requirement(id="R1", description="Framework-agnostic tracing (not locked into LangChain or any single framework)", priority=Priority.high),
    Requirement(id="R2", description="Self-hosting option with full data sovereignty", priority=Priority.high),
    Requirement(id="R3", description="Built-in evaluation framework (LLM-as-judge, custom metrics, regression testing)", priority=Priority.high),
    Requirement(id="R4", description="OpenTelemetry support for integration with existing observability stack", priority=Priority.medium),
    Requirement(id="R5", description="Prompt management and versioning with rollback capability", priority=Priority.medium),
    Requirement(id="R6", description="Transparent, predictable pricing at scale (100K+ traces/month)", priority=Priority.low),
]
