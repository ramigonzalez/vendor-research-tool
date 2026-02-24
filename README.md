# Vendor Research Tool

An AI-powered research and comparison tool for LLM observability vendors. The application runs an automated pipeline that searches the web, extracts evidence, scores vendors against configurable requirements, and presents results in an interactive comparison matrix.

Built with Python, FastAPI, LangGraph, and Anthropic Claude.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Architecture](#architecture)
- [Scoring Methodology](#scoring-methodology)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Development](#development)
- [Scaling Considerations](#scaling-considerations)
- [Known Limitations](#known-limitations)
- [Project Structure](#project-structure)

---

## Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd vendor-research-tool

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate          # Windows

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys (see Prerequisites)

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload

# Open http://localhost:8000 in your browser
```

---

## Prerequisites

- **Python 3.11+**
- **Tavily API key** -- used for web search queries during the research phase.
  Sign up at [https://app.tavily.com](https://app.tavily.com).
- **LLM API key** -- one of the following, depending on your chosen provider:
  - **OpenRouter** (default, free models available) -- sign up at [https://openrouter.ai](https://openrouter.ai)
  - **Anthropic** -- sign up at [https://console.anthropic.com](https://console.anthropic.com)
  - **OpenAI** -- sign up at [https://platform.openai.com](https://platform.openai.com)

Create a `.env` file in the project root (or copy `.env.example`):

```env
# Provider selection
LLM_PROVIDER=openrouter
LLM_MODEL=meta-llama/llama-3.3-70b-instruct:free
LLM_TEMPERATURE=0

# API keys (set all you have; only the active provider's key is required)
OPENROUTER_API_KEY=sk-or-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx

# Always required
TAVILY_API_KEY=tvly-xxx
```

---

## Architecture

The application is a FastAPI server that orchestrates a LangGraph pipeline. A single-page frontend (vanilla HTML/CSS/JS) communicates with the backend over Server-Sent Events (SSE) for real-time progress updates.

### Pipeline Phases

The research pipeline executes in three sequential phases across eight graph nodes:

**Phase 1 -- Research**

1. **Query Generation** -- For each vendor/requirement pair, the LLM generates targeted search queries.
2. **Web Search** -- Queries are executed against the Tavily search API in parallel.
3. **Evidence Extraction** -- The LLM extracts structured evidence (claims, source types, relevance scores) from raw search results.
4. **Gap Analysis Loop** -- Evidence is evaluated for gaps (missing sources, low authority, insufficient count). If gaps are detected and the iteration limit has not been reached, the pipeline loops back through search and extraction with refined queries.

**Phase 2 -- Scoring**

5. **Capability Assessment** -- The LLM evaluates each vendor's capability level, maturity, and limitations for every requirement based on the collected evidence.
6. **Score Computation** -- Deterministic 4-factor score and 4-factor confidence formulas produce numerical results (see [Scoring Methodology](#scoring-methodology)).
7. **Ranking** -- Vendors are ranked by priority-weighted scores normalized to a 0--100 scale.

**Phase 3 -- Synthesis**

8. **Executive Summary** -- The LLM generates a narrative summary of the findings, rankings, and notable trade-offs.

### Data Flow

```
Query Generation --> Web Search --> Evidence Extraction
                        ^                  |
                        |          Gap Analysis (conditional)
                        +--<--<-- Gap Filling Queries
                                           |
                                           v
                    Capability Assessment --> Score Computation
                                               --> Ranking
                                                    --> Executive Summary
```

### Tech Stack

| Layer       | Technology                          |
|-------------|-------------------------------------|
| Backend     | Python 3.11+, FastAPI, Uvicorn      |
| Pipeline    | LangGraph, LangChain                |
| LLM         | Configurable: OpenRouter (default), Anthropic, OpenAI |
| Web Search  | Tavily API                          |
| Database    | SQLite with aiosqlite (WAL mode)    |
| Frontend    | Vanilla HTML / CSS / JavaScript     |

---

## Scoring Methodology

All scores are computed deterministically from LLM assessments and extracted evidence. There are no hidden weights or opaque model outputs in the final numbers.

### Requirement Score (0--10)

Each vendor-requirement pair receives a score computed from four factors:

```
score = 0.40 * capability + 0.30 * evidence + 0.20 * maturity + 0.10 * limitations
```

| Factor       | Weight | Derivation                                                              |
|--------------|--------|-------------------------------------------------------------------------|
| Capability   | 40%    | Based on the LLM's assessed capability level                           |
| Evidence     | 30%    | Count of supporting evidence sources (capped at 5)                     |
| Maturity     | 20%    | Based on the feature's maturity stage                                  |
| Limitations  | 10%    | Penalty based on the number of identified limitations                  |

**Capability scores:**

| Level    | Score |
|----------|-------|
| full     | 10    |
| partial  | 7     |
| minimal  | 3     |
| none     | 0     |
| unknown  | 2     |

**Evidence score:**

```
evidence_score = min(supporting_evidence_count, 5) / 5 * 10
```

**Maturity scores:**

| Level        | Score |
|--------------|-------|
| ga           | 10    |
| beta         | 7     |
| experimental | 4     |
| planned      | 2     |
| unknown      | 3     |

**Limitations score:**

```
limitations_score = max(0, 10 - limitation_count * 2)
```

### Confidence Score (0.0--1.0)

Each score is accompanied by a confidence value representing the reliability of the underlying evidence:

```
confidence = 0.30 * source_count + 0.30 * source_authority + 0.25 * source_recency + 0.15 * consistency
```

| Factor           | Weight | Derivation                                                                 |
|------------------|--------|---------------------------------------------------------------------------|
| Source Count      | 30%    | `min(evidence_count, 5) / 5`                                              |
| Source Authority  | 30%    | Mean authority weight across all evidence sources                         |
| Source Recency    | 25%    | Mean recency score based on evidence age                                  |
| Consistency       | 15%    | Proportion of evidence that supports the requirement                      |

**Authority weights by source type:**

| Source Type    | Weight |
|----------------|--------|
| official_docs  | 1.0    |
| github         | 0.8    |
| comparison     | 0.6    |
| blog           | 0.4    |
| community      | 0.3    |

**Recency scoring:**

| Evidence Age       | Score |
|--------------------|-------|
| 180 days or less   | 1.0   |
| 181--365 days      | 0.7   |
| Over 365 days      | 0.3   |

### Weighted Ranking (0--100)

Vendors are ranked using priority-weighted scores:

```
weighted_sum = SUM(score * priority_weight * confidence)  for each requirement
normalized_score = (weighted_sum / max_possible) * 100
```

Priority weights: **high = 3.0**, **medium = 2.0**, **low = 1.0**

---

## Configuration

All research parameters are defined in `app/config.py` and can be modified without changing any other code.

### LLM Provider

The LLM provider is configurable via environment variables. The default is **OpenRouter** with a free Llama model for zero-cost prototyping.

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `openrouter` | Active provider: `openrouter`, `anthropic`, or `openai` |
| `LLM_MODEL` | `meta-llama/llama-3.3-70b-instruct:free` | Model name for the selected provider |
| `LLM_TEMPERATURE` | `0` | Sampling temperature |
| `OPENROUTER_API_KEY` | | Required when `LLM_PROVIDER=openrouter` |
| `ANTHROPIC_API_KEY` | | Required when `LLM_PROVIDER=anthropic` |
| `OPENAI_API_KEY` | | Required when `LLM_PROVIDER=openai` |

**Quick-switch examples:**

```env
# Free prototyping (default — no changes needed)
LLM_PROVIDER=openrouter
LLM_MODEL=meta-llama/llama-3.3-70b-instruct:free

# Premium Anthropic results
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-5

# OpenAI alternative
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
```

You can set API keys for all three providers simultaneously in `.env`. Only the active provider's key is validated — switching providers is a one-line change to `LLM_PROVIDER`.

### Vendors

The default vendor list evaluates four LLM observability platforms:

```python
VENDORS = ["LangSmith", "Langfuse", "Braintrust", "PostHog"]
```

Add or remove vendors by editing this list.

### Requirements

Six requirements are evaluated, each with a priority level:

| ID  | Description                   | Priority |
|-----|-------------------------------|----------|
| R1  | Framework-agnostic tracing    | high     |
| R2  | Self-hosting support          | high     |
| R3  | Evaluation framework          | medium   |
| R4  | OpenTelemetry integration     | medium   |
| R5  | Custom metrics                | low      |
| R6  | Cost transparency             | low      |

To modify requirements, edit the `REQUIREMENTS` list in `app/config.py`:

```python
REQUIREMENTS = [
    Requirement(id="R1", description="Framework-agnostic tracing", priority=Priority.high),
    Requirement(id="R2", description="Self-hosting support", priority=Priority.high),
    # Add or modify requirements here
]
```

### Priority Weights

```python
PRIORITY_WEIGHTS = {
    "high": 3.0,
    "medium": 2.0,
    "low": 1.0,
}
```

### API Keys

API keys are loaded from the `.env` file via Pydantic Settings. Only the active provider's key and `TAVILY_API_KEY` are required. See [LLM Provider](#llm-provider) for details.

---

## API Reference

| Method | Endpoint                   | Description                                     |
|--------|----------------------------|-------------------------------------------------|
| GET    | `/`                        | Serve the frontend UI                           |
| GET    | `/health`                  | Health check (returns `{"status": "ok"}`)       |
| POST   | `/api/research`            | Start a research pipeline run (SSE stream)      |
| GET    | `/api/research/{job_id}`   | Retrieve results for a completed job            |
| GET    | `/api/jobs`                | List previous research jobs (most recent first) |

### POST /api/research

Launches the full research pipeline. Returns a Server-Sent Events stream with progress updates:

```
data: {"type": "started", "job_id": "..."}
data: {"type": "progress", "phase": "research", "pct": 25, "message": "..."}
...
data: {"type": "completed", "results": {...}}
```

### GET /api/research/{job_id}

Returns one of:

- `{"status": "running", "progress_pct": N}` -- pipeline still in progress
- `{"status": "failed", "error": "..."}` -- pipeline failed
- Full `ResearchResults` JSON -- pipeline completed

---

## Development

### Running Tests

```bash
# Run the full test suite with coverage
pytest tests/

# Run a specific test file
pytest tests/test_scoring.py
```

The project enforces a minimum of 60% code coverage.

### Linting and Type Checking

```bash
# Lint with ruff
make lint

# Auto-format
make format

# Type check with pyright
make typecheck

# Run all quality gates (lint + format check + typecheck + tests)
make check
```

### Security Audit

```bash
make security    # runs pip-audit
```

### Code Style

The project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting, configured in `pyproject.toml`:

- Target: Python 3.11
- Line length: 120 characters
- Rules: E, W, F, I, UP, B, SIM, RUF

---

## Scaling Considerations

The current architecture is designed for local, single-user evaluation runs. To scale from 4 vendors to 50+ or support concurrent users, consider the following changes:

### Database

Replace SQLite with **PostgreSQL** (or another production database) to support concurrent read/write access. The repository pattern (`app/repository.py`) already defines an abstract interface, making it straightforward to add a new implementation.

### Task Queue

Add **Celery + Redis** (or a similar task queue) for parallel pipeline execution. Each vendor's research phase is largely independent and can run as a separate task, significantly reducing wall-clock time.

### Evidence Deduplication

Integrate a **vector store** (e.g., Chroma, Pinecone, Weaviate) to deduplicate evidence across vendors and across repeated runs. This avoids redundant searches and improves consistency.

### Caching

Add a caching layer for Tavily search results and LLM responses. Repeated evaluations of the same vendors would benefit from cached evidence, reducing both latency and API costs.

### Vendor Expansion

The vendor list is a simple Python list in `app/config.py`. Scaling to 50+ vendors requires no structural changes -- only the configuration update and sufficient API quota. For very large vendor sets, consider batching pipeline runs and parallelizing across worker processes.

### Containerization

Package the application in a Docker container for reproducible deployments. Add a `docker-compose.yml` with PostgreSQL and Redis services for a production-ready setup.

---

## Known Limitations

- **Fixed vendor list** -- Vendors are configurable in code (`app/config.py`) but not through the UI.
- **Local-only deployment** -- No Docker, cloud, or production deployment configuration is included.
- **Runtime** -- A full 4-vendor, 6-requirement research run takes approximately 3 minutes (55--60 Tavily searches plus multiple LLM calls).
- **SQLite concurrency** -- SQLite is not suitable for concurrent production use with multiple simultaneous pipeline runs.
- **No authentication** -- API endpoints are unauthenticated and intended for local use only.
- **Rate limits** -- Large vendor lists may encounter Tavily or Anthropic API rate limits.

---

## Project Structure

```
vendor-research-tool/
|-- app/
|   |-- api/
|   |   |-- router.py          # FastAPI route handlers (SSE, jobs, results)
|   |-- graph/
|   |   |-- nodes.py           # LangGraph node implementations
|   |   |-- pipeline.py        # Graph assembly and execution
|   |   |-- progress.py        # SSE progress event helpers
|   |   |-- state.py           # Pipeline state definition
|   |-- prompts/               # LLM prompt templates
|   |-- scoring/
|   |   |-- engine.py          # Score, confidence, and ranking computation
|   |-- config.py              # Vendors, requirements, weights, API keys
|   |-- main.py                # FastAPI app setup and lifespan
|   |-- models.py              # Pydantic domain models
|   |-- repository.py          # SQLite repository (abstract + implementation)
|-- static/
|   |-- index.html             # Single-page frontend (HTML/CSS/JS)
|-- tests/                     # pytest test suite
|-- .env.example               # Template for environment variables
|-- Makefile                   # Development task shortcuts
|-- pyproject.toml             # Ruff, pyright, and pytest configuration
|-- requirements.txt           # Python dependencies
```
