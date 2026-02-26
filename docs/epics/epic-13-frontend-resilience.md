# Epic 13: Frontend Resilience & Error Handling

## Overview
Harden the frontend against runtime failures during live research pipelines and result rendering. The app currently has no Error Boundaries — any unhandled React rendering error produces a white screen with no recovery path. This epic adds crash protection, defensive data guards, and graceful degradation so users never lose visibility into their research results.

## Stories

| Story | Title | Status |
|-------|-------|--------|
| 13.1 | Error Boundary & Defensive Result Guards | Done |

## Dependencies
- None (standalone resilience improvements)

## Files Affected
- `src/components/atoms/ErrorBoundary.tsx` (NEW)
- `src/components/templates/ResearchPage.tsx`
- `src/components/organisms/VendorRankings.tsx`
- `src/components/molecules/PriorityWeights.tsx`
