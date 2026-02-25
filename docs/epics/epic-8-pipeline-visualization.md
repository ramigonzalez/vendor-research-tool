# Epic 8: Pipeline Visualization & Research-Time UX

## Status
Complete

## Goal
Provide real-time, granular feedback during ~5 minute research runs through a multi-stage stepper, animated source discovery, live counters, and a centralized SSE state machine — inspired by Perplexity, ChatGPT, and Claude deep-search UIs.

## Business Value
- Addresses user pain point #1: "no pipeline stage visualization"
- Addresses user pain point #2: "no animations"
- Addresses user pain point #6: "UI feedback is very poor at research time"
- Fixes critical bug: progress percentage going backwards during gap-filling
- Surfaces backend errors/warnings previously only visible in server logs

## Success Metrics
- Pipeline stepper transitions through all 6 phases during a live research run
- Source pills animate in real-time as search results arrive
- Progress percentage is always monotonically increasing
- Elapsed time counter accurate to within 1 second
- Backend warnings surface in the UI (not just server logs)

## Architecture Decision
- **SSE event types**: 9 new granular event types added to backend (backward-compatible)
- **State management**: Single `useResearchState` hook as centralized state machine
- **SSE client**: Custom fetch-based reader with abort support (not EventSource API)
- **Phase model**: `idle -> planning -> searching -> analyzing -> scoring -> ranking -> writing -> complete | error`
- **Monotonic progress**: Gap-fill uses 45-50% range, never resets

## Stories

| ID | Story | Points | Status | Executor |
|----|-------|--------|--------|----------|
| 8.1 | Backend: Granular SSE Event Emission | 5 | Done | @dev |
| 8.2 | PipelineStepper Component | 5 | Done | @dev |
| 8.3 | ResearchTimeline + SourcePill with Animations | 5 | Done | @dev |
| 8.4 | LiveCounters Component | 2 | Done | @dev |
| 8.5 | useResearchState Hook + SSE State Machine | 4 | Done | @dev |

**Total: 5 stories, 21 points**

## Dependencies
- Epic 7 (Foundation) — requires scaffolded frontend and design tokens

## Risks & Mitigations
1. **SSE event volume (~200 events/run)** — Mitigated: React virtual DOM handles batched updates efficiently.
2. **Timer accuracy** — Mitigated: `setInterval(1000)` with `Date.now()` delta calculation.
3. **Connection loss** — Mitigated: SSE client detects errors, transitions to error state.

## Key References
| Asset | Path |
|-------|------|
| SSE progress helpers | `vendor-research-tool-backend/app/graph/progress.py` |
| Pipeline nodes | `vendor-research-tool-backend/app/graph/nodes.py` |
| Competitive analysis | `docs/ux/competitive-analysis.md` |
| ResearchTimeline spec | `docs/ux/components/research-timeline.md` |
| SourcePill spec | `docs/ux/components/source-pill.md` |

## Priority
P0 — Core UX (directly addresses top user pain points)

## Sprint Allocation
- Sprint 1: Story 8.1 (5 pts, backend)
- Sprint 2: Story 8.5 (4 pts, state management)
- Sprint 3: Stories 8.2, 8.3, 8.4 (12 pts, UI components)
