# @sm Story Validation Report — SignalCore Vendor Research Tool

> **Prepared by**: River (@sm)
> **Requested by**: Morgan (@pm)
> **Date**: 2026-02-23
> **Stories reviewed**: 25 (Epics 1–5)
> **PRD version**: 1.0
> **Epic files reviewed**: epic-1 through epic-5

---

## Overall Assessment: PASS WITH NOTES

The story set is solid. A dev agent could pick up and implement the vast majority of stories without reading additional documentation. There are no blocking structural failures. The critical issues identified below are minor enough that a skilled dev agent could work around them, but they should be resolved to prevent ambiguity during implementation. There are no stories with broken executor/quality-gate assignments, no missing acceptance criteria families, and the build order logic is sound.

---

## Story-by-Story Review

---

### Story 2.1 — Pydantic Domain Models

- **Format**: Correct — uses team/"development team" as actor, appropriate for a foundational infrastructure story.
- **AC Quality**: Excellent. 13 numbered, specific, testable criteria. Field types, validators, and module locations all specified.
- **Executor != Quality Gate**: `@dev` / `@architect` — PASS
- **Dependencies**: Explicitly states "must be completed FIRST." No inbound dependencies. PASS
- **Tasks actionable**: Yes. Subtasks map one-to-one to AC items.
- **Dev Notes**: Outstanding. Pydantic v2 patterns, TypedDict rationale, and testing location all spelled out.
- **MoSCoW Alignment**: Must Have per epic-2. Story correctly omits a priority label but epic is unambiguous.
- **Issues**: None. This is the reference-quality story in the set.

---

### Story 3.1 — SQLite Schema & Database Initialization

- **Format**: Correct — "As a persistence layer / I want / so that."
- **AC Quality**: Good. 8 numbered criteria with exact column definitions and SQL pragmas.
- **Executor != Quality Gate**: `@data-engineer` / `@dev` — PASS (different roles, rule satisfied)
- **Dependencies**: States "Depends on Story 2.1 (models)." Correct — enums needed to understand field constraints.
- **Tasks actionable**: Yes. All DDL tasks are concrete.
- **Dev Notes**: Good. aiosqlite pattern shown, FastAPI lifespan pattern shown, SQLite quirks (INTEGER for bool, JSON for lists) documented.
- **MoSCoW Alignment**: Must Have per epic-3. PASS
- **Issues**:
  - **Minor**: The epic file specifies an additional index `scores(job_id, vendor)` (composite). The story AC only specifies `evidence(job_id)` and `scores(job_id)`. The composite index is dropped without explanation. Low impact but worth adding for the query pattern in `get_results()`.
  - **Minor**: `UNIQUE(job_id, vendor, requirement_id)` constraint on `scores` is specified in the epic but is implicit in the AC (it's in the DDL block). Could be an explicit numbered AC item for traceability.

---

### Story 3.2 — Repository Pattern Implementation

- **Format**: Correct.
- **AC Quality**: Strong. 7 criteria covering interface, implementation, SQL safety, assembly logic, sorting, dependency injection, and mock.
- **Executor != Quality Gate**: `@data-engineer` / `@dev` — PASS
- **Dependencies**: "Depends on Story 2.1 (models), Story 3.1 (schema)." Correct.
- **Tasks actionable**: Yes. Each repository method listed as a separate subtask.
- **Dev Notes**: Good. Singleton pattern, `get_results()` assembly pseudocode, `rankings_json` serialization all documented.
- **MoSCoW Alignment**: Must Have. PASS
- **Issues**:
  - **Minor**: `save_final_results()` is listed in the AC abstract method list but the `ResearchRepository` ABC signature in AC item 1 does not include it — it only appears in the task list (`save_final_results()`). The abstract method list in AC item 1 should include `save_final_results(job_id: str, summary: str, rankings: list[VendorRanking]) -> None` to be complete.

---

### Story 1.1 — LangGraph Query Generation Node

- **Format**: Correct.
- **AC Quality**: Good. 9 numbered criteria. Specifies function signature, concurrency approach, storage key format, fallback behavior.
- **Executor != Quality Gate**: `@dev` / `@architect` — PASS
- **Dependencies**: "Depends on Story 2.1 (ResearchState TypedDict), Story 5.1 (config with VENDORS, REQUIREMENTS)." Correct — these must exist first.
- **Tasks actionable**: Yes. Prompt creation, node implementation, and unit testing all listed.
- **Dev Notes**: Excellent. LLM client code, prompt template, example queries, fallback validation, and asyncio.gather usage all documented.
- **MoSCoW Alignment**: Must Have. PASS
- **Issues**:
  - **Minor**: The PRD build order specifies `E2-S1 → E3-S1 → E3-S2 → E1-S1`. Story 1.1's dependency declaration omits Story 3.2 (repository). While 1.1 itself doesn't write to the DB, the pipeline won't work end-to-end without it, and the dev agent should be aware. Not a blocking issue since the node itself doesn't call the repo.
  - **Minor**: AC item 6 says fallback uses `f"{vendor} {requirement} official documentation site:docs.{vendor.lower()}.com"`. The `site:` syntax with a variable domain is fragile (e.g., "site:docs.posthog.com" may not work for PostHog, whose docs are at posthog.com/docs). Flag for PM to review fallback template per vendor.

---

### Story 1.2 — Parallel Search Execution

- **Format**: Correct.
- **AC Quality**: Good. 8 criteria. Concurrency limit, search parameters, result storage format, failure handling, and progress events all specified.
- **Executor != Quality Gate**: `@dev` / `@architect` — PASS
- **Dependencies**: "Depends on Story 1.1 (query generation), Story 2.1 (ResearchState)." Correct.
- **Tasks actionable**: Yes.
- **Dev Notes**: Full implementation pattern provided verbatim from planning docs. Tavily result structure documented. Time filter parameter noted.
- **MoSCoW Alignment**: Must Have. PASS
- **Issues**:
  - **Minor**: AC item 7 says "Progress events emitted every 5 searches completed (update state for SSE)." This creates a coupling to Story 1.5 (SSE progress queue). The dependency declaration only mentions Stories 1.1 and 2.1. Story 1.5 should be listed as a dependency (or at minimum a note: "progress emission requires progress_queue from Story 1.5"). As written, a dev agent implementing this story in isolation before 1.5 won't have the queue mechanism.

---

### Story 1.3 — Structured Evidence Extraction

- **Format**: Correct.
- **AC Quality**: Strong. 10 criteria covering node signature, input aggregation, all Evidence fields, source classification, conservative extraction, multiple claims per result, storage, persistence, empty case, and concurrency.
- **Executor != Quality Gate**: `@dev` / `@architect` — PASS
- **Dependencies**: "Depends on Story 1.2 (raw_results), Story 2.1 (Evidence model), Story 3.2 (repository)." Correct and complete.
- **Tasks actionable**: Yes. Prompt file, node implementation with content truncation, and testing all listed.
- **Dev Notes**: Excellent. Full extraction prompt, source type classification heuristics, content truncation limit, repository call pattern.
- **MoSCoW Alignment**: Must Have. PASS
- **Issues**: None material.

---

### Story 1.4 — Evidence Gap Analysis & Research Loop

- **Format**: Correct.
- **AC Quality**: Strong. 8 criteria covering all four gap types, conditional edge routing, iteration cap, and gap metadata storage.
- **Executor != Quality Gate**: `@dev` / `@architect` — PASS
- **Dependencies**: "Depends on Story 1.3 (evidence extracted), Story 2.1 (GapType enum in models)." Correct.
- **Tasks actionable**: Yes. All four gap-related functions listed plus the LangGraph wiring.
- **Dev Notes**: Verbatim code for `check_evidence_sufficiency()` and `diagnose_gap()`. Conditional edge code. State update pattern.
- **MoSCoW Alignment**: Must Have. PASS
- **Issues**:
  - **Minor/Ambiguity**: AC item 5 shows `should_continue_research()` returning "continue" or "proceed_to_scoring" but the task list code shows it returning "continue" or "proceed" (shortened). The `add_conditional_edges` call in the task list also uses `"proceed"` not `"proceed_to_scoring"`. The AC and code are inconsistent. One string value must be canonical — recommend standardising to `"proceed_to_scoring"` in both places for clarity.
  - **Minor**: The story notes that refined query generation "may reuse `generate_queries` node with gap context appended to prompt." This is underspecified — it could mean calling the same node again (which LangGraph routing handles) or calling a separate function. Given the loop routes back to `generate_queries`, the implementation is implied, but documenting that the second iteration will call the same node with gap context already in state would help the dev agent.

---

### Story 1.5 — SSE Progress Events

- **Format**: Correct — "As a frontend user."
- **AC Quality**: Good. 9 criteria covering all event types, SSE formatting, queue mechanism, and density of progress updates.
- **Executor != Quality Gate**: `@dev` / `@architect` — PASS
- **Dependencies**: "Depends on Story 2.1 (ResearchState with progress_queue field), Story 3.3 (FastAPI SSE endpoint)."
- **Tasks actionable**: Yes. Queue setup, helper function, node updates, SSE generator, and integration test all listed.
- **Dev Notes**: Full SSE generator pattern and queue mechanism shown.
- **MoSCoW Alignment**: Must Have. PASS
- **Issues**:
  - **Circular dependency flag**: Story 1.5 says it depends on Story 3.3, and Story 3.3 says it depends on Story 1.5. This is a mutual dependency. In practice, what's needed is: (a) the `progress_queue` field in `ResearchState` (from 2.1), and (b) the SSE generator pattern (which lives in `main.py`). The actual LangGraph nodes that call `emit_progress()` are separate from the FastAPI endpoint. The dependency should be restructured:
    - Story 1.5 depends on: Story 2.1 (ResearchState)
    - Story 3.3 depends on: Story 1.5 (emit_progress helper and queue pattern)
    - This is workable if 1.5 is scoped as "implement the queue + emit_progress helper + update all nodes to call it" and 3.3 is scoped as "implement the FastAPI generator that reads from the queue." The current story files largely reflect this split, but the dependency declarations create a confusing cycle. Recommend PM clarify the dependency direction.
  - **Minor**: AC item 3 says phases and percentages are `research (5–50%)`, `scoring (50–80%)`, `synthesis (80–95%)`. The PRD epic-1 AC states `research (0–50%)`. The story uses 5% as the starting point (after query generation). Inconsistency with PRD is minor but should be made canonical.

---

### Story 2.2 — LLM Capability Assessment

- **Format**: Correct.
- **AC Quality**: Strong. 8 criteria covering node signature, LLM inputs, output schema, conservative guidance, relevance filter, storage, failure defaults, and concurrency.
- **Executor != Quality Gate**: `@dev` / `@architect` — PASS
- **Dependencies**: "Depends on Story 1.3 (evidence in state), Story 2.1 (LLMAssessment model)." Correct.
- **Tasks actionable**: Yes.
- **Dev Notes**: Full assessment prompt, `with_structured_output` usage, evidence formatting function shown.
- **MoSCoW Alignment**: Must Have. PASS
- **Issues**:
  - **Minor**: AC item 5 says "filter evidence where relevance >= 0.3 before passing to LLM." This filter is applied only here. The evidence stored in the state (and DB) still includes low-relevance items, which is correct. However the story could note that `compute_confidence()` (Story 2.4) uses the full evidence list (not filtered), while assessment uses the filtered list. This distinction matters for reproducibility.

---

### Story 2.3 — Deterministic Score Computation

- **Format**: Correct.
- **AC Quality**: Excellent. 10 criteria with exact formulas, weights, lookup values, purity constraint, performance budget, and persistence.
- **Executor != Quality Gate**: `@dev` / `@architect` — PASS
- **Dependencies**: "Depends on Story 2.2 (LLMAssessment), Story 2.1 (ScoreResult model), Story 3.2 (repository)." Correct.
- **Tasks actionable**: Yes. Engine file, lookup dicts, formula, node, and tests all listed.
- **Dev Notes**: Verbatim implementation from planning docs. ScoreResult assembly shown. Test fixtures included.
- **MoSCoW Alignment**: Must Have. PASS
- **Issues**:
  - **Minor**: AC item 3 specifies Evidence Strength uses `len([e for e in evidence if e.supports_requirement])` (supporting count). The PRD FR5 description says "Evidence Strength (30%)" without distinguishing "supporting." The story is more specific than the PRD, which is correct — this is the right implementation. No issue with correctness, but worth noting for transparency.

---

### Story 2.4 — Confidence Score Computation

- **Format**: Correct.
- **AC Quality**: Excellent. 9 criteria with exact component weights, authority weights per source type, recency thresholds, consistency formula, clamping, and empty-list behavior.
- **Executor != Quality Gate**: `@dev` / `@architect` — PASS
- **Dependencies**: "Depends on Story 2.1 (Evidence model)." Correct — this function is pure and only needs the model.
- **Tasks actionable**: Yes. All 4 components listed as subtasks plus date parsing utility.
- **Dev Notes**: Full verbatim implementation. `python-dateutil` dependency noted.
- **MoSCoW Alignment**: Must Have. PASS
- **Issues**:
  - **Minor**: `python-dateutil` is listed in the dev notes as a required pip package but Story 5.1 must add it to `requirements.txt`. Checking Story 5.1 — it does include `python-dateutil>=2.9.0`. Dependency satisfied. PASS.

---

### Story 2.5 — Weighted Vendor Ranking

- **Format**: Correct — "As a results consumer."
- **AC Quality**: Strong. 9 criteria covering formula, sort order, VendorRanking fields, all-vendors return, tiebreaker, LangGraph node, persistence, and purity.
- **Executor != Quality Gate**: `@dev` / `@architect` — PASS
- **Dependencies**: "Depends on Story 2.3 + 2.4 (scores + confidence), Story 2.1 (VendorRanking model)." Correct.
- **Tasks actionable**: Yes.
- **Dev Notes**: Verbatim implementation. Formula clarification note (naturally produces 0–10). Requirement weights shown with sum check.
- **MoSCoW Alignment**: Must Have. PASS
- **Issues**:
  - **Minor**: The `save_final_results()` call is listed in AC item 8 ("persisted via `repository.save_final_results()`") but `save_final_results()` is defined in Story 3.2. A dev implementing 2.5 who hasn't implemented 3.2 yet will need to stub this call. The dependency declaration should include Story 3.2. As written it only mentions 2.3, 2.4, and 2.1.

---

### Story 3.3 — POST /api/research with SSE Streaming

- **Format**: Correct.
- **AC Quality**: Strong. 10 criteria covering request body, job creation, content-type, event stream order, SSE format, frontend consumption method, error handling, status persistence, and CORS.
- **Executor != Quality Gate**: `@dev` / `@architect` — PASS
- **Dependencies**: "Depends on Story 1.5 (progress events), Story 2.5 (pipeline final results), Story 3.1 + 3.2 (repository)." Correct. This is the integration point.
- **Tasks actionable**: Yes.
- **Dev Notes**: Full FastAPI SSE pattern shown. CORS config shown. Frontend fetch pattern documented for README.
- **MoSCoW Alignment**: Must Have. PASS
- **Issues**:
  - **Note on the circular dependency with 1.5**: See Story 1.5 review above. The dependency direction between 1.5 and 3.3 needs clarification.
  - **Minor**: The `build_initial_state()` function is referenced in the SSE endpoint code but never defined or described in any story. It's implied, but no story explicitly owns its implementation. The dev agent will need to infer it creates the `ResearchState` TypedDict. Recommend Story 1.1 or 3.3 claim ownership of this utility function.

---

### Story 3.4 — GET /api/research/{job_id}

- **Format**: Correct.
- **AC Quality**: Good. 8 criteria covering all four response cases (completed, running, failed, not found), matrix structure, and performance target.
- **Executor != Quality Gate**: `@dev` / `@architect` — PASS
- **Dependencies**: "Depends on Story 3.2 (repository.get_results()), Story 2.1 (ResearchResults model)." Correct.
- **Tasks actionable**: Yes. Simple 3-task story.
- **Dev Notes**: Full route implementation shown. Serialization note for Pydantic v2.
- **MoSCoW Alignment**: Must Have. PASS
- **Issues**: None material.

---

### Story 3.5 — GET /api/jobs Listing

- **Format**: Correct but minimal — "As a frontend / I want to list previous research jobs / so that users can navigate to past research results." The "so that" is a bit weak (no user goal articulated). Functional but slightly below the quality bar of other stories.
- **AC Quality**: Adequate. 5 criteria. Minimal but sufficient.
- **Executor != Quality Gate**: `@dev` / `@architect` — PASS
- **Dependencies**: "Depends on Story 3.2 (repository.list_jobs())." Correct.
- **Tasks actionable**: Yes (two subtasks is thin but the story is simple).
- **Dev Notes**: Route implementation shown.
- **MoSCoW Alignment**: Marked "Could Have" in epic-3. Story does not carry a visible priority label.
- **Issues**:
  - **Minor**: The story lacks a `## Status` section entry for priority/MoSCoW. All other stories have `Status: Draft`. This one has it too, but there's no MoSCoW tag visible in the story file. Minor documentation gap.
  - **Minor**: The "so that" clause says "users can navigate to past research results" — but that navigation behavior is actually implemented in Story 5.4 (job history page). This story only exposes the API. Recommend refining the "so that" to: "so that the frontend can display a history of research runs."
  - **Minor**: Testing section is very thin ("Test: empty list, Test: jobs sorted newest-first"). Edge cases like limit=50 enforcement and running/failed job inclusion are worth testing but not listed.

---

### Story 3.6 — Static File Serving & App Entry Point

- **Format**: Correct — "As a developer."
- **AC Quality**: Good. 6 criteria.
- **Executor != Quality Gate**: `@dev` / `@architect` — PASS
- **Dependencies**: None declared. Appropriate — this is infrastructure that can be set up standalone.
- **Tasks actionable**: Yes.
- **Dev Notes**: Code shown. Note about `python-multipart` included.
- **MoSCoW Alignment**: Marked "Could Have" in epic-3. Story does not carry a visible MoSCoW tag.
- **Issues**:
  - **Minor**: The epic marks E3-S5 and E3-S6 as "Could Have," but `3.6.static-file-serving.md` is the entry point that makes `uvicorn app.main:app --reload` work and calls `create_db_and_tables()` on startup. This story is effectively required for any dev environment to function, making "Could Have" seem like a labeling error. Recommend the PM revisit the MoSCoW label — likely Should Have or Must Have.
  - **Minor**: The story does not mention CORS configuration, which is set up in `main.py` alongside static file serving. Story 3.3 mentions CORS, but if a dev builds 3.6 before 3.3, CORS won't be in `main.py` yet. A note would prevent this gap.

---

### Story 4.1 — Comparison Matrix

- **Format**: Correct — "As a researcher/evaluator."
- **AC Quality**: Strong. 8 criteria with exact color hex values, grouping logic, null handling, and responsive behavior.
- **Executor != Quality Gate**: `@dev` / `@architect` — PASS
- **Dependencies**: "Depends on Story 3.4 (GET results endpoint providing matrix data)." Correct.
- **Tasks actionable**: Yes. HTML structure, JS function, CSS, and manual test all listed.
- **Dev Notes**: JSON structure example shown. Score color function shown. Priority grouping logic shown. Responsive CSS shown.
- **MoSCoW Alignment**: Must Have. PASS
- **Issues**:
  - **Minor**: AC item 7 says "matrix container horizontally scrollable on screens < 768px" but AC item 3 specifies background colors using hex. The PRD Section 3.3 says `<4 = red (#e74c3c)` but the story says the same. No conflict. PASS.
  - **Minor**: The story says "Testing — Manual testing with fixture JSON data" with "No automated UI tests (Could Have for this assignment)." This is fine for this context, but the testing section is notably weaker than backend stories. Not a blocker.

---

### Story 4.2 — Confidence Visualization

- **Format**: Correct.
- **AC Quality**: Good. 6 criteria with exact CSS values, confidence thresholds, and display format.
- **Executor != Quality Gate**: `@dev` / `@architect` — PASS
- **Dependencies**: "Depends on Story 4.1 (matrix rendering)." Correct — extends cell rendering.
- **Tasks actionable**: Yes.
- **Dev Notes**: Cell HTML structure and CSS classes shown.
- **MoSCoW Alignment**: Should Have per epic-4. Story does not carry a visible MoSCoW label.
- **Issues**:
  - **Minor**: The PRD Section 3.3 states "confidence: opacity level (high=full, medium=70%, low=40%) + dashed border for low confidence." The story uses 80% and 60% opacity instead of 70% and 40%. Minor deviation from PRD. Not blocking but should be made canonical.

---

### Story 4.3 — Evidence Drill-Down Panel

- **Format**: Correct.
- **AC Quality**: Strong. 8 criteria covering panel trigger, header content, justification section, limitations section, evidence display, badge colors, close behavior, performance, and multi-click behavior.
- **Executor != Quality Gate**: `@dev` / `@architect` — PASS
- **Dependencies**: "Depends on Story 4.1 (matrix with click handlers), Story 4.2 (evidence data in memory)."
- **Tasks actionable**: Yes. Panel HTML, JS function with all sections, close behavior, click wiring, and CSS all listed.
- **Dev Notes**: Full HTML structure, JS badge colors, in-memory access pattern, CSS animation shown.
- **MoSCoW Alignment**: Should Have per epic-4. PASS
- **Issues**:
  - **Minor**: The dependency on Story 4.2 is slightly off. The evidence data in memory comes from Story 4.1 loading results from the API — not specifically Story 4.2. Story 4.2 only adds confidence CSS. The dependency should list Story 4.1, not 4.2. This is a documentation inaccuracy that could confuse sequencing.

---

### Story 4.4 — Executive Summary Display

- **Format**: Correct.
- **AC Quality**: Good. 7 criteria covering placement, paragraph rendering, heading, rankings visualization, readability constraints, LLM synthesis node, and fallback.
- **Executor != Quality Gate**: `@dev` / `@architect` — PASS
- **Dependencies**: "Depends on Story 2.5 (rankings in state), Story 3.4 (summary in results JSON), Story 4.1 (display context)." Correct.
- **Tasks actionable**: Yes. Backend synthesis node AND frontend rendering both covered in the same story.
- **Dev Notes**: Full synthesis prompt from planning docs. Pipeline node order. Frontend JS function shown.
- **MoSCoW Alignment**: Should Have per epic-4. PASS
- **Issues**:
  - **Split story concern**: Story 4.4 owns both the backend `generate_summary` LangGraph node (creating `app/prompts/synthesis.py` + a new graph node) AND the frontend summary display. This is more than other "4.x" frontend stories own. A backend synthesis node is a non-trivial LangGraph addition. If a dev agent is handed only this story, they are implementing two distinctly different things. This is workable but creates a higher risk of the story being underestimated.
  - **Minor**: The `generate_summary` node is not mentioned in any Epic 1 or Epic 2 story — it lives here, in the frontend epic. The build order in the PRD shows `E2-S5 → E1-S5 → E3-S3 → ...` but never mentions the synthesis node explicitly. It surfaces implicitly via this story. A dev agent implementing Epic 1 stories might not realize a synthesis node needs to exist in the LangGraph graph.
  - **Minor**: AC item 6 says "Executive summary generated by LLM as LangGraph `synthesize` node — see Dev Notes." This is an implementation detail that belongs in Dev Notes, not in an Acceptance Criterion. An AC should be user-observable. Recommend restating as: "Summary text in `results.summary` is non-empty after pipeline completes."

---

### Story 4.5 — Real-time Progress Display

- **Format**: Correct.
- **AC Quality**: Good. 8 criteria covering button state, progress bar fill, status message, phase label, disable state, completion transition, error state, and animation.
- **Executor != Quality Gate**: `@dev` / `@architect` — PASS
- **Dependencies**: "Depends on Story 1.5 (SSE events from pipeline), Story 3.3 (POST endpoint)." Correct.
- **Tasks actionable**: Yes. HTML elements, `consumeSSE()` function, CSS animation, retry logic all listed.
- **Dev Notes**: Full SSE consumption pattern shown. CSS progress bar shown.
- **MoSCoW Alignment**: Could Have per epic-4. PASS
- **Issues**:
  - **Minor**: The SSE consumption code in Dev Notes does not show the "Retry" button implementation despite AC item 7 requiring it. The retry behavior should be described (does it re-trigger `runResearch()`? Does it reset state?).
  - **Minor**: AC item 8 says "progress bar width transition is CSS animated." This is already captured in Story 5.2 (UI styling). Duplication is fine, but could cause conflicting implementations if both stories try to define the same CSS.

---

### Story 5.1 — Project Setup & Environment

- **Format**: Correct.
- **AC Quality**: Strong. 10 criteria with exact file names, dependency list, config structure, and startup verification.
- **Executor != Quality Gate**: `@dev` / `@architect` — PASS
- **Dependencies**: "This story should be implemented FIRST." No dependencies listed. Correct.
- **Tasks actionable**: Yes. Each file is a separate task.
- **Dev Notes**: Full `requirements.txt` contents, `config.py` with Settings class, REQUIREMENTS list with weights, and weight sum verification all included.
- **MoSCoW Alignment**: Should Have per epic-5. PASS (note: the build order in PRD says this is the first story to implement despite being in Epic 5 — the story correctly calls this out).
- **Issues**:
  - **Minor**: The `requirements.txt` in Dev Notes uses `>=` version pins ("fastapi>=0.115.0"). AC item 1 says "pinned versions." These are minimum-bound pins, not exact pins (e.g., `fastapi==0.115.0`). Minimum bounds are actually safer for a demo/assignment context, but the AC says "pinned" which typically means exact. Recommend the PM clarify intent or change AC to "minimum-version-bounded."
  - **Minor**: `httpx` is in requirements.txt (for testing) but no test dependency section. Test-only dependencies mixed with runtime dependencies. This is standard for simple projects but worth noting for maintainability.

---

### Story 5.2 — UI Styling Polish

- **Format**: Correct.
- **AC Quality**: Adequate. 7 criteria. Some criteria overlap with Stories 4.1 and 4.2.
- **Executor != Quality Gate**: `@dev` / `@architect` — PASS
- **Dependencies**: "Depends on Stories 4.1–4.5 (all UI elements existing)." Correct.
- **Tasks actionable**: Yes.
- **Dev Notes**: Font stack, sticky header CSS, rank badge example shown.
- **MoSCoW Alignment**: Could Have per epic-5. Story correctly flags this as "could have." PASS
- **Issues**:
  - **Minor**: AC items 2 (matrix table sticky header) and 6 (responsive < 768px) are already specified in Stories 4.1 and 4.2. Implementing both could produce conflicting CSS or duplicate work. Recommend the PM clarify that Story 5.2 is a polish/refinement pass, not a re-implementation of items already in 4.x.

---

### Story 5.3 — README & Documentation

- **Format**: Correct.
- **AC Quality**: Good. 8 criteria covering all major README sections.
- **Executor != Quality Gate**: `@dev` / `@architect` — PASS
- **Dependencies**: None declared. Appropriate — README can be written last.
- **Tasks actionable**: Yes.
- **Dev Notes**: Quick start section, API key links, runtime estimate all shown.
- **MoSCoW Alignment**: Should Have per epic-5. PASS
- **Issues**: None material.

---

### Story 5.4 — Job History Page

- **Format**: Correct.
- **AC Quality**: Adequate. 7 criteria covering section visibility, API calls, job display, view button, empty state, failed job handling, and priority label.
- **Executor != Quality Gate**: `@dev` / `@architect` — PASS
- **Dependencies**: "Depends on Story 3.5 (GET /api/jobs), Story 3.4 (GET results endpoint)." Correct.
- **Tasks actionable**: Yes.
- **Dev Notes**: Timestamp formatting, status badge colors shown.
- **MoSCoW Alignment**: Could Have per epic-5. Story correctly flags this. PASS
- **Issues**: None material.

---

## FR Coverage Map

| FR | Requirement | Covered By |
|----|-------------|------------|
| FR1 | LangGraph pipeline — 2 queries per vendor×requirement pair | Story 1.1 |
| FR2 | Tavily parallel search, max 5 concurrent, AsyncTavilyClient | Story 1.2 |
| FR3 | Structured Evidence extraction with all 7 fields | Story 1.3 |
| FR4 | Evidence sufficiency checking — ≥2 sources, ≥1 authoritative, ≥1 relevant. Max 2 iterations | Story 1.4 |
| FR5 | Per-requirement score (0–10) — 4-component hybrid formula | Story 2.3 |
| FR6 | Confidence score (0–1) — fully deterministic from evidence metadata | Story 2.4 |
| FR7 | Weighted vendor rankings | Story 2.5 |
| FR8 | SQLite persistence via ResearchRepository + aiosqlite | Stories 3.1, 3.2 |
| FR9 | POST /api/research — pipeline trigger with SSE streaming | Story 3.3 |
| FR10 | GET /api/research/{job_id} — cached results retrieval | Story 3.4 |
| FR11 | GET /api/jobs — job listing | Story 3.5 |
| FR12 | Frontend comparison matrix — vendors × requirements | Story 4.1 |
| FR13 | Evidence drill-down panel | Story 4.3 |
| FR14 | Executive summary display | Story 4.4 |
| FR15 | Real-time progress via SSE | Stories 1.5, 3.3, 4.5 |

**Coverage verdict: ALL 15 functional requirements covered. No gaps.**

---

## NFR Coverage Notes

| NFR | Addressed By |
|-----|-------------|
| NFR1 (API rate limits, full run) | Story 1.2 (semaphore 5), Story 1.4 (max 2 iterations) |
| NFR2 (local only) | Story 5.1 (no cloud infra), Story 3.6 (uvicorn entry point) |
| NFR3 (deterministic scoring) | Stories 2.3, 2.4 (pure functions, no LLM in scoring) |
| NFR4 (Python 3.11+, Pydantic v2) | Story 2.1 (Pydantic v2 patterns), Story 5.1 (requirements.txt) |
| NFR5 (repository pattern / PostgreSQL swap) | Story 3.2 (abstract ABC) |
| NFR6 (no build tools, pure HTML/JS) | Stories 4.1–4.5 (pure JS in index.html) |
| NFR7 (graceful evidence gaps) | Story 1.4 (gap analysis), Stories 2.4 (confidence=0 for no evidence) |
| NFR8 (API keys from env) | Story 5.1 (pydantic-settings, .env.example) |

**NFR coverage: Complete.**

---

## Critical Issues (Must Fix)

### CRIT-1: Circular Dependency Between Stories 1.5 and 3.3

**Story 1.5** Dev Notes state: "Depends on Story 3.3 (FastAPI SSE endpoint)."
**Story 3.3** Dev Notes state: "Depends on Story 1.5 (progress events)."

This is a circular dependency in the documentation. In practice, the implementation is separable:
- Story 1.5 should depend only on Story 2.1 (ResearchState with progress_queue field)
- Story 3.3 should depend on Story 1.5 (the emit_progress helper and queue pattern)

**Action for @pm**: Remove Story 3.3 from Story 1.5's dependency list. Confirm Story 3.3 depends on 1.5.

### CRIT-2: Missing `build_initial_state()` Ownership

The `build_initial_state()` function is referenced in Story 3.3 Dev Notes and Story 1.5 Dev Notes as:
```python
state = build_initial_state(job_id, queue)
```
This function is never defined in any story. No story claims responsibility for implementing it. A dev agent will discover this gap mid-implementation.

**Action for @pm**: Assign `build_initial_state()` to Story 1.1 (query generation node, which owns the initial state composition) or Story 3.3 (which calls it). Add a task item in the chosen story.

### CRIT-3: `generate_summary` LangGraph Node Has No Story in Epic 1 or 2

The synthesis node (`generate_summary`) is described in Story 4.4 under a frontend epic. It creates a new LangGraph node (`app/prompts/synthesis.py`, a new graph node in `pipeline.py`), but the LangGraph `pipeline.py` construction is never mentioned in any explicit story. Epic 1 contains the research nodes; Epic 2 contains the scoring nodes; but the synthesis node that closes the LangGraph graph appears only in a frontend story.

**Action for @pm**: Either (a) move the `generate_summary` backend node implementation into a new Epic 1 or 2 story, or (b) explicitly note in Story 4.4 that it owns the complete `pipeline.py` graph construction including all node registrations and edge wiring.

---

## Minor Recommendations

### REC-1: Story 3.6 MoSCoW Label Should Be Revisited
The epic marks E3-S6 (static file serving) as "Could Have," but this story initializes the FastAPI app entry point and calls `create_db_and_tables()`. Without it, no other story can be run end-to-end. Suggest upgrading to "Must Have" or at minimum "Should Have."

### REC-2: Story 4.4 AC Item 6 Should Be Rephrased
"Executive summary generated by LLM as LangGraph `synthesize` node" is an implementation detail, not a testable criterion. Suggest replacing with: "After pipeline completes, `results.summary` contains a non-empty string of 3–4 prose paragraphs."

### REC-3: Story 4.3 Dependency on 4.2 Is Incorrect
The dependency declaration says "Depends on Story 4.2" for evidence data, but evidence data comes from Story 4.1. Story 4.2 only adds CSS classes. Correct to: "Depends on Story 4.1."

### REC-4: Story 2.5 Missing Story 3.2 in Dependency List
`save_final_results()` is called in the `compute_rankings()` node. Story 3.2 should appear in Story 2.5's dependency declarations.

### REC-5: Story 4.4 Scope Straddles Backend and Frontend Layers
The story owns both `generate_summary` (LangGraph node, backend) and `renderSummary` (JavaScript, frontend). Consider whether a dev agent can realistically implement both in one story, or whether the backend synthesis node should be separated. Low risk for this project size, but worth flagging.

### REC-6: Story 1.1 Fallback URL Template May Fail for Some Vendors
AC item 6 uses `site:docs.{vendor.lower()}.com` which is fragile for PostHog (docs at posthog.com/docs) and Braintrust (braintrust.dev). Recommend predefining fallback URLs per vendor in `config.py` rather than constructing them dynamically.

### REC-7: Story 1.2 Progress Event Dependency Gap
AC item 7 ("emit progress events every 5 searches") implicitly requires the `progress_queue` from Story 1.5. Story 1.2's dependency declaration should include Story 1.5 (or at minimum note: "progress queue must exist in state before this runs").

### REC-8: Story 5.1 Pin Strategy Inconsistency
AC item 1 says "pinned versions" but the Dev Notes use `>=` bounds. Clarify whether exact pins (`==`) or minimum bounds (`>=`) are intended. For a demo/assignment, minimum bounds are pragmatically better.

### REC-9: Story 4.2 Opacity Values Differ From PRD
PRD Section 3.3 specifies medium=70% opacity, low=40% opacity. Story 4.2 AC specifies 80% and 60%. Align one or the other. No functional impact, but creates a discrepancy between spec and acceptance test.

### REC-10: Synthesis Node Missing from PRD Build Order
The PRD build order (`E2-S1 → E3-S1 → ... → E4-S4 → E5-S1 → ...`) does not explicitly name the synthesis node step. The build order should include E4-S4 with a note that it introduces a new LangGraph node that modifies `pipeline.py`.

---

## Build Order Validation

**PRD-specified critical path**:
`E2-S1 → E3-S1 → E3-S2 → E1-S1 → E1-S2 → E1-S3 → E1-S4 → E2-S2 → E2-S3 → E2-S4 → E2-S5 → E1-S5 → E3-S3 → E3-S4 → E3-S5 → E3-S6 → E4-S5 → E4-S1 → E4-S2 → E4-S3 → E4-S4 → E5-S1 → E5-S2 → E5-S3 → E5-S4`

**Validation against declared story dependencies**:

| Position | Story | Declared Deps | Deps Satisfied at This Point? |
|----------|-------|---------------|-------------------------------|
| 1 | E2-S1 (Domain Models) | None | YES |
| 2 | E3-S1 (SQLite Schema) | 2.1 | YES |
| 3 | E3-S2 (Repository) | 2.1, 3.1 | YES |
| 4 | E1-S1 (Query Gen) | 2.1, 5.1 | PARTIAL — 5.1 not yet done |
| 5 | E1-S2 (Parallel Search) | 1.1, 2.1 | YES |
| 6 | E1-S3 (Evidence Extract) | 1.2, 2.1, 3.2 | YES |
| 7 | E1-S4 (Gap Analysis) | 1.3, 2.1 | YES |
| 8 | E2-S2 (LLM Assessment) | 1.3, 2.1 | YES |
| 9 | E2-S3 (Score Computation) | 2.2, 2.1, 3.2 | YES |
| 10 | E2-S4 (Confidence) | 2.1 | YES |
| 11 | E2-S5 (Ranking) | 2.3, 2.4, 2.1 | YES — but 3.2 missing (see REC-4) |
| 12 | E1-S5 (SSE Progress) | 2.1, 3.3 | PARTIAL — 3.3 not yet done |
| 13 | E3-S3 (POST SSE endpoint) | 1.5, 2.5, 3.1, 3.2 | YES — 1.5 just done |
| 14 | E3-S4 (GET results) | 3.2, 2.1 | YES |
| 15 | E3-S5 (GET jobs) | 3.2 | YES |
| 16 | E3-S6 (Static file serving) | None | YES |
| 17 | E4-S5 (Progress display) | 1.5, 3.3 | YES |
| 18 | E4-S1 (Matrix) | 3.4 | YES |
| 19 | E4-S2 (Confidence viz) | 4.1 | YES |
| 20 | E4-S3 (Drill-down) | 4.1, 4.2 | YES — but dep on 4.2 is wrong (see REC-3) |
| 21 | E4-S4 (Summary display) | 2.5, 3.4, 4.1 | YES |
| 22 | E5-S1 (Project setup) | None | YES — but NOTE: should be FIRST |
| 23 | E5-S2 (Styling) | 4.1–4.5 | YES |
| 24 | E5-S3 (README) | None | YES |
| 25 | E5-S4 (Job history) | 3.5, 3.4 | YES |

**Two anomalies found**:

1. **E1-S1 (position 4) depends on E5-S1** which is at position 22 in the build order. The story correctly notes "Story 5.1 should be implemented FIRST" and the Epic 5 file confirms it. However the PRD build order places E5-S1 at position 22. This is the most significant sequencing issue — Story 5.1 creates `app/config.py` (VENDORS, REQUIREMENTS constants) which Story 1.1 needs. In practice the dev agent should implement 5.1 first despite its Epic 5 numbering. The build order in the PRD must be treated as the authority, not the epic number. A prominent note in the story set would prevent confusion.

2. **E1-S5 (position 12) depends on E3-S3** which is at position 13. This is the circular dependency identified in CRIT-1. The fix (removing the 3.3 dependency from 1.5) resolves this.

**Verdict**: The build order is safe with two caveats: (a) treat E5-S1 as the true first story despite its numbering, and (b) resolve the 1.5/3.3 circular dependency. All other stories can be implemented in the specified order.

---

## Summary Scorecard

| Category | Score | Notes |
|----------|-------|-------|
| Story format (As a / I want / so that) | 25/25 PASS | All stories have proper format |
| Acceptance criteria quality | 23/25 PASS WITH NOTES | 3.5 thin, 4.4 has one impl-detail AC |
| Executor != Quality Gate | 25/25 PASS | No violations |
| Dependencies declared | 22/25 PASS WITH NOTES | 1.5/3.3 circular, 2.5 missing 3.2, 4.3 wrong dep |
| Sequencing safety | PASS WITH NOTES | E5-S1 must go first; circular dep must be fixed |
| FR coverage | 15/15 PASS | All FRs covered |
| Tasks actionable | 25/25 PASS | All stories have concrete implementation tasks |
| Dev Notes sufficiency | 24/25 PASS | build_initial_state() undefined, synthesis node unowned |
| MoSCoW alignment | 23/25 PASS WITH NOTES | 3.6 likely mis-labeled; 3.5/4.2 missing labels |

---

*Report by River (@sm) — 2026-02-23*
*3 Critical Issues identified | 10 Minor Recommendations | 0 Story rewrites required*
*Recommendation: PM to address CRIT-1 through CRIT-3 before dev sprint begins. Minor items can be addressed inline during implementation.*
