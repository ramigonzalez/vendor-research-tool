# Epic 10: Scoring Methodology & Explanation UI

## Status
Complete

## Goal
Make the scoring system fully transparent by providing visual formula breakdowns, confidence component visualization, and priority weight explanations — so users understand exactly how each vendor score, confidence value, and ranking is calculated.

## Business Value
- Addresses user pain point #4: "I want to know how the scoring is being applied"
- Addresses user pain point #5: "missing a clear explanation of the score and the confidence score"
- Builds trust through algorithmic transparency
- Enables informed decision-making by showing which factors drive each score

## Success Metrics
- Users can see the exact formula components for any vendor-requirement score
- Confidence breakdown shows all 4 components with color-coded quality indicators
- Scoring methodology is accessible via a single-click expandable section
- Client-side scoring formulas produce identical results to backend `engine.py`
- Priority weights are clearly explained with per-vendor contribution details

## Architecture Decision
- **Client-side scoring replication**: `scoring.ts` mirrors `app/scoring/engine.py` formulas exactly
- **Test coverage**: 25 unit tests verify formula parity between TypeScript and Python
- **Maintenance strategy**: `scoring.ts` header documents the Python source it mirrors
- **Score formula**: Capability (40%) + Evidence (30%) + Maturity (20%) - Limitations (10%)
- **Confidence formula**: Source Count (30%) + Authority (30%) + Recency (25%) + Consistency (15%)
- **Ranking formula**: `Sum(score x confidence x priority_weight) / max_possible x 100`

## Stories

| ID | Story | Points | Status | Executor |
|----|-------|--------|--------|----------|
| 10.1 | ScoringMethodology Explainer | 3 | Done | @dev |
| 10.2 | ConfidenceBreakdown Visualization | 4 | Done | @dev |
| 10.3 | ScoreBreakdown in Drill-Down | 3 | Done | @dev |
| 10.4 | PriorityWeights Legend & Ranking Explanation | 3 | Done | @dev |

**Total: 4 stories, 13 points**

## Dependencies
- Epic 7 (Foundation) — requires design tokens and migrated DrillDownPanel

## Risks & Mitigations
1. **Client-side scoring duplication** — Mitigated: 25 unit tests verify parity; `scoring.ts` header documents the Python source.
2. **Formula changes** — Mitigated: Any changes to `engine.py` must be reflected in `scoring.ts` and tests updated.
3. **Rounding differences** — Mitigated: Both TypeScript and Python use `Math.max(0, Math.min(10, ...))` clamping.

## Key References
| Asset | Path |
|-------|------|
| Backend scoring engine | `vendor-research-tool-backend/app/scoring/engine.py` |
| Client-side scoring | `vendor-research-tool-frontend/src/lib/scoring.ts` |
| Scoring tests | `vendor-research-tool-frontend/src/lib/scoring.test.ts` |
| ScoringMethodology | `vendor-research-tool-frontend/src/components/organisms/ScoringMethodology.tsx` |
| ConfidenceBreakdown | `vendor-research-tool-frontend/src/components/molecules/ConfidenceBreakdown.tsx` |
| ScoreBreakdown | `vendor-research-tool-frontend/src/components/molecules/ScoreBreakdown.tsx` |
| PriorityWeights | `vendor-research-tool-frontend/src/components/molecules/PriorityWeights.tsx` |

## Priority
P1 — Explanation (directly addresses user trust concerns)

## Sprint Allocation
- Sprint 2: Story 10.1 (3 pts)
- Sprint 3: Story 10.4 (3 pts)
- Sprint 4: Stories 10.2, 10.3 (7 pts)
