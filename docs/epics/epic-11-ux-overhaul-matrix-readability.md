# Epic 11: UX Overhaul — Matrix Readability & Component Polish

## Overview

Address 7 UX issues (3 CRITICAL, 3 HIGH, 1 MEDIUM) identified during product owner review of the live UI. The most impactful problems involve oppressive near-black matrix headers, raw markdown rendering in executive summaries, confusing confidence breakdown colors, and missing requirement context.

## Business Value

- **User Trust:** Professional-looking comparison matrix increases confidence in research results
- **Readability:** Properly rendered markdown and distinct color semantics reduce cognitive load
- **Completeness:** Requirement IDs and priority indicators provide full context without drill-down

## Scope

### CRITICAL (Phase A)
1. Matrix header colors too dark (near-black `bg-text-primary`)
2. Priority section rows use hardcoded dark backgrounds (`bg-[#34495e]`)
3. Requirement rows missing ID prefix and priority badge
4. Confidence breakdown reuses score colors (green/orange/red) with different semantics
5. ScoringMethodology Source Count bar inconsistent with confidence breakdown

### HIGH (Phase B)
6. Executive summary renders raw markdown (literal `**bold**` asterisks)
7. PriorityWeights per-vendor breakdown too small, missing req descriptions
8. ResearchTimeline lacks auto-collapse and smooth animation

### MEDIUM (Phase C)
9. Rankings section in ExecutiveSummary is plain text, no visual hierarchy

## Success Metrics

- All matrix headers use professional dark blue-gray (#2c3e50 light / #1e293b dark)
- Priority rows use tinted backgrounds with colored left borders
- Each requirement row displays `[Priority Badge] req.id description`
- Confidence breakdown uses 4 distinct category colors (teal/blue/purple/copper)
- Executive summary renders formatted markdown with serif font
- Rankings show score bars with #1 highlight
- Timeline auto-collapses after completion with smooth CSS transition
- `npm run lint && npm run typecheck` pass with zero errors

## Stories

| Story | Title | Phase | Priority |
|-------|-------|-------|----------|
| 11.1 | UX Overhaul: Comparison Matrix Readability & Component Polish | A/B/C | CRITICAL → MEDIUM |

## Dependencies

- None (all changes are frontend-only, no API changes)

## Risks

- Font loading: Source Serif 4 already imported but never used — verify it loads correctly
- Color accessibility: New tinted priority rows must maintain sufficient contrast ratios
- react-markdown: New dependency — verify bundle size impact is acceptable

---

*Epic created by @pm — 2026-02-25*
