"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings

from app.models import Priority, Requirement


class Settings(BaseSettings):
    """API keys and environment configuration."""

    ANTHROPIC_API_KEY: str
    TAVILY_API_KEY: str

    model_config = {"env_file": ".env"}


settings = Settings()  # type: ignore[call-arg]

VENDORS: list[str] = ["LangSmith", "Langfuse", "Braintrust", "PostHog"]

PRIORITY_WEIGHTS: dict[str, float] = {
    "high": 3.0,
    "medium": 2.0,
    "low": 1.0,
}

REQUIREMENTS: list[Requirement] = [
    Requirement(id="R1", description="Framework-agnostic tracing", priority=Priority.high),
    Requirement(id="R2", description="Self-hosting support", priority=Priority.high),
    Requirement(id="R3", description="Evaluation framework", priority=Priority.medium),
    Requirement(id="R4", description="OpenTelemetry integration", priority=Priority.medium),
    Requirement(id="R5", description="Custom metrics", priority=Priority.low),
    Requirement(id="R6", description="Cost transparency", priority=Priority.low),
]
