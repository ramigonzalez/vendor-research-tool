# Vendor Research Tool

An AI-powered research and comparison tool for LLM observability vendors. The application runs an automated pipeline that searches the web, extracts evidence, scores vendors against configurable requirements, and presents results in an interactive comparison matrix with real-time pipeline visualization and a full audit trail.

Built with Python, FastAPI, LangGraph, React, TypeScript, and Tailwind CSS.

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
- [Engineering Notes](#engineering-notes)
- [Known Limitations](#known-limitations)
- [Project Structure](#project-structure)

---

## Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd vendor-research-tool

# Configure backend environment
cp vendor-research-tool-backend/.env.example vendor-research-tool-backend/.env
# Edit .env with your API keys (see Prerequisites)

# Start both backend + frontend
./run.sh

# Or start them separately:
# Terminal 1 — Backend
cd vendor-research-tool-backend
./run.sh

# Terminal 2 — Frontend
cd vendor-research-tool-frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## Prerequisites

- **Python 3.11+**
- **Node.js 20+** (for the React frontend)
- **Tavily API key** -- used for web search queries during the research phase.
  Sign up at [https://app.tavily.com](https://app.tavily.com).
- **LLM API key** -- one of the following, depending on your chosen provider:
  - **OpenRouter** (default, free models available) -- sign up at [https://openrouter.ai](https://openrouter.ai)
  - **Anthropic** -- sign up at [https://console.anthropic.com](https://console.anthropic.com)
  - **OpenAI** -- sign up at [https://platform.openai.com](https://platform.openai.com)

Create a `.env` file in `vendor-research-tool-backend/` (or copy `.env.example`):

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

# CORS (frontend origin)
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

---

## Architecture

The application is a **monorepo** with two projects:

- **Backend** (`vendor-research-tool-backend/`) -- FastAPI server that orchestrates a LangGraph research pipeline, stores results in SQLite, and streams progress via SSE.
- **Frontend** (`vendor-research-tool-frontend/`) -- React + TypeScript + Tailwind CSS single-page app that renders real-time pipeline visualization, audit trail, and scoring breakdowns.

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
| Frontend    | React 19, TypeScript, Tailwind CSS v4, Vite |

### Frontend Features

- **Pipeline Stepper** -- 7-stage horizontal stepper showing real-time pipeline progress
- **Research Timeline** -- Animated source pills appearing as search results arrive
- **Audit Trail** -- 4-tab view (Timeline, Queries, Sources, Activity Log) for both live and historical runs
- **Scoring Explanation** -- Interactive breakdowns of score formulas, confidence components, and priority weights
- **Comparison Matrix** -- Click any cell to drill down into evidence, scores, and confidence details
- **Accessibility** -- ARIA roles, keyboard navigation, focus management, skip-to-content link

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

All research parameters are defined in `vendor-research-tool-backend/app/config.py` and can be modified without changing any other code.

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

| ID  | Description                                                                       | Priority |
|-----|-----------------------------------------------------------------------------------|----------|
| R1  | Framework-agnostic tracing (not locked into LangChain or any single framework)    | high     |
| R2  | Self-hosting option with full data sovereignty                                    | high     |
| R3  | Built-in evaluation framework (LLM-as-judge, custom metrics, regression testing)  | high     |
| R4  | OpenTelemetry support for integration with existing observability stack           | medium   |
| R5  | Prompt management and versioning with rollback capability                         | medium   |
| R6  | Transparent, predictable pricing at scale (100K+ traces/month)                    | low      |

To modify requirements, edit the `REQUIREMENTS` list in `app/config.py`:

```python
REQUIREMENTS = [
    Requirement(id="R1", description="Framework-agnostic tracing (not locked into LangChain or any single framework)", priority=Priority.high),
    Requirement(id="R2", description="Self-hosting option with full data sovereignty", priority=Priority.high),
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

| Method | Endpoint                          | Description                                        |
|--------|-----------------------------------|----------------------------------------------------|
| GET    | `/health`                         | Health check (returns `{"status": "ok"}`)          |
| POST   | `/api/research`                   | Start a research pipeline run (SSE stream)         |
| GET    | `/api/research/{job_id}`          | Retrieve results for a completed job               |
| GET    | `/api/research/{job_id}/audit`    | Retrieve audit events for a job (chronological)    |
| GET    | `/api/jobs`                       | List previous research jobs (most recent first)    |

### POST /api/research

Launches the full research pipeline. Returns a Server-Sent Events stream with progress updates:

```
data: {"type": "started", "job_id": "..."}
data: {"type": "phase_start", "phase": "planning", "timestamp": "..."}
data: {"type": "query_generated", "vendor": "...", "requirement_id": "...", "queries": [...]}
data: {"type": "search_result", "vendor": "...", "source_url": "...", "source_name": "...", "domain": "..."}
data: {"type": "evidence_extracted", "vendor": "...", "requirement_id": "...", "count": 3}
data: {"type": "score_computed", "vendor": "...", "requirement_id": "...", "score": 8.5, "confidence": 0.85}
data: {"type": "vendor_ranked", "vendor": "...", "rank": 1, "overall_score": 85.2}
data: {"type": "phase_end", "phase": "planning", "timestamp": "..."}
data: {"type": "progress", "phase": "research", "pct": 25, "message": "..."}
...
data: {"type": "completed", "results": {...}}
```

### GET /api/research/{job_id}

Returns one of:

- `{"status": "running", "progress_pct": N}` -- pipeline still in progress
- `{"status": "failed", "error": "..."}` -- pipeline failed
- Full `ResearchResults` JSON -- pipeline completed

### GET /api/research/{job_id}/audit

Returns the persisted audit events for a historical job as a JSON array, sorted chronologically:

```json
[
  {"event_type": "phase_start", "payload": {"phase": "planning"}, "created_at": "2026-02-25T..."},
  {"event_type": "query_generated", "payload": {"vendor": "...", "queries": [...]}, "created_at": "..."}
]
```

Returns 404 if the job does not exist, or an empty array if no audit events were recorded.

---

## Development

### Running the Backend

```bash
cd vendor-research-tool-backend

# Create venv and install deps
python3 -m venv ../venv
source ../venv/bin/activate
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload
```

### Running the Frontend

```bash
cd vendor-research-tool-frontend

# Install deps and start dev server
npm install
npm run dev
```

The frontend dev server runs on port 5173 and proxies API requests to the backend on port 8000.

### Running Tests

```bash
# Backend tests (from vendor-research-tool-backend/)
pytest tests/

# Frontend tests (from vendor-research-tool-frontend/)
npm test

# Frontend scoring parity tests
npm test -- scoring
```

The backend enforces a minimum of 60% code coverage.

### Linting and Type Checking

```bash
# Backend (from vendor-research-tool-backend/)
make lint          # Lint with ruff
make format        # Auto-format
make typecheck     # Type check with pyright
make check         # Run all quality gates

# Frontend (from vendor-research-tool-frontend/)
npm run lint       # ESLint
npm run typecheck  # TypeScript
npm run build      # Full build (type check + Vite build)
```

### Security Audit

```bash
make security    # runs pip-audit (from backend dir)
```

### Code Style

The backend uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting, configured in `pyproject.toml`:

- Target: Python 3.11
- Line length: 120 characters
- Rules: E, W, F, I, UP, B, SIM, RUF

The frontend uses ESLint with TypeScript-aware rules.

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

## Engineering Notes

### Approach and Key Decisions

The core design principle is **prevention-first scoring**: the LLM never generates final scores directly. Instead, it handles what it does well (reading comprehension, structured extraction, narrative synthesis), while a deterministic formula handles scoring. Every number in the matrix is traceable -- you can audit any cell back to the exact evidence items and formula inputs that produced it.

**Evidence collection.** Tavily was chosen over Exa or SerpAPI for three reasons: native LangChain integration saves boilerplate in a time-constrained build; it returns NLP-summarized snippets rather than raw HTML, keeping evidence extraction prompts lean; and its per-result relevance scores provide a free signal for the confidence computation. The trade-off is single-provider dependency. Each vendor x requirement pair gets two search queries targeting different source types -- official documentation and community/comparison sources -- because what vendors *claim* to support and what users *actually experience* often diverge. That gap is where procurement mistakes happen.

**Scoring design.** The hybrid approach -- LLM capability assessment feeding a deterministic weighted formula -- makes scores reproducible and auditable. The confidence dimension is kept separate from the score deliberately: a vendor can score 8/10 with high confidence (strong, recent, authoritative evidence) or 8/10 with low confidence (sparse evidence). Both are represented differently in the UI. Penalizing through confidence rather than zeroing out sparse-evidence scores is more honest than either guessing a number or assigning zero to vendors with thin documentation.

**LangGraph.** The pipeline uses LangGraph to make phases explicit and inspectable. Honestly, a plain async function with a `while` loop for the gap analysis would have worked. LangGraph adds dependency overhead for what is essentially a linear pipeline with one conditional edge. It was kept because the explicit graph structure is easier to discuss architecturally and aligns with the ecosystem of tools being evaluated -- but this was a deliberate trade-off, not an organic fit.

**SSE over polling.** A 3-minute pipeline with ~55 API calls needs real-time feedback. Server-Sent Events cut the request count from ~20 polling calls to 1 persistent connection, give the UI instant per-step updates, and eliminate the need for a GET-status endpoint while the job runs (the GET endpoint still exists for loading past results).

---

### How AI Tools Were Used

This project was built using [Claude Code](https://claude.com/claude-code) with Synkra AIOS, an AI orchestration framework that coordinates specialized agents (`@dev`, `@qa`, `@architect`) around a story-driven development workflow.

**What worked well.** Working through architecture decisions with Claude *before writing any code* was the highest-leverage use of AI in this project. The three documents in `docs/initial-documentation/` capture the reasoning behind every major choice -- Tavily vs. alternatives, hybrid scoring, SSE transport, repository pattern, evidence sufficiency thresholds -- all worked through interactively before implementation started. No architectural regrets after the fact. From there, roughly 80% of the codebase was generated through the `@dev` agent following those plans, with the author reviewing, correcting, and verifying outputs. The test suite (14 test files, type checking, linting) was largely AI-generated, which is where the time savings are most reliable -- test logic is mechanical enough to verify quickly.

**Where AI went astray.** The AI's instinct is always to add scope. Enforcing the time budget required explicit intervention: each "Could Have" and "Won't Have" item in the planning documents represents a boundary held against AI suggestions. The final scope is narrower than what the AI proposed, and deliberately so. LangGraph is the other example -- the AI defaulted to it without weighing whether the complexity was justified. It was kept after deliberate evaluation, not because the AI was right.

**Validation.** AI-generated code was validated at two levels: automated (`make check` -- lint, type-check, tests) and manual (running the full pipeline end-to-end, verifying that evidence items link to real source URLs, checking that scores move in the expected direction when evidence changes).

---

### What I'd Improve With More Time

**Multi-provider search.** The single biggest quality improvement would be fanning out to Tavily, Exa, and direct documentation scraping, then deduplicating by URL. Each provider has blind spots; coverage improves significantly when combined. This is also the fix for the recency problem -- direct doc scraping always reflects the current state of a vendor's documentation.

**Dynamic configuration.** Vendors and requirements are hardcoded in `app/config.py`. The pipeline and scoring engine already support arbitrary inputs; only the configuration layer is static. A setup flow in the UI (define vendors, enter requirements with priorities, launch) would make this a general-purpose tool rather than a one-off.

**Evidence caching.** Re-running the same vendor set costs API credits and 3 minutes every time. A caching layer with a TTL would make repeat runs near-instant and enable the tool to track capability changes over time -- which is far more useful than a point-in-time snapshot.

**Behavioral testing.** The tool currently evaluates *documentation* -- what vendors claim. The more valuable signal is *behavioral* -- does the API actually work as documented, what's the latency overhead, where does tracing fail? This is what a production version would add: lightweight integration tests that exercise vendor SDKs against a controlled workload. That's what moves this from a research tool to a procurement tool.

---

## Known Limitations

- **Fixed vendor list** -- Vendors are configurable in code (`app/config.py`) but not through the UI.
- **Local-only deployment** -- No Docker, cloud, or production deployment configuration is included.
- **Runtime** -- A full 4-vendor, 6-requirement research run takes approximately 3 minutes (55--60 Tavily searches plus multiple LLM calls).
- **SQLite concurrency** -- SQLite is not suitable for concurrent production use with multiple simultaneous pipeline runs.
- **No authentication** -- API endpoints are unauthenticated and intended for local use only.
- **Rate limits** -- Large vendor lists may encounter Tavily or LLM API rate limits.

---

## Project Structure

```
vendor-research-tool/
|-- run.sh                          # Start both backend + frontend
|-- vendor-research-tool-backend/
|   |-- app/
|   |   |-- api/
|   |   |   |-- router.py          # FastAPI route handlers (SSE, jobs, results, audit)
|   |   |-- graph/
|   |   |   |-- nodes.py           # LangGraph node implementations
|   |   |   |-- pipeline.py        # Graph assembly and execution
|   |   |   |-- progress.py        # SSE progress event helpers + audit persistence
|   |   |   |-- state.py           # Pipeline state definition
|   |   |-- prompts/               # LLM prompt templates
|   |   |-- scoring/
|   |   |   |-- engine.py          # Score, confidence, and ranking computation
|   |   |-- config.py              # Vendors, requirements, weights, API keys
|   |   |-- main.py                # FastAPI app setup, CORS, lifespan
|   |   |-- models.py              # Pydantic domain models
|   |   |-- repository.py          # SQLite repository (abstract + implementation)
|   |-- tests/                     # pytest test suite (200 tests, 94% coverage)
|   |-- data/                      # SQLite database (auto-created)
|   |-- run.sh                     # Backend-only run script
|   |-- Makefile                   # Development task shortcuts
|   |-- pyproject.toml             # Ruff, pyright, and pytest configuration
|   |-- requirements.txt           # Python dependencies
|   |-- .env.example               # Template for environment variables
|-- vendor-research-tool-frontend/
|   |-- src/
|   |   |-- components/
|   |   |   |-- atoms/             # Badge, ScoreCell
|   |   |   |-- molecules/         # LiveCounters, SourcePill, ScoreBreakdown, ConfidenceBreakdown, PriorityWeights
|   |   |   |-- organisms/         # ComparisonMatrix, DrillDownPanel, PipelineStepper, AuditView, ActivityFeed, etc.
|   |   |   |-- templates/         # ResearchPage (main layout)
|   |   |-- hooks/                 # useResearchState, useTimer
|   |   |-- lib/                   # types, scoring, sse-client, api
|   |   |-- styles/                # Tailwind globals with design tokens
|   |-- package.json
|   |-- vite.config.ts
|   |-- tsconfig.json
|-- docs/
|   |-- stories/                   # Development stories (numbered by epic)
|   |-- epics/                     # Epic documents
|   |-- initial-documentation/     # Architecture, PRD, planning docs
```
