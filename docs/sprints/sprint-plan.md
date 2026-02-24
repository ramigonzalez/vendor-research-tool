# SignalCore Vendor Research Tool — Sprint Plan

> **Created by**: River (@sm) | **Date**: 2026-02-23
> **Total Stories**: 25 | **Total Points**: 61
> **Constraint**: 2–3 hour time-boxed prototype, single developer

---

## Wave Structure

Stories are organized into **waves** based on dependency resolution. Within each wave, stories can be executed **in parallel** (no inter-dependencies). A wave can only start when ALL its blocking dependencies from previous waves are complete.

---

## Wave 0 — Foundation (2 stories, 4 pts)

> **Goal**: Project scaffold + domain models. Everything else depends on these.

| Story | Name | Pts | MoSCoW | Depends On |
|-------|------|-----|--------|------------|
| 5.1 | Project Setup & Environment | 2 | Must Have | — |
| 2.1 | Pydantic Domain Models | 2 | Must Have | — |

**Parallelism**: `5.1 ∥ 2.1` — these can run simultaneously. Story 5.1 creates the scaffold (`config.py`, `.env`, `requirements.txt`, `__init__.py` files). Story 2.1 creates `app/models.py`. No overlap.

**Exit criteria**: `uvicorn app.main:app` starts without import errors; all Pydantic models pass validation tests.

---

## Wave 1 — Persistence + Pipeline Entry (4 stories, 12 pts)

> **Goal**: Database layer + first pipeline nodes + SSE infrastructure.

| Story | Name | Pts | MoSCoW | Depends On |
|-------|------|-----|--------|------------|
| 3.1 | SQLite Schema & DB Init | 2 | Must Have | 2.1 |
| 1.1 | Query Generation Node | 3 | Must Have | 2.1, 5.1 |
| 1.5 | SSE Progress Events | 3 | Must Have | 2.1 |
| 2.4 | Confidence Score Computation | 2 | Must Have | 2.1 |

**Parallelism**: `3.1 ∥ 1.1 ∥ 1.5 ∥ 2.4` — all four depend only on Wave 0 outputs.

**Why 2.4 here**: Confidence computation depends only on the `Evidence` model from 2.1. It's a pure function with no pipeline dependency — can be built and tested in isolation with fixtures.

**Exit criteria**: SQLite tables created; query generation produces 48 queries; progress events emit correctly; confidence function passes unit tests.

---

## Wave 2 — Repository + Search + Evidence (3 stories, 11 pts)

> **Goal**: Repository pattern enables persistence; search executes against Tavily; evidence extraction processes results.

| Story | Name | Pts | MoSCoW | Depends On |
|-------|------|-----|--------|------------|
| 3.2 | Repository Pattern Implementation | 3 | Must Have | 2.1, 3.1 |
| 1.2 | Parallel Search Execution | 4 | Must Have | 1.1, 2.1, 1.5 |
| 1.3 | Evidence Extraction | 4 | Must Have | 1.2, 2.1, 3.2 |

**Parallelism**: `3.2 ∥ 1.2` — then `1.3` after both complete.

> **Note**: Story 1.3 depends on both 1.2 (raw results) and 3.2 (repository for persistence). It cannot start until both are done. Stories 3.2 and 1.2 can run in parallel.

**Exit criteria**: Repository CRUD operations pass; 48 Tavily searches execute with semaphore; structured Evidence objects extracted from raw results.

---

## Wave 3 — Gap Analysis + Scoring Core (3 stories, 10 pts)

> **Goal**: Complete the research loop and build the scoring engine.

| Story | Name | Pts | MoSCoW | Depends On |
|-------|------|-----|--------|------------|
| 1.4 | Evidence Gap Analysis & Loop | 4 | Must Have | 1.3, 2.1 |
| 2.2 | LLM Capability Assessment | 3 | Must Have | 1.3, 2.1 |
| 2.3 | Score Computation | 3 | Must Have | 2.2, 2.1, 3.2 |

**Parallelism**: `1.4 ∥ 2.2` — then `2.3` after 2.2 completes.

> **Note**: 1.4 (gap analysis) and 2.2 (LLM assessment) both depend on 1.3 (evidence). They can run in parallel since 1.4 refines evidence while 2.2 assesses it. Story 2.3 (score computation) must wait for 2.2 (assessments).

**Exit criteria**: Gap analysis identifies missing evidence and triggers iteration 2; LLM assessments return structured capability levels; scores compute deterministically from assessments.

---

## Wave 4 — Rankings + API Endpoints (4 stories, 7 pts)

> **Goal**: Complete scoring pipeline + expose all API endpoints.

| Story | Name | Pts | MoSCoW | Depends On |
|-------|------|-----|--------|------------|
| 2.5 | Weighted Vendor Ranking | 2 | Must Have | 2.3, 2.4, 2.1, 3.2 |
| 3.4 | GET /api/research/{job_id} | 2 | Must Have | 3.2, 2.1 |
| 3.6 | Static File Serving & App Entry | 1 | Must Have | — |
| 3.5 | GET /api/jobs Listing | 1 | Could Have | 3.2 |

**Parallelism**: `2.5 ∥ 3.4 ∥ 3.6 ∥ 3.5` — all four can run simultaneously.

> **Note**: Story 3.6 has no hard dependency chain — it creates the FastAPI app shell and static file serving. It can technically be built anytime, but placing it here ensures it's ready for the SSE endpoint in Wave 5. Story 3.4 depends on 3.2 (repository) which completed in Wave 2.

**Exit criteria**: Rankings sort vendors by weighted score (0–100); GET endpoint returns full results JSON; FastAPI serves `static/index.html`; job listing returns previous runs.

---

## Wave 5 — SSE Endpoint + Pipeline Assembly (2 stories, 5 pts)

> **Goal**: Wire the full pipeline end-to-end with SSE streaming.

| Story | Name | Pts | MoSCoW | Depends On |
|-------|------|-----|--------|------------|
| 3.3 | POST /api/research (SSE) | 3 | Must Have | 1.5, 2.5, 3.1, 3.2 |
| 4.4 | Executive Summary Display | 2 | Should Have | 2.5, 3.4, 4.1* |

> **⚠ Story 4.4 split note**: Story 4.4 owns both the backend `synthesize` LangGraph node AND the full `pipeline.py` graph construction. The backend portion (synthesis node + pipeline assembly) can start here. The frontend portion (summary rendering) must wait for Wave 6 (after 4.1 matrix is built). **Recommendation**: Implement the backend half in this wave; frontend rendering in Wave 6.

**Parallelism**: `3.3 ∥ 4.4 (backend only)` — SSE endpoint wiring + pipeline assembly.

**Exit criteria**: `POST /api/research` triggers full pipeline and streams SSE events; LangGraph graph compiles and runs end-to-end; executive summary generated by synthesis node.

---

## Wave 6 — Frontend Core (2 stories, 5 pts)

> **Goal**: Build the comparison matrix UI and progress display.

| Story | Name | Pts | MoSCoW | Depends On |
|-------|------|-----|--------|------------|
| 4.1 | Comparison Matrix | 3 | Must Have | 3.4 |
| 4.5 | Real-time Progress Display | 1 | Could Have | 1.5, 3.3 |

**Parallelism**: `4.1 ∥ 4.5` — matrix renders from GET data; progress connects to SSE stream. Independent UI components.

**Exit criteria**: Matrix displays 4 vendors × 6 requirements with scores; progress bar updates via SSE during research.

---

## Wave 7 — Frontend Enhancements (3 stories, 7 pts)

> **Goal**: Confidence visualization, evidence drill-down, executive summary rendering.

| Story | Name | Pts | MoSCoW | Depends On |
|-------|------|-----|--------|------------|
| 4.2 | Confidence Visualization | 2 | Should Have | 4.1 |
| 4.3 | Evidence Drill-Down Panel | 3 | Should Have | 4.1 |
| 4.4 | Executive Summary Display (frontend) | — | Should Have | 4.1 (rendering portion) |

**Parallelism**: `4.2 ∥ 4.3 ∥ 4.4-frontend` — all three enhance the matrix independently.

> **Note**: 4.4 points were counted in Wave 5. This wave only covers the frontend rendering of the summary above the matrix.

**Exit criteria**: Confidence shown via opacity + dashed borders; cell click opens evidence panel with source URLs; executive summary renders above matrix.

---

## Wave 8 — Polish & Delivery (3 stories, 5 pts)

> **Goal**: Final polish, documentation, job history.

| Story | Name | Pts | MoSCoW | Depends On |
|-------|------|-----|--------|------------|
| 5.2 | UI Styling Polish | 2 | Could Have | 4.1–4.5 |
| 5.3 | README & Documentation | 2 | Should Have | All epics |
| 5.4 | Job History Page | 1 | Could Have | 3.5, 3.4 |

**Parallelism**: `5.2 ∥ 5.3 ∥ 5.4` — all three are independent finishing tasks.

**Exit criteria**: Professional styling applied; README covers setup, architecture, scoring; job history shows previous runs.

---

## Summary

| Wave | Stories | Points | Parallelism | MoSCoW Coverage |
|------|---------|--------|-------------|-----------------|
| 0 | 5.1, 2.1 | 4 | 2 parallel | Must Have |
| 1 | 3.1, 1.1, 1.5, 2.4 | 10 | 4 parallel | Must Have |
| 2 | 3.2, 1.2, 1.3 | 11 | 2 parallel → 1 serial | Must Have |
| 3 | 1.4, 2.2, 2.3 | 10 | 2 parallel → 1 serial | Must Have |
| 4 | 2.5, 3.4, 3.6, 3.5 | 6 | 4 parallel | Must + Could |
| 5 | 3.3, 4.4 (backend) | 5 | 2 parallel | Must + Should |
| 6 | 4.1, 4.5 | 4 | 2 parallel | Must + Could |
| 7 | 4.2, 4.3, 4.4 (frontend) | 5 | 3 parallel | Should Have |
| 8 | 5.2, 5.3, 5.4 | 5 | 3 parallel | Should + Could |
| **Total** | **25** | **61** | | |

---

## MVP Cut Line

Given the 2–3 hour time constraint, the **MVP cut line** falls after **Wave 6**:

- **Waves 0–6** (55 pts, 21 stories) = All **Must Have** stories complete + working end-to-end demo
- **Waves 7–8** (6 pts, 6 stories) = **Should Have** + **Could Have** enhancements

If time is tight, Wave 7 stories (confidence viz, drill-down, summary rendering) are the highest-value Should Have items. Wave 8 is expendable.

---

## Dependency Graph (Visual)

```
Wave 0:  [5.1] ─────────────────────────────────────────────────────────┐
         [2.1] ──┬──────────────┬──────────┬─────────────────────┐      │
                 │              │          │                     │      │
Wave 1:  [3.1]  [1.5]        [2.4]      [1.1] ◄────────────────┼──────┘
           │      │              │          │
Wave 2:  [3.2] ◄─┼──────────  [1.2] ◄─────┘
           │      │              │
           └──────┼─────► [1.3] ◄┘
                  │         │
Wave 3:           │       [1.4]   [2.2] ◄── (1.3)
                  │                 │
                  │               [2.3]
                  │                 │
Wave 4:           │    [2.5] ◄─── (2.3 + 2.4)   [3.4] [3.6] [3.5]
                  │      │
Wave 5:         [3.3] ◄─┘    [4.4 backend]
                  │
Wave 6:         [4.1]        [4.5]
                  │
Wave 7:  [4.2]  [4.3]  [4.4 frontend]

Wave 8:  [5.2]  [5.3]  [5.4]
```

---

## Execution Infrastructure

| Document | Purpose |
|----------|---------|
| [Wave Execution Protocol](./wave-execution-protocol.md) | Entry/exit checklists, error handling, commit protocol |
| [Agent Prompt Template](./agent-prompt-template.md) | Standard prompt structure + decision log requirement for every story agent |
| [File Ownership Map](./file-ownership-map.md) | Per-wave file ownership, conflict analysis, and resolution strategies |
| [Wave Logs](./wave-logs/) | Decision persistence — each story agent writes a log documenting files, decisions, and test results |

---

## Quality Gate Integration

Every wave must pass a **3-layer quality gate** before proceeding. Layers execute sequentially with fail-fast behavior.

### Quality Gate Layers

| Layer | Name | Trigger | Blocking | Owner |
|-------|------|---------|----------|-------|
| **1** | Automated Quality Gates | Every wave exit | Yes — fail = wave blocked | `make check` (CI) |
| **2** | Per-Story Agent Review | Every wave exit (after Layer 1) | Yes — FAIL verdict = wave blocked | Story's `quality_gate` agent |
| **3** | Human @architect Review | After Wave 6 (MVP) and Wave 8 (Final) | Yes — signoff required | @architect (human) |

### Layer 1 Tooling

| Tool | Version | Purpose | Config Location |
|------|---------|---------|-----------------|
| **ruff** | ≥0.8.0 | Linting + formatting (Rust-based, fast) | `[tool.ruff]` in `pyproject.toml` |
| **pyright** | latest | Static type checking (basic mode) | `[tool.pyright]` in `pyproject.toml` |
| **pytest-cov** | ≥6.0.0 | Test runner + coverage enforcement | `[tool.pytest.ini_options]` in `pyproject.toml` |
| **pip-audit** | ≥2.7.0 | Security vulnerability scanning (optional) | `make security` |

### Coverage Threshold

- **Target**: ≥60% line coverage on `app/` (enforced by `--cov-fail-under=60`)
- **Rationale**: Realistic for LLM-calling code where external API calls are mocked. Strict 80% would require excessive mock scaffolding for a prototype.
- **Omitted**: `__init__.py` files (no meaningful logic)

### Layer 2 Agent Assignments

Each story declares its quality gate reviewer in the YAML header:
```yaml
quality_gate: "@architect"       # or "@qa", "@dev"
quality_gate_tools: ["Read", "Grep", "mcp__ide__getDiagnostics"]
```

The assigned agent verifies all ACs are met, wave log is complete, and code follows conventions. See [Wave Execution Protocol — Layer 2](./wave-execution-protocol.md) for full protocol.

### Layer 3 Checkpoints

| Checkpoint | After Wave | Gate Focus |
|------------|-----------|------------|
| **MVP Gate** | Wave 6 | End-to-end flow works, architecture sound, no critical debt |
| **Final Delivery** | Wave 8 | Polish quality, docs complete, demo-ready |

### Deferred Quality Items (post-MVP)

| Item | Severity | Reason for Deferral |
|------|----------|-------------------|
| Integration tests | Medium | Requires full pipeline; unit tests sufficient for prototype |
| Frontend quality checks (ESLint) | Medium | Minimal HTML/JS in static files |
| License audit | Low | No distribution planned |
| Log validation automation | Low | Manual review sufficient at this scale |

---

## Risk Mitigation for Parallel Execution

### File Conflicts
- **Identified conflicts**: 5 instances across waves 3, 4, 6, 7, 8 where parallel stories touch the same file
- **Mitigation**: All resolved via primary owner designation + sequential ordering within the wave
- **Details**: See [File Ownership Map](./file-ownership-map.md#summary-same-wave-file-conflicts)

### Agent Failure Cascade
- A failed story in Wave N blocks dependent stories in later waves
- Non-dependent stories continue normally
- Failed stories are logged with remediation notes for manual follow-up
- **Protocol**: See [Wave Execution Protocol — Error Handling](./wave-execution-protocol.md#error-handling-protocol)

### Decision Persistence
- Every story agent writes a mandatory wave log before completing
- Downstream agents receive dependency outputs via agent prompt template
- Wave logs capture: files created, decisions made, deviations, warnings
- **Template**: See [Agent Prompt Template — Decision Log](./agent-prompt-template.md#template)

### Recommended Sequential Overrides
Some waves with file conflicts should run specific stories sequentially:
- **Wave 4**: Run 3.4 before 3.5 (shared `router.py`)
- **Wave 6**: Run 4.1 before 4.5 (shared `index.html`) — optional, low risk
- **Wave 7**: Run 4.4-frontend → 4.2 → 4.3 sequentially (all modify `index.html`)
- **Wave 8**: Run 5.2 before 5.4 (shared `index.html`)

---

*— River, removendo obstáculos 🌊*
