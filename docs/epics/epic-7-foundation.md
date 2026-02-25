# Epic 7: Foundation — Repo Restructure, React Migration & Design System

## Status
Complete

## Goal
Split monorepo into independently deployable backend/frontend directories, fix critical data bugs, scaffold a modern React + Tailwind CSS + Vite (TypeScript) frontend, migrate existing UI to React components, and establish a design token system.

## Business Value
- Enables independent deployment of frontend (Vercel/Railway) and backend (Railway/Render)
- Fixes critical bug where requirement descriptions showed as "R1" instead of full text
- Establishes portfolio-grade frontend architecture for maintainability and extensibility
- Provides accessible, standards-compliant UI foundation

## Success Metrics
- Backend tests pass after restructure (192 passed, 94% coverage)
- Frontend builds with zero TypeScript errors
- Visual parity with previous inline HTML UI
- WCAG AA accessibility compliance on core interactions

## Architecture Decision
- **Decoupled architecture**: `vendor-research-tool-backend/` and `vendor-research-tool-frontend/` within monorepo
- **Frontend stack**: React 19 + Vite 7 + TypeScript 5.9 + Tailwind CSS v4
- **API connection**: `VITE_API_URL` env var (no Vite proxy)
- **Backend CORS**: `ALLOWED_ORIGINS` env var
- **Design tokens**: CSS-first `@theme` blocks (Tailwind v4), mapped from `docs/ux/tokens.yaml`
- **Component architecture**: Atomic Design (atoms/molecules/organisms/templates)

## Stories

| ID | Story | Points | Status | Executor |
|----|-------|--------|--------|----------|
| 7.0 | Restructure Monorepo into Backend + Frontend Directories | 3 | Done | @dev |
| 7.1 | Fix Requirement Descriptions & Priority Mapping | 2 | Done | @dev |
| 7.2 | Scaffold Vite + React + TypeScript + Tailwind Project | 3 | Done | @dev |
| 7.3 | Configure Tailwind Theme from Design Tokens | 3 | Done | @dev |
| 7.4 | Migrate Existing UI to React Components | 5 | Done | @dev |
| 7.5 | Accessibility Foundations | 3 | Done | @dev |

**Total: 6 stories, 19 points**

## Dependencies
- None (foundation epic)

## Risks & Mitigations
1. **Monorepo restructure breaks imports** — Mitigated: `app/` moved as unit, imports unchanged. Verified with `pytest`.
2. **React migration visual regression** — Mitigated: Tailwind classes from tokens.yaml ensure consistent styling.

## Key References
| Asset | Path |
|-------|------|
| Design tokens | `docs/ux/tokens.yaml` |
| Design system | `docs/ux/design-system-overview.md` |
| Scoring engine | `vendor-research-tool-backend/app/scoring/engine.py` |
| Config (requirements) | `vendor-research-tool-backend/app/config.py` |

## Priority
P0 — Foundation (all other epics depend on this)

## Sprint Allocation
- Sprint 1: Stories 7.0, 7.1, 7.2, 7.3 (11 pts)
- Sprint 2: Stories 7.4, 7.5 (8 pts)
