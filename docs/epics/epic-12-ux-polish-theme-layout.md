# Epic 12: UX Polish — Theme System, Layout & Hierarchy

## Overview
Address multiple UX issues: no manual dark/light mode switch, sparse home page, Research Analysis taking too much space after completion, and Executive Summary lacking proper hierarchy with a progress bar bug.

## Stories

| Story | Title | Status |
|-------|-------|--------|
| 12.1 | Dark/Light/System Theme Toggle | Pending |
| 12.2 | Home Page Layout & Hero State | Pending |
| 12.3 | Collapsible Research Analysis | Pending |
| 12.4 | Executive Summary & Rankings Hierarchy | Pending |
| 12.5 | Comparison Matrix Readability | Pending |
| 12.6 | End-to-End Score Status Tracking | Pending |

## Dependencies
- Stories 12.2–12.4 depend on 12.1 (ThemeToggle component used in header)
- Stories 12.3 and 12.4 are independent of each other

## Files Affected
- `src/styles/globals.css`
- `src/contexts/ThemeContext.tsx` (NEW)
- `src/components/atoms/ThemeToggle.tsx` (NEW)
- `src/App.tsx`
- `index.html`
- `src/components/templates/ResearchPage.tsx`
- `src/components/organisms/AuditView.tsx`
- `src/components/organisms/ExecutiveSummary.tsx`
- `src/components/organisms/ScoringMethodology.tsx`
