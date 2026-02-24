# File Ownership Map

> **Purpose**: Defines which story owns which files per wave. When two stories in the same wave touch the same file, one is designated "primary owner" and the other must wait.

---

## Conflict Analysis Summary

After analyzing all 25 stories across 9 waves: **no same-wave file conflicts exist**. The wave structure naturally separates stories that touch the same files into different waves.

Cross-wave file evolution (same file, different waves) is expected and handled by wave ordering:
- `app/repository.py`: 3.1 (Wave 1) creates schema → 3.2 (Wave 2) adds CRUD
- `app/graph/nodes.py`: 1.1 (Wave 1) creates → 1.2, 1.3 (Wave 2) extend → 1.4, 2.2, 2.3 (Wave 3) extend → 2.5 (Wave 4) extends
- `app/main.py`: 3.6 (Wave 4) creates → 3.3 (Wave 5) extends with SSE endpoint
- `static/index.html`: 3.6 (Wave 4) creates placeholder → 4.1 (Wave 6) builds matrix → 4.2, 4.3, 4.4 (Wave 7) extend
- `app/scoring/engine.py`: 2.4 (Wave 1) creates → 2.3 (Wave 3) extends → 2.5 (Wave 4) extends
- `tests/test_nodes.py`: 1.1 (Wave 1) creates → 1.2, 1.3 (Wave 2) extend → 2.2 (Wave 3) extends

---

## Wave 0 — Foundation

| Story | Files Created | Files Modified |
|-------|--------------|----------------|
| **5.1** | `requirements.txt`, `.env.example`, `.gitignore`, `app/config.py`, `app/__init__.py`, `app/graph/__init__.py`, `app/scoring/__init__.py`, `app/prompts/__init__.py`, `tests/__init__.py`, `tests/conftest.py`, `app/main.py` (minimal shell) | — |
| **2.1** | `app/models.py`, `app/graph/state.py`, `tests/test_models.py` | — |

**Conflicts**: None. 5.1 creates scaffold files, 2.1 creates domain model files. No overlap.

---

## Wave 1 — Persistence + Pipeline Entry

| Story | Files Created | Files Modified |
|-------|--------------|----------------|
| **3.1** | `app/repository.py` (schema + `create_db_and_tables()`) | `.gitignore` (add `research.db`), `tests/test_repository.py` |
| **1.1** | `app/graph/nodes.py` (`generate_queries`), `app/prompts/research.py` | `tests/test_nodes.py` |
| **1.5** | `app/graph/progress.py` (`emit_progress` helper, SSE generator) | `app/graph/state.py` (add `progress_queue` note) |
| **2.4** | `app/scoring/engine.py` (`compute_confidence`) | `tests/test_scoring.py` |

**Conflicts**: None. Each story creates distinct files.

**Notes**:
- 1.5 may need to touch `app/graph/state.py` to document `progress_queue` usage — but `state.py` was created by 2.1 in Wave 0, and 1.5 only adds a helper that reads from state, not modifies the TypedDict definition.
- If 1.5 needs to modify `state.py`, it owns that modification for this wave.

---

## Wave 2 — Repository + Search + Evidence

| Story | Files Created | Files Modified |
|-------|--------------|----------------|
| **3.2** | — | `app/repository.py` (add ABC + SQLite CRUD + `get_repository()`), `tests/conftest.py` (add `MockResearchRepository`), `tests/test_repository.py` |
| **1.2** | — | `app/graph/nodes.py` (add `execute_searches`), `tests/test_nodes.py` |
| **1.3** | `app/prompts/extraction.py` | `app/graph/nodes.py` (add `extract_evidence`), `tests/test_nodes.py` |

**Sequencing**: 3.2 and 1.2 run in parallel. 1.3 runs AFTER both complete.

**Conflicts**: 1.2 and 1.3 both modify `app/graph/nodes.py` — but 1.3 runs after 1.2, so no conflict.

---

## Wave 3 — Gap Analysis + Scoring Core

| Story | Files Created | Files Modified |
|-------|--------------|----------------|
| **1.4** | `app/graph/gap_analysis.py` (or in `nodes.py`), `tests/test_evidence.py` | `app/models.py` (add `GapType` enum), `app/graph/nodes.py` (add gap functions + conditional edge) |
| **2.2** | `app/prompts/assessment.py` | `app/graph/nodes.py` (add `assess_capabilities`), `tests/test_nodes.py` |
| **2.3** | — | `app/scoring/engine.py` (add `compute_requirement_score`), `app/graph/nodes.py` (add `compute_scores` node), `tests/test_scoring.py` |

**Sequencing**: 1.4 and 2.2 run in parallel. 2.3 runs AFTER 2.2 completes.

**Conflicts within parallel group (1.4 ∥ 2.2)**:
- Both modify `app/graph/nodes.py` — **potential conflict!**
  - **Resolution**: 1.4 adds gap analysis functions. 2.2 adds `assess_capabilities` node. These are independent additions (different functions). Both can append to the same file.
  - **Mitigation**: 1.4 owns gap-related functions. 2.2 owns assessment function. Each appends to the end of `nodes.py`. If merge issues arise, 2.3 (which runs after both) can reconcile.
- 1.4 modifies `app/models.py` (adds `GapType` enum) — no other Wave 3 story touches models. No conflict.

---

## Wave 4 — Rankings + API Endpoints

| Story | Files Created | Files Modified |
|-------|--------------|----------------|
| **2.5** | — | `app/scoring/engine.py` (add `compute_vendor_rankings`), `app/graph/nodes.py` (add `compute_rankings` node), `tests/test_scoring.py` |
| **3.4** | `app/api/router.py` (or routes in `main.py`) | `tests/test_api.py` |
| **3.6** | `static/index.html` (placeholder), `static/` directory | `app/main.py` (add StaticFiles mount, `/` route, `/health` route) |
| **3.5** | — | `app/api/router.py` (add `/api/jobs` route), `tests/test_api.py` |

**Conflicts within parallel group (all 4 parallel)**:
- 3.4 and 3.5 both touch `app/api/router.py` and `tests/test_api.py`
  - **Resolution**: 3.4 adds GET `/api/research/{job_id}`. 3.5 adds GET `/api/jobs`. Independent routes in the same file.
  - **Mitigation**: 3.4 is primary owner of `router.py` (creates it). 3.5 appends to it. If both create the file, 3.4 has priority (more complex route). Alternatively: 3.5 can run slightly after 3.4 within the wave.
- 2.5 modifies `app/graph/nodes.py` — no other Wave 4 story touches `nodes.py`. No conflict.
- 3.6 creates `app/main.py` content — no other Wave 4 story touches `main.py`. No conflict.

**Recommended execution order within wave**: 3.4 first (creates `router.py`), then 3.5 (appends to `router.py`). 2.5 and 3.6 fully parallel with everything.

---

## Wave 5 — SSE Endpoint + Pipeline Assembly

| Story | Files Created | Files Modified |
|-------|--------------|----------------|
| **3.3** | `app/graph/state.py` (add `build_initial_state`) | `app/main.py` (add POST `/api/research`, CORS, SSE generator), `tests/test_api.py` |
| **4.4 (backend)** | `app/prompts/synthesis.py`, `app/graph/pipeline.py` | `app/graph/nodes.py` (add `generate_summary` node) |

**Conflicts**: None. 3.3 owns `app/main.py`. 4.4 owns `app/graph/pipeline.py`. No overlap.

---

## Wave 6 — Frontend Core

| Story | Files Created | Files Modified |
|-------|--------------|----------------|
| **4.1** | — | `static/index.html` (build full matrix UI) |
| **4.5** | — | `static/index.html` (add progress bar + SSE consumption) |

**Conflicts**: Both modify `static/index.html`!
- **Resolution**: These are independent UI sections. 4.1 builds the results/matrix section. 4.5 builds the progress/SSE section.
- **Mitigation**: **4.1 is primary owner** (larger, creates core structure). 4.5 adds a separate section (progress bar) that doesn't overlap with the matrix.
- **Risk**: Low. Both add distinct HTML sections and JS functions. If merge issues arise, manual reconciliation after wave is straightforward.
- **Alternative**: Run 4.1 first, then 4.5. Adds minimal time since 4.5 is 1 point.

---

## Wave 7 — Frontend Enhancements

| Story | Files Created | Files Modified |
|-------|--------------|----------------|
| **4.2** | — | `static/index.html` (add confidence CSS + extend `renderMatrix`) |
| **4.3** | — | `static/index.html` (add drill-down panel HTML/CSS/JS) |
| **4.4 (frontend)** | — | `static/index.html` (add `renderSummary` JS function + summary HTML section) |

**Conflicts**: All three modify `static/index.html`!
- **Resolution**: Each adds independent sections/functions:
  - 4.2: confidence CSS classes + extends existing `renderMatrix()` cell rendering
  - 4.3: drill-down panel (new HTML block + new JS function `openDrillDown`)
  - 4.4: summary section (new HTML block + new JS function `renderSummary`)
- **Mitigation**: **4.3 is primary owner** (most complex, 3 points). Run order: 4.4-frontend first (adds summary section above matrix), then 4.2 (modifies matrix cells), then 4.3 (adds panel after matrix).
- **Recommended**: Run sequentially within wave: 4.4-frontend → 4.2 → 4.3

---

## Wave 8 — Polish & Delivery

| Story | Files Created | Files Modified |
|-------|--------------|----------------|
| **5.2** | — | `static/index.html` (CSS polish, responsive tweaks) |
| **5.3** | `README.md` | — |
| **5.4** | — | `static/index.html` (add job history section + JS) |

**Conflicts**: 5.2 and 5.4 both modify `static/index.html`.
- **Resolution**: 5.2 does CSS polish. 5.4 adds a new section. Independent changes.
- **Mitigation**: **5.2 is primary owner** (broader changes). Run 5.4 after 5.2.
- 5.3 is fully independent (creates README.md only).

---

## Summary: Same-Wave File Conflicts

| Wave | File | Stories | Resolution |
|------|------|---------|------------|
| 3 | `app/graph/nodes.py` | 1.4, 2.2 | Independent function additions; both append. 2.3 reconciles after. |
| 4 | `app/api/router.py` | 3.4, 3.5 | 3.4 creates, 3.5 appends. Run 3.4 first. |
| 6 | `static/index.html` | 4.1, 4.5 | 4.1 primary owner. Independent sections. |
| 7 | `static/index.html` | 4.2, 4.3, 4.4 | Run sequentially: 4.4 → 4.2 → 4.3 |
| 8 | `static/index.html` | 5.2, 5.4 | 5.2 primary owner. Run 5.4 after 5.2. |

**Verdict**: All conflicts are manageable via ordering or independent section additions. No story needs to be moved to a different wave.
