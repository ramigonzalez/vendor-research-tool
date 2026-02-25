# Epic 9: Audit Trail & Research Transparency

## Status
In Progress (4/5 stories complete)

## Goal
Provide complete research transparency through a live activity feed during research and a post-research audit trail showing every query generated, source visited, and evidence extracted — enabling users to understand, validate, and trust the research results.

## Business Value
- Addresses user pain point #3: "no audit trail — I want to audit what the research did"
- Enables step-by-step explanation of data processing
- Builds user trust through full transparency of AI research process
- Supports compliance and reproducibility requirements

## Success Metrics
- During research: live activity feed shows queries, sources, evidence, scores, and warnings in real time
- Post-research: tabbed audit view with Timeline, Queries, Sources, and Activity Log tabs
- Historical replay: previously completed jobs show their full audit trail (Story 9.5)
- All search queries are auditable with vendor/requirement grouping
- All sources are deduplicated, grouped by domain, and linked

## Architecture Decision
- **Tab structure**: Timeline | Queries | Sources | Activity Log
- **Accessibility**: `role="tablist"` / `role="tab"` / `role="tabpanel"` with arrow-key navigation
- **Data source (live)**: `useResearchState` hook SSE events
- **Data source (historical)**: `GET /api/research/{job_id}/audit` endpoint (Story 9.5)
- **Storage**: SQLite `audit_events` table (~200 events/run, ~40KB)

## Stories

| ID | Story | Points | Status | Executor |
|----|-------|--------|--------|----------|
| 9.1 | ActivityFeed Component | 4 | Done | @dev |
| 9.2 | QueryHistory Tab | 3 | Done | @dev |
| 9.3 | SourcesVisited Tab | 3 | Done | @dev |
| 9.4 | AuditView Tabbed Container | 4 | Done | @dev |
| 9.5 | Backend: Persist Audit Events for Historical Replay | 5 | **Pending** | @dev |

**Total: 5 stories, 19 points**

## Dependencies
- Epic 8 (Pipeline Visualization) — requires SSE events and state machine

## Blocker
**Story 9.5 is the last remaining implementation story.** It requires:
- New `audit_events` SQLite table with job_id index
- `save_audit_event()` method called from each `emit_*` function in `progress.py`
- New API endpoint: `GET /api/research/{job_id}/audit`
- Frontend AuditView integration to fetch and display historical audit data

## Risks & Mitigations
1. **Storage growth** — Mitigated: ~40KB per run is lightweight; can add cleanup job if needed.
2. **Historical jobs without audit data** — Mitigated: UI shows "Audit trail not available for this run" message.
3. **Event ordering** — Mitigated: Events stored with `created_at` timestamp, returned chronologically.

## Key References
| Asset | Path |
|-------|------|
| AuditView component | `vendor-research-tool-frontend/src/components/organisms/AuditView.tsx` |
| ActivityFeed component | `vendor-research-tool-frontend/src/components/organisms/ActivityFeed.tsx` |
| Repository pattern | `vendor-research-tool-backend/app/repository.py` |
| API router | `vendor-research-tool-backend/app/api/router.py` |

## Priority
P1 — Transparency (enhances trust and auditability)

## Sprint Allocation
- Sprint 4: Stories 9.1, 9.4 (8 pts)
- Sprint 5: Stories 9.2, 9.3, 9.5 (11 pts)
