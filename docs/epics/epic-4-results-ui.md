# Epic 4: Results UI

**Epic Goal**: Build the single-page HTML frontend that displays the comparison matrix, confidence visualization, evidence drill-down, executive summary, and real-time progress during research.

**Integration Requirements**: Consumes `POST /api/research` SSE stream and `GET /api/research/{job_id}` from Epic 3. No build tools — pure HTML/CSS/JS in `static/index.html`.

**MoSCoW**: E4-S1 (Must Have), E4-S2 + E4-S3 + E4-S4 (Should Have), E4-S5 (Could Have)
**Total Story Points**: 12

---

## Story 4.1 — Comparison Matrix

**As a** researcher/evaluator,
**I want** to see a grid of all vendors × requirements with scores,
**so that** I can quickly compare vendor capabilities at a glance.

### Acceptance Criteria
1. Matrix renders with vendors as columns and requirements as rows.
2. Each cell displays the numerical score (0–10, one decimal place).
3. Cell background color: score ≥7 = green (`#2ecc71`), 4–6.9 = amber (`#f39c12`), <4 = red (`#e74c3c`).
4. Requirements grouped by priority: "High Priority" section first, then "Medium", then "Low".
5. Vendor overall ranking score displayed in header row below vendor name.
6. Matrix is horizontally scrollable on narrow screens.
7. Empty/missing scores show as "—" with neutral styling.

**Executor**: @dev | **Quality Gate**: @architect
**Story Points**: 4

---

## Story 4.2 — Confidence Visualization

**As a** researcher/evaluator,
**I want** to see confidence levels visually within each matrix cell,
**so that** I know which scores are based on solid evidence vs. sparse sources.

### Acceptance Criteria
1. Each cell shows confidence as visual indicator alongside score.
2. High confidence (≥0.7): solid border, full opacity.
3. Medium confidence (0.4–0.69): dashed border, 80% opacity.
4. Low confidence (<0.4): dashed red border, 60% opacity, warning icon (⚠️).
5. Confidence value shown as small text below score (e.g., "conf: 0.82").
6. Legend explaining confidence indicators shown below matrix.

**Executor**: @dev | **Quality Gate**: @architect
**Story Points**: 2

---

## Story 4.3 — Evidence Drill-Down Panel

**As a** researcher/evaluator,
**I want** to click a matrix cell and see the evidence behind the score,
**so that** I can verify the LLM's reasoning and check source quality.

### Acceptance Criteria
1. Clicking a matrix cell opens a slide-in panel (right side or modal).
2. Panel header shows: vendor name, requirement name, score, confidence.
3. Panel body shows: LLM justification paragraph.
4. Evidence list shows each `Evidence` item with: claim text, source badge (source_type), source name + URL (clickable link), content date, relevance score.
5. Source type badges color-coded: official_docs=blue, github=dark, comparison=purple, blog=orange, community=grey.
6. Evidence items sorted by relevance descending.
7. "Supports requirement" indicator (✓ or ✗) shown per evidence item.
8. Panel closable via ✕ button or clicking outside.
9. Limitations list shown if non-empty.

**Executor**: @dev | **Quality Gate**: @architect
**Story Points**: 3

---

## Story 4.4 — Executive Summary Display

**As a** researcher/evaluator,
**I want** to read an AI-generated executive summary at the top of results,
**so that** I get a narrative overview and top recommendation before diving into the matrix.

### Acceptance Criteria
1. Executive summary displayed as prose (3–4 paragraphs) above the matrix.
2. Summary section has a clear header: "Executive Summary".
3. Rankings bar chart or ordered list shown below summary: vendor ranked 1–4 with overall scores.
4. Summary text is non-editable, styled for readability (max-width ~700px, line-height 1.6).
5. If summary is empty or failed, show fallback: "Summary generation failed — see matrix for details."

**Executor**: @dev | **Quality Gate**: @architect
**Story Points**: 2

---

## Story 4.5 — Real-time Progress Display

**As a** user triggering research,
**I want** to see real-time progress updates while the pipeline runs,
**so that** I know the system is working and approximately how long to wait.

### Acceptance Criteria
1. "Run Research" button triggers POST to `/api/research` and opens SSE stream.
2. Progress bar fills from 0–100% based on `pct` field in SSE events.
3. Current phase label shown below bar (e.g., "Researching: LangSmith × Tracing...").
4. "Run Research" button disabled while pipeline is running.
5. On `completed` event: hide progress, render results matrix and summary.
6. On `error` event: show error message with retry button.
7. Phase transitions animate smoothly (CSS transition on width).

**Executor**: @dev | **Quality Gate**: @architect
**Story Points**: 1
