# SignalCore Vendor Research Tool — Brownfield Enhancement PRD

> **Document Type**: Brownfield PRD (planning-complete, implementation-pending)
> **Version**: 1.0 | **Date**: 2026-02-23 | **Author**: Morgan (PM Agent)
> **Status**: Approved for Implementation

---

## Change Log

| Change | Date | Version | Description | Author |
|--------|------|---------|-------------|--------|
| Initial PRD | 2026-02-23 | 1.0 | Synthesized from 3 planning documents | Morgan (@pm) |

---

## 1. Intro — Project Analysis and Context

### 1.1 Analysis Source

**IDE-based fresh analysis** + User-provided planning documentation:
- `docs/1. signalcore-plan.md` — Initial architecture & MVP plan
- `docs/2. signalcore-refinement.md` — Deep dive on search, scoring, async patterns
- `docs/3. signalcore-final-refinement.md` — Final technical specs, domain models, PM handoff

### 1.2 Current Project State

The SignalCore Vendor Research Tool is a **technical engineering evaluation assignment** for an AI engineering team at SignalCore. The tool automates research and comparison of LLM observability platforms by running an agentic search pipeline against real web sources, computing evidence-backed scores, and presenting results in an interactive matrix UI.

**Current state**: 100% planned, 0% implemented. Three progressive planning documents define the complete architecture, scoring methodology, data models, API design, and implementation roadmap. This PRD formalizes those decisions into actionable epics and stories.

### 1.3 Available Documentation Analysis

| Documentation | Available | Notes |
|---------------|-----------|-------|
| Tech Stack | ✓ | Fully specified in planning docs |
| Architecture | ✓ | C4 diagrams (Level 1 & 2), LangGraph flow diagrams |
| Coding Standards | ✓ | Python patterns, Pydantic models, repository pattern |
| API Documentation | ✓ | SSE streaming, REST endpoints fully specified |
| External API Documentation | ✓ | Tavily, Claude Anthropic APIs documented |
| UX/UI Guidelines | Partial | Single-page HTML/JS; wireframe described in prose |
| Technical Debt | N/A | No code yet |
| Scoring Methodology | ✓ | 3-layer scoring fully specified with Python code |

### 1.4 Enhancement Scope

**Enhancement Type**: New Feature Addition (greenfield implementation against a complete spec)

**Enhancement Description**: Implement the full SignalCore Vendor Research Tool from scratch, following the fully-specified architecture in `/docs`. The implementation covers a three-stage LangGraph research pipeline, deterministic scoring engine, FastAPI backend with SSE streaming, SQLite persistence with repository pattern, and a single-page HTML frontend showing a comparison matrix with drill-down evidence.

**Impact Assessment**: Major Impact — new codebase, all components built from spec.

### 1.5 Goals & Constraints

**Hard Constraint**: This is a **2–3 hour time-boxed prototype** built by a single developer. All MoSCoW prioritization and architectural decisions are driven by this constraint. The goal is a working demo for a Zoom evaluation, not a production system.

- Deliver a runnable local tool: `git clone → pip install → uvicorn → works`
- Collect evidence from real, recent, citable web sources (not static LLM knowledge)
- Score 4 vendors × 6 requirements with transparent, explainable methodology
- Present results as an interactive matrix with confidence indicators and evidence drill-down
- Demonstrate production-ready architectural thinking (repository pattern, SSE streaming, evidence sufficiency thresholds, deterministic scoring)
- Support the Zoom evaluation/interview by showing technical depth across the full stack

### 1.6 Background Context

An AI engineering team needs to select an LLM observability platform and commissioned this tool to automate vendor evaluation. The assignment doubles as a technical evaluation of the builder's capabilities — it must demonstrate LangGraph orchestration, evidence-backed scoring, API design, and scalability thinking.

The three planning documents represent a progressive refinement process: Document 1 established the core architecture; Document 2 refined search strategy (Tavily `/search` not `/research`), promoted SQLite to Must Have, and clarified async patterns (SSE over polling); Document 3 finalized evidence sufficiency thresholds, repository pattern with Pydantic models, and produced the full epic/story breakdown. This PRD consolidates all three into an authoritative implementation guide.

---

## 2. Requirements

### 2.1 Functional Requirements

- **FR1**: The system shall run a LangGraph research pipeline that generates 2 search queries per vendor×requirement pair, targeting different source types (official documentation vs. external sources).
- **FR2**: The system shall execute Tavily searches in parallel (max 5 concurrent) using `AsyncTavilyClient` with semaphore control.
- **FR3**: The system shall extract structured `Evidence` objects from search results using LLM, capturing: claim, source_url, source_name, source_type, content_date, relevance, and supports_requirement.
- **FR4**: The system shall implement evidence sufficiency checking with deterministic thresholds: ≥2 sources, ≥1 authoritative source (official_docs or github), ≥1 source with relevance ≥0.5. Maximum 2 research iterations.
- **FR5**: The system shall compute per-requirement scores (0–10) using a hybrid LLM+algorithmic approach: Capability Coverage (40%), Evidence Strength (30%), Maturity (20%), Limitations penalty (10%).
- **FR6**: The system shall compute confidence scores (0–1) fully deterministically from evidence metadata: Source Count (30%), Source Authority (30%), Source Recency (25%), Consistency (15%).
- **FR7**: The system shall compute weighted vendor rankings: `Σ(score × priority_weight × confidence)` where priority weights are High=3.0, Medium=2.0, Low=1.0, normalized to 0–100.
- **FR8**: The system shall persist all jobs, evidence, and scores in SQLite using a `ResearchRepository` interface with aiosqlite.
- **FR9**: The system shall expose a `POST /api/research` endpoint that triggers the pipeline and streams real-time progress via Server-Sent Events.
- **FR10**: The system shall expose a `GET /api/research/{job_id}` endpoint to retrieve cached results.
- **FR11**: The system shall expose a `GET /api/jobs` endpoint to list previous research jobs.
- **FR12**: The frontend shall display a comparison matrix with vendors as columns and requirements as rows, with scores and confidence indicators.
- **FR13**: The frontend shall support evidence drill-down: clicking a matrix cell expands a panel showing justification, evidence items, source badges, and content dates.
- **FR14**: The frontend shall display an executive summary (3–4 paragraphs) at the top of results.
- **FR15**: The frontend shall display real-time progress during research using SSE, showing phase labels and percentage.

### 2.2 Non-Functional Requirements

- **NFR1**: The full research pipeline (4 vendors × 6 requirements × 2 iterations) shall complete within the Tavily and Claude API rate limits without manual intervention.
- **NFR2**: The tool shall run entirely locally: no cloud infrastructure, no authentication, no persistent server required beyond `uvicorn`.
- **NFR3**: All scores must be reproducible — same evidence input yields same score output (deterministic scoring engine).
- **NFR4**: The codebase must follow Python 3.11+ typing standards with Pydantic v2 for all domain models.
- **NFR5**: The repository pattern must allow swapping SQLite for PostgreSQL with no business logic changes (interface abstraction).
- **NFR6**: The frontend must work in modern browsers with no build tools, bundlers, or npm — pure HTML/CSS/JS.
- **NFR7**: The system must handle evidence gaps gracefully — low confidence display, not failure, when sources are sparse.
- **NFR8**: API keys (ANTHROPIC_API_KEY, TAVILY_API_KEY) must be loaded from environment variables / `.env` file, never hardcoded.

### 2.3 Compatibility Requirements

- **CR1**: No existing API compatibility required (new system).
- **CR2**: SQLite schema must support future migration to PostgreSQL (no SQLite-specific syntax in queries).
- **CR3**: Frontend styling must be self-contained in `static/index.html` (no external CDN dependencies that could break).
- **CR4**: LangGraph pipeline must be compatible with LangChain ecosystem versions specified in `requirements.txt`.

---

## 3. User Interface Enhancement Goals

### 3.1 Integration with Existing UI

Single-page HTML application with no existing UI to integrate with. Design principles:
- Clean, data-dense presentation (evaluator audience, not consumer)
- Immediate visual hierarchy: summary → matrix → drill-down
- Color semantics: green/amber/red for score ranges; opacity for confidence

### 3.2 Modified/New Screens

| Screen | Type | Description |
|--------|------|-------------|
| Start Screen | New | Single "Run Research" button, progress area |
| Results Matrix | New | Vendors × requirements grid with scores and confidence |
| Evidence Drill-Down | New | Slide-out panel with evidence list per cell |
| Executive Summary | New | 3–4 paragraph narrative at top of results |
| Job History | New (Could Have) | List of previous research runs |

### 3.3 UI Consistency Requirements

- All UI in `static/index.html` — single file, self-contained
- Use CSS custom properties for theming
- Score cells: background color based on score range (≥7 green, 4–6.9 amber, <4 red)
- Confidence: opacity level (high=full, medium=70%, low=40%) + dashed border for low confidence

---

## 4. Technical Constraints and Integration Requirements

### 4.1 Existing Technology Stack

**Languages**: Python 3.11+, JavaScript (vanilla ES2022)
**Frameworks**: FastAPI, LangGraph, LangChain, Pydantic v2
**Database**: SQLite via aiosqlite (async)
**Infrastructure**: Local only — uvicorn dev server, no Docker required
**External Dependencies**:
- Anthropic Claude API (claude-sonnet-4-5 or equivalent for structured output)
- Tavily Search API (`/search` endpoint, sync mode via AsyncTavilyClient)

### 4.2 Integration Approach

**Database Integration Strategy**: aiosqlite for async SQLite; abstract `ResearchRepository` interface enables future PostgreSQL swap; WAL mode for concurrent read/write during streaming.

**API Integration Strategy**: FastAPI with `StreamingResponse` for SSE; `text/event-stream` content type; client uses `fetch + ReadableStream` (not EventSource, which doesn't support POST headers).

**Frontend Integration Strategy**: FastAPI serves `static/index.html` as static file. JS uses `fetch` for POST trigger and SSE streaming, then `fetch` for GET cached results.

**Testing Integration Strategy**: `pytest` + `pytest-asyncio` for async tests; mock Tavily and Claude APIs in unit tests; test scoring engine with deterministic fixtures.

### 4.3 Code Organization

```
vendor-research-tool/
├── app/
│   ├── main.py              # FastAPI app, routes, static serving
│   ├── config.py            # Settings (vendors, requirements, API keys)
│   ├── models.py            # All Pydantic domain models
│   ├── repository.py        # ResearchRepository interface + SQLite impl
│   ├── graph/
│   │   ├── state.py         # LangGraph ResearchState TypedDict
│   │   ├── nodes.py         # All graph nodes (query, search, extract, score, synthesize)
│   │   └── pipeline.py      # Graph construction and compilation
│   ├── scoring/
│   │   └── engine.py        # Deterministic scoring functions
│   └── prompts/
│       ├── research.py      # Query generation prompts
│       ├── extraction.py    # Evidence extraction prompts
│       ├── assessment.py    # Capability assessment prompts
│       └── synthesis.py     # Summary generation prompts
├── static/
│   └── index.html           # Complete single-page frontend
├── tests/
│   ├── test_scoring.py
│   ├── test_evidence.py
│   └── test_api.py
├── .env.example
├── requirements.txt
└── README.md
```

**Naming Conventions**: snake_case for Python; kebab-case for CSS classes; SCREAMING_SNAKE for constants.

**Coding Standards**: Type annotations on all function signatures; Pydantic models for all data boundaries; no bare `except` clauses; structured logging.

### 4.4 Deployment and Operations

**Build Process**: No build step. `pip install -r requirements.txt && uvicorn app.main:app --reload`.

**Deployment Strategy**: Local development only. Future: containerize with Docker for evaluation reproducibility.

**Monitoring and Logging**: Python `logging` module with structured output. Debug log at `.ai/debug-log.md` per AIOS standards.

**Configuration Management**: `python-dotenv` for `.env` loading; `pydantic-settings` for typed settings; `.env.example` committed with placeholder keys.

### 4.5 Risk Assessment and Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Tavily rate limiting during 55-60 API calls | Medium | High | AsyncTavilyClient semaphore (max 5 concurrent), exponential backoff |
| Claude structured output parsing failures | Medium | Medium | Fallback to template-based query generation; conservative "unknown" defaults |
| Evidence gap for newer/smaller vendors (Braintrust, PostHog) | High | Medium | Gap-filling second iteration with alternative terminology queries |
| SQLite WAL mode conflicts during streaming | Low | Medium | Single-writer design; SSE writes happen in background task |
| Context window overflow on evidence extraction | Low | High | Batch evidence by search result, not by vendor×requirement aggregate |

---

## 5. Architecture Decision Records

### ADR-001: Evidence Collection via Tavily `/search`
**Decision**: Use Tavily `/search` (sync, per-query) not `/research` (async, pre-composed).
**Rationale**: Full control over queries, per-requirement granularity, demonstrates LangGraph orchestration skill.

### ADR-002: Hybrid Score Computation
**Decision**: LLM extracts evidence and provides capability assessment; algorithm computes deterministic scores.
**Rationale**: Prevents hallucination; scores are transparent, reproducible, and explainable.

### ADR-003: 2-Iteration Research Loop with Deterministic Sufficiency
**Decision**: Max 2 search iterations. Sufficiency thresholds: ≥2 sources, ≥1 authoritative, ≥1 relevant (≥0.5).
**Rationale**: Balances evidence quality vs. API cost; prevents infinite loops; gap types drive query refinement strategies.

### ADR-004: SSE over Polling
**Decision**: Server-Sent Events for real-time progress, not GET polling.
**Rationale**: 1 persistent connection vs. 20+ polling requests; instant updates; native FastAPI StreamingResponse support.

### ADR-005: Repository Pattern for Persistence
**Decision**: Abstract `ResearchRepository` interface; `SQLiteResearchRepository` implementation.
**Rationale**: Type-safe data access; easy PostgreSQL migration; testable with mock implementation.

---

## 6. Epic and Story Structure

**Epic Structure Decision**: 5 epics structured by system layer, designed for sequential execution following the critical path dependency graph. Each epic is independently testable.

| Epic | Title | Stories | Story Points | Priority |
|------|-------|---------|-------------|----------|
| 1 | Research Pipeline | 5 | 18 | Must Have |
| 2 | Scoring Engine | 5 | 12 | Must Have |
| 3 | API & Persistence Layer | 6 | 12 | Must Have |
| 4 | Results UI | 5 | 12 | Must Have + Should Have |
| 5 | Polish & Delivery | 4 | 7 | Should Have + Could Have |

**Build Order (Critical Path)**:
`E5-S1 → E2-S1 → E3-S1 → E3-S2 → E1-S1 → E1-S2 → E1-S3 → E1-S4 → E2-S2 → E2-S3 → E2-S4 → E2-S5 → E1-S5 → E3-S3 → E3-S4 → E3-S5 → E3-S6 → E4-S5 → E4-S1 → E4-S2 → E4-S3 → E4-S4 → E5-S2 → E5-S3 → E5-S4`

> **Note**: E5-S1 (Project Setup) is the critical-path first story — it creates the project scaffold (`config.py`, `.env`, `requirements.txt`, package structure) that all other stories depend on. It is Must Have despite being in Epic 5.

> See individual epic files in `docs/prd/` for full story breakdowns.

---

## 7. Vendors & Requirements (Fixed MVP Scope)

### Vendors
| Vendor | Evidence Density | Notes |
|--------|-----------------|-------|
| LangSmith | High | Official LangChain ecosystem, well-documented |
| Langfuse | High | Active open-source, strong GitHub presence |
| Braintrust | Medium | Newer, less community content |
| PostHog | Medium-Low | Product analytics first, LLM features secondary |

### Requirements
| ID | Requirement | Priority |
|----|-------------|----------|
| R1 | Framework-agnostic tracing | High |
| R2 | Self-hosting support | High |
| R3 | Evaluation framework | Medium |
| R4 | OpenTelemetry integration | Medium |
| R5 | Custom metrics | Low |
| R6 | Cost transparency | Low |

**Priority Weights** (used in weighted ranking formula — see FR7):
- High = 3.0
- Medium = 2.0
- Low = 1.0

> Weights are derived from priority categories, not assigned per-requirement. This matches the scoring methodology defined in the planning documents (Doc 1 §2.5 Layer 3, Doc 2 `compute_overall_rankings()` implementation).

---

*— Morgan, planejando o futuro 📊*
*Sharded epics: `docs/prd/epic-{1-5}-*.md` | Stories: `docs/stories/{epic}.{story}.*.md`*
