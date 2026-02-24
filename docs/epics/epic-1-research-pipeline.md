# Epic 1: Research Pipeline

**Epic Goal**: Build the complete LangGraph research pipeline that collects real web evidence for each vendor×requirement pair using iterative Tavily searches, evidence extraction, and gap analysis.

**Integration Requirements**: Depends on domain models (E2-S1) and repository pattern (E3-S2). Provides evidence data consumed by Scoring Engine (Epic 2).

**MoSCoW**: All stories = Must Have
**Total Story Points**: 18

---

## Story 1.1 — LangGraph Query Generation Node

**As a** research pipeline,
**I want** to generate 2 targeted search queries per vendor×requirement pair using an LLM,
**so that** each pair is researched from two complementary angles (official documentation and external sources).

### Acceptance Criteria
1. LangGraph node `generate_queries` accepts vendor name and requirement as input.
2. LLM generates exactly 2 queries in a single API call via structured output.
3. Query 1 targets official sources (e.g., docs, GitHub).
4. Query 2 targets external sources (e.g., comparisons, community, blog posts).
5. Fallback template-based query generation activates if LLM output is invalid/unparseable.
6. Queries are stored in `ResearchState.queries` dict keyed by `(vendor, requirement_id)`.
7. All 4 vendors × 6 requirements = 24 query pairs generated before execution.

**Executor**: @dev | **Quality Gate**: @architect
**Story Points**: 3

---

## Story 1.2 — Parallel Search Execution

**As a** research pipeline,
**I want** to execute Tavily searches in parallel with concurrency control,
**so that** all 24+ search pairs complete efficiently without overwhelming the API.

### Acceptance Criteria
1. Uses `AsyncTavilyClient` for async search execution.
2. `asyncio.Semaphore` limits concurrent searches to maximum 5.
3. Each query executed with: `max_results=5`, `search_depth="advanced"`, `include_raw_content=False`.
4. Results stored in `ResearchState.raw_results` keyed by `(vendor, requirement_id, query_index)`.
5. Individual search failures are caught and logged; do not abort entire pipeline.
6. Total search time logged for performance monitoring.

**Executor**: @dev | **Quality Gate**: @architect
**Story Points**: 4

---

## Story 1.3 — Structured Evidence Extraction

**As a** research pipeline,
**I want** to extract structured `Evidence` objects from raw search results using an LLM,
**so that** each piece of evidence has traceable, structured metadata for scoring.

### Acceptance Criteria
1. LLM extracts `Evidence` objects from Tavily search results per vendor×requirement pair.
2. Each `Evidence` contains: `claim`, `source_url`, `source_name`, `source_type`, `content_date`, `relevance` (0–1), `supports_requirement` (bool).
3. `source_type` is classified as one of: `official_docs`, `github`, `comparison`, `blog`, `community`.
4. LLM instructed to be conservative — only extract explicitly stated claims, not inferences.
5. Evidence objects persisted to SQLite via repository.
6. Minimum 0 evidence accepted (gap handling follows in E1-S4).

**Executor**: @dev | **Quality Gate**: @architect
**Story Points**: 4

---

## Story 1.4 — Evidence Gap Analysis & Research Loop

**As a** research pipeline,
**I want** to detect evidence gaps and run a second research iteration to fill them,
**so that** sparse-evidence vendor×requirement pairs get a second chance before scoring.

### Acceptance Criteria
1. `check_evidence_sufficiency()` function runs after initial research with deterministic thresholds: ≥2 sources AND ≥1 authoritative (official_docs or github) AND ≥1 with relevance ≥0.5.
2. `find_evidence_gaps()` returns list of (vendor, requirement_id) pairs failing sufficiency.
3. `diagnose_gap()` classifies each gap: `no_evidence`, `no_authoritative_source`, `low_relevance`, `insufficient_count`.
4. Gap type drives targeted query refinement strategy (alternative terminology, GitHub search, changelog, community search).
5. LangGraph conditional edge: if gaps exist AND iteration < 2, route to query generation; else route to scoring.
6. Maximum 2 research iterations enforced as hard cap.
7. Gap metadata stored in `ResearchState` for UI transparency.

**Executor**: @dev | **Quality Gate**: @architect
**Story Points**: 4

---

## Story 1.5 — SSE Progress Events

**As a** frontend,
**I want** to receive real-time progress events during pipeline execution,
**so that** the user sees meaningful progress feedback instead of a spinner.

### Acceptance Criteria
1. Pipeline emits structured progress events at key milestones.
2. Event format: `{"type": "progress", "phase": "<phase>", "pct": <0-100>, "message": "<text>"}`.
3. Phases: `research` (0–50%), `scoring` (50–80%), `synthesis` (80–95%), `completed` (100%).
4. `{"type": "started", "job_id": "<uuid>"}` emitted at pipeline start.
5. `{"type": "completed", "results": {...}}` emitted with full results on success.
6. `{"type": "error", "message": "<text>"}` emitted on pipeline failure.
7. Events serialized as SSE format: `data: {json}\n\n`.

**Executor**: @dev | **Quality Gate**: @architect
**Story Points**: 3
