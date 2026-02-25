# SM Handoff: Frontend UX Overhaul — Story Breakdown

**Date:** 2026-02-25
**From:** @dev (Dex)
**To:** @sm
**Status:** 17/20 stories implemented, formal story documents needed in `docs/stories/`

---

## Process Note

Implementation was completed ahead of formal story documentation. This handoff provides the complete story breakdown so @sm can create proper story files in `docs/stories/` for tracking, acceptance criteria verification, and audit trail.

---

## Epic 7: Foundation — Repo Restructure, React Migration & Design System

### Story 7.0 — Restructure Monorepo (3 pts) — DONE

**User Story:** As a developer, I want the codebase split into backend and frontend directories so they can be deployed independently.

**Acceptance Criteria:**
- [x] All Python code moved to `vendor-research-tool-backend/`
- [x] `static/index.html` removed (archived in git history)
- [x] Static file serving removed from `app/main.py`
- [x] CORS configured via `ALLOWED_ORIGINS` env var
- [x] All backend tests pass after restructure
- [x] `.gitignore` updated for frontend paths

**Files Changed:** `.gitignore`, `vendor-research-tool-backend/` (all files moved)
**Dependencies:** None
**Sprint:** 1

---

### Story 7.1 — Fix Requirement Descriptions & Priority Mapping (2 pts) — DONE

**User Story:** As a user, I want to see full requirement descriptions instead of "R1", "R2" codes in the results.

**Acceptance Criteria:**
- [x] `get_results()` imports `REQUIREMENTS` from `app.config`
- [x] Builds lookup dict to resolve descriptions and priorities
- [x] Falls back to `description=rid, priority=medium` for unknown IDs
- [x] Unit test for description resolution
- [x] Unit test for unknown ID fallback

**Files Changed:** `vendor-research-tool-backend/app/repository.py`, `vendor-research-tool-backend/tests/test_repository.py`
**Dependencies:** 7.0
**Sprint:** 1

---

### Story 7.2 — Scaffold Vite + React + TypeScript + Tailwind Project (3 pts) — DONE

**User Story:** As a developer, I want a modern frontend scaffold so I can build React components with TypeScript and Tailwind CSS.

**Acceptance Criteria:**
- [x] Vite + React + TypeScript project created in `vendor-research-tool-frontend/`
- [x] Tailwind CSS v4 installed with `@tailwindcss/vite` plugin
- [x] `VITE_API_URL` env var configured for backend connection
- [x] Folder structure: atoms/molecules/organisms/templates/hooks/lib/styles
- [x] `.env.example` with `VITE_API_URL=http://localhost:8000`
- [x] API fetch wrapper (`src/lib/api.ts`) using env var
- [x] TypeScript types matching backend models (`src/lib/types.ts`)
- [x] Project builds successfully

**Files Changed:** `vendor-research-tool-frontend/` (entire scaffold)
**Dependencies:** 7.0
**Sprint:** 1

---

### Story 7.3 — Configure Tailwind Theme from Design Tokens (3 pts) — DONE

**User Story:** As a developer, I want Tailwind configured with our design tokens so components use consistent styling.

**Acceptance Criteria:**
- [x] All `docs/ux/tokens.yaml` values mapped to Tailwind `@theme` block
- [x] Colors: light/dark mode with status, confidence, accent colors
- [x] Typography: Inter, Source Serif 4, JetBrains Mono with font-display swap
- [x] Custom keyframe animations: shimmer, token-fade-in, step-pulse, pill-enter
- [x] `@media (prefers-reduced-motion: reduce)` reset
- [x] Dark mode support via `prefers-color-scheme`

**Files Changed:** `vendor-research-tool-frontend/src/styles/globals.css`
**Dependencies:** 7.2
**Sprint:** 1

---

### Story 7.4 — Migrate Existing UI to React Components (5 pts) — DONE

**User Story:** As a user, I want the same functionality as the current UI but built with React components for better maintainability.

**Acceptance Criteria:**
- [x] `<ComparisonMatrix>` — table with priority grouping, score cells, confidence legend
- [x] `<DrillDownPanel>` — slide-in panel with justification, limitations, evidence
- [x] `<ExecutiveSummary>` — summary paragraphs + ranked vendor list
- [x] `<JobHistory>` — collapsible previous runs list
- [x] `<ScoreCell>` atom — colored cell with score + confidence, click handler
- [x] `<Badge>` atom — rank, status, source-type, priority badges
- [x] All existing API interactions preserved (fetch /api/jobs, /api/research/{id})

**Files Changed:** `src/components/atoms/Badge.tsx`, `ScoreCell.tsx`, `src/components/organisms/ComparisonMatrix.tsx`, `DrillDownPanel.tsx`, `ExecutiveSummary.tsx`, `JobHistory.tsx`
**Dependencies:** 7.2, 7.3
**Sprint:** 2

---

### Story 7.5 — Accessibility Foundations (3 pts) — DONE

**User Story:** As a user with accessibility needs, I want the UI to be navigable via keyboard and screen reader.

**Acceptance Criteria:**
- [x] ScoreCell: `role="button"`, `tabIndex={0}`, `aria-label` with vendor+requirement+score
- [x] DrillDownPanel: `role="dialog"`, `aria-labelledby`, focus trap, return-focus on close
- [x] Escape key closes panel
- [x] Skip-to-content link
- [x] Visible focus rings: `focus-visible:ring-2 focus-visible:ring-accent-primary`

**Files Changed:** `src/components/atoms/ScoreCell.tsx`, `src/components/organisms/DrillDownPanel.tsx`, `src/components/templates/ResearchPage.tsx`
**Dependencies:** 7.4
**Sprint:** 2

---

## Epic 8: Pipeline Visualization & Research-Time UX

### Story 8.1 — Backend: Granular SSE Event Emission (5 pts) — DONE

**User Story:** As a frontend developer, I want granular SSE events so I can show real-time pipeline feedback.

**Acceptance Criteria:**
- [x] New event types: `phase_start`, `phase_end`, `query_generated`, `search_result`, `evidence_extracted`, `score_computed`, `vendor_ranked`, `warning`, `iteration_start`
- [x] Progress percentage never goes backwards (monotonic progress fix)
- [x] Gap-filling iteration uses 45-50% range instead of resetting to 10%
- [x] Extraction failures emit `warning` events
- [x] Backward-compatible: existing `progress` events preserved
- [x] All backend tests pass (192 passed, 94% coverage)

**Files Changed:** `vendor-research-tool-backend/app/graph/progress.py`, `vendor-research-tool-backend/app/graph/nodes.py`, `vendor-research-tool-backend/tests/test_nodes.py`
**Dependencies:** 7.0
**Sprint:** 1

---

### Story 8.2 — PipelineStepper Component (5 pts) — DONE

**User Story:** As a user, I want to see which stage the research is in so I know what's happening.

**Acceptance Criteria:**
- [x] Horizontal stepper: Planning -> Searching -> Analyzing -> Scoring -> Ranking -> Complete
- [x] Step states: pending (gray), active (animated pulse), complete (green check)
- [x] Connecting line fills progressively
- [x] Active step colors from design tokens
- [x] Elapsed time counter (MM:SS)
- [x] Responds to `phase_start`/`phase_end` SSE events
- [x] Responsive: mobile condenses to current phase + time

**Files Changed:** `src/components/organisms/PipelineStepper.tsx`
**Dependencies:** 7.3, 8.1, 8.5
**Sprint:** 3

---

### Story 8.3 — ResearchTimeline + SourcePill with Animations (5 pts) — DONE

**User Story:** As a user, I want to see sources appearing in real-time during research like Perplexity/ChatGPT deep search.

**Acceptance Criteria:**
- [x] Vertical timeline below stepper, one row per phase
- [x] Active row: animated pulse on icon
- [x] SourcePill molecules animate in as `search_result` events arrive
- [x] SourcePill: domain text, rounded-full pill, entrance animation
- [x] Hover expands to show full title
- [x] Live source count updates
- [x] Searching sub-phases: shows iteration info from `iteration_start` events

**Files Changed:** `src/components/organisms/ResearchTimeline.tsx`, `src/components/molecules/SourcePill.tsx`
**Dependencies:** 7.3, 8.1, 8.2, 8.5
**Sprint:** 3

---

### Story 8.4 — LiveCounters Component (2 pts) — DONE

**User Story:** As a user, I want to see how many sources were found and how long the research has been running.

**Acceptance Criteria:**
- [x] Sources found counter (increments on `search_result` events)
- [x] Elapsed time MM:SS (useTimer hook)
- [x] `aria-atomic="true"` for screen readers
- [x] Freezes on completion

**Files Changed:** `src/components/molecules/LiveCounters.tsx`
**Dependencies:** 8.2, 8.3
**Sprint:** 3

---

### Story 8.5 — useResearchState Hook + SSE State Machine (4 pts) — DONE

**User Story:** As a developer, I want a centralized state management hook for the research pipeline so all components stay in sync.

**Acceptance Criteria:**
- [x] State machine: idle -> planning -> searching -> analyzing -> scoring -> ranking -> writing -> complete | error
- [x] Tracks: currentPhase, stepStatuses, sources[], queries[], evidenceCounts, scores, rankings, elapsedTime
- [x] SSE client: handles connection, abort, parsing
- [x] All UI components consume this hook
- [x] State resets on new research run
- [x] Activity counter uses useRef (not module-level)

**Files Changed:** `src/hooks/useResearchState.ts`, `src/hooks/useTimer.ts`, `src/lib/sse-client.ts`
**Dependencies:** 7.4, 8.1
**Sprint:** 2

---

## Epic 9: Audit Trail & Research Transparency

### Story 9.1 — ActivityFeed Component (4 pts) — DONE

**User Story:** As a user, I want to see a live log of what the research agent is doing.

**Acceptance Criteria:**
- [x] Scrollable feed with relative timestamps (+0:34)
- [x] Maps SSE event types to human-readable messages
- [x] Warning entries styled with amber highlight
- [x] New entries at top with fade-in animation
- [x] Max 200 entries in state
- [x] Auto-scroll unless user scrolled up

**Files Changed:** `src/components/organisms/ActivityFeed.tsx`
**Dependencies:** 8.1, 8.5
**Sprint:** 4

---

### Story 9.2 — QueryHistory Tab (3 pts) — DONE

**User Story:** As a user, I want to audit which search queries the research agent generated.

**Acceptance Criteria:**
- [x] Tab in AuditView listing all generated queries
- [x] Grouped by vendor -> requirement
- [x] Gap-filling queries tagged "Refined"
- [x] Real-time population from `query_generated` events
- [x] Count in tab header: "Queries (48)"

**Files Changed:** `src/components/organisms/QueryHistory.tsx`
**Dependencies:** 8.5, 9.4
**Sprint:** 5

---

### Story 9.3 — SourcesVisited Tab (3 pts) — DONE

**User Story:** As a user, I want to see all sources the research agent discovered.

**Acceptance Criteria:**
- [x] Tab in AuditView listing all discovered sources
- [x] Reuses SourcePill component
- [x] Deduplicated by URL, grouped by domain
- [x] "Sources (24 unique from 48 searches)" counter
- [x] Clickable links (target="_blank" rel="noopener")

**Files Changed:** `src/components/organisms/SourcesVisited.tsx`
**Dependencies:** 8.3, 8.5, 9.4
**Sprint:** 5

---

### Story 9.4 — AuditView Tabbed Container (4 pts) — DONE

**User Story:** As a user, I want a tabbed interface to browse different aspects of the research audit trail.

**Acceptance Criteria:**
- [x] Tabs: Timeline | Queries | Sources | Activity Log
- [x] Accessible: `role="tablist"` / `role="tab"` / `role="tabpanel"`, arrow-key navigation
- [x] Populated from useResearchState hook data
- [x] "Audit trail not available" message for historical jobs without data
- [x] Tab counts update in real-time

**Files Changed:** `src/components/organisms/AuditView.tsx`
**Dependencies:** 8.3, 9.1
**Sprint:** 4

---

### Story 9.5 — Backend: Persist Audit Events for Historical Replay (5 pts) — PENDING

**User Story:** As a user, I want to review the audit trail for past research runs, not just the current one.

**Acceptance Criteria:**
- [ ] New `audit_events` SQLite table: `(id INTEGER PK, job_id TEXT, event_type TEXT, payload_json TEXT, created_at TEXT)`
- [ ] Index on `job_id`
- [ ] `save_audit_event()` method called alongside each `emit_*` in `progress.py`
- [ ] New endpoint: `GET /api/research/{job_id}/audit` returns events chronologically
- [ ] Frontend AuditView fetches audit events when viewing historical jobs
- [ ] ~200 events/run, ~40KB — lightweight

**Files to Change:** `vendor-research-tool-backend/app/repository.py`, `vendor-research-tool-backend/app/graph/progress.py`, `vendor-research-tool-backend/app/api/router.py`, frontend AuditView
**Dependencies:** 8.1, 9.4
**Sprint:** 5

---

## Epic 10: Scoring Methodology & Explanation UI

### Story 10.1 — ScoringMethodology Explainer (3 pts) — DONE

**User Story:** As a user, I want to understand how scores and confidence values are calculated.

**Acceptance Criteria:**
- [x] Expandable "How scores are calculated" section
- [x] Score formula: Capability (40%) + Evidence (30%) + Maturity (20%) - Limitations (10%)
- [x] Confidence formula: Source Count (30%) + Authority (30%) + Recency (25%) + Consistency (15%)
- [x] Capability and maturity level explanations
- [x] Ranking formula explanation
- [x] Visual weight bars for each component
- [x] `aria-expanded` on toggle

**Files Changed:** `src/components/organisms/ScoringMethodology.tsx`
**Dependencies:** 7.3
**Sprint:** 2

---

### Story 10.2 — ConfidenceBreakdown Visualization (4 pts) — DONE

**User Story:** As a user, I want to understand why a confidence score is high or low for a specific vendor-requirement pair.

**Acceptance Criteria:**
- [x] Horizontal stacked bar showing 4 confidence components in DrillDownPanel
- [x] Client-side recomputation in `scoring.ts` mirrors `engine.py`
- [x] Color per segment: green (>=0.7), amber (0.4-0.69), red (<0.4)
- [x] Hover tooltip on each segment showing raw value + explanation
- [x] 25 unit tests verifying parity with Python scoring logic

**Files Changed:** `src/components/molecules/ConfidenceBreakdown.tsx`, `src/lib/scoring.ts`, `src/lib/scoring.test.ts`
**Dependencies:** 7.4
**Sprint:** 4

---

### Story 10.3 — ScoreBreakdown in Drill-Down (3 pts) — DONE

**User Story:** As a user, I want to see exactly which factors contributed to a vendor's score for a specific requirement.

**Acceptance Criteria:**
- [x] "Score Breakdown" section in DrillDownPanel
- [x] Shows 4 components: Capability, Evidence, Maturity, Limitations
- [x] Visual formula: `0.40 x 10.0 + 0.30 x 6.0 + 0.20 x 7.0 + 0.10 x 8.0 = 8.0`
- [x] Color coding: green (contributing), red (pulling down)
- [x] Lookup tables match `engine.py`

**Files Changed:** `src/components/molecules/ScoreBreakdown.tsx`
**Dependencies:** 10.1
**Sprint:** 4

---

### Story 10.4 — PriorityWeights Legend & Ranking Explanation (3 pts) — DONE

**User Story:** As a user, I want to understand how requirement priorities affect vendor rankings.

**Acceptance Criteria:**
- [x] Priority callout: High = 3x, Medium = 2x, Low = 1x
- [x] Priority badges (H/M/L) with color
- [x] Ranking formula displayed
- [x] Per-vendor ranking expandable showing per-requirement weighted contributions

**Files Changed:** `src/components/molecules/PriorityWeights.tsx`
**Dependencies:** 7.1, 7.3
**Sprint:** 3

---

## Sprint Allocation Summary

| Sprint | Stories | Points | Status |
|--------|---------|--------|--------|
| Sprint 1 | 7.0, 7.1, 7.2, 7.3, 8.1 | 16 | DONE |
| Sprint 2 | 7.4, 7.5, 8.5, 10.1 | 15 | DONE |
| Sprint 3 | 8.2, 8.3, 8.4, 10.4 | 15 | DONE |
| Sprint 4 | 9.1, 9.4, 10.2, 10.3 | 15 | DONE |
| Sprint 5 | 9.2, 9.3, 9.5 | 11 | IN PROGRESS (9.5 pending) |

---

## Action Items for @sm

1. Create formal story files in `docs/stories/` for each story above (7.0-10.4)
2. Verify acceptance criteria against actual implementation
3. Mark completed stories with appropriate status
4. Prioritize Story 9.5 for next sprint
5. Consider adding stories for frontend test coverage expansion
