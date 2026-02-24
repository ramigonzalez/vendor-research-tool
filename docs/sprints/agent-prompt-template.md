# Agent Prompt Template

> **Purpose**: Standard prompt structure for every story agent. Copy and fill in the template before launching an agent.

---

## Template

```markdown
# Story Agent: {story_id} — {story_name}

## Wave Context
- **Wave**: {wave_number}
- **Parallel siblings**: {list of other stories running in this wave}
- **Sequential dependency**: {if this story must wait for another in-wave story, note it here}

## Story Specification

{paste full story content from docs/stories/X.Y.story-name.md}

## Dependency Outputs

The following stories have already been completed. Their outputs are available:

{for each dependency, list:}
### Story {dep_id} — {dep_name} (Wave {dep_wave})
- **Files created**: {list from wave log}
- **Key decisions**: {from wave log}
- **Deviations**: {from wave log, if any}
- **Warnings for downstream**: {from wave log, if any}

## File Ownership

### Files YOU own (create/modify freely):
{list from file-ownership-map.md for this story}

### Files you must NOT modify (owned by parallel agents):
{list files owned by sibling stories in this wave}

### Files you may READ but not WRITE:
{list files from prior waves that you depend on}

## Decision Log Requirement

**MANDATORY**: Before completing, you MUST create a wave log file at:

```
docs/sprints/wave-logs/wave-{N}/{X.Y}-{story-name-slug}.md
```

The log MUST contain the following sections:

### Log Template:

```markdown
# Wave Log: Story {X.Y} — {Story Name}

## Status: {completed | failed | partial}

## Files Created
| File | Lines | Description |
|------|-------|-------------|
| path/to/file.py | ~N | Brief description |

## Files Modified
| File | Changes | Description |
|------|---------|-------------|
| path/to/file.py | Added function X | Brief description |

## Decisions Made
| Decision | Rationale | Alternatives Considered |
|----------|-----------|------------------------|
| Used X pattern | Because Y | Could have done Z |

## Deviations from Story Spec
{List any deviations from acceptance criteria, with justification}
{Write "None" if fully compliant}

## Test Results
```
{paste pytest output summary}
```

## Warnings for Downstream Stories
{List anything that downstream stories should know about}
{e.g., "Used different function signature than suggested in dev notes"}
{Write "None" if no warnings}

## Blockers Encountered
{List any blockers and how they were resolved}
{Write "None" if no blockers}
```

## Execution Rules

1. Read the COMPLETE story spec before writing any code
2. Check file ownership — only modify files you own
3. Run quality checks after implementation: `make check` (lint → format-check → typecheck → test+coverage)
4. Write your wave log BEFORE signaling completion
5. If you encounter an error you can't resolve in 3 attempts, STOP and document it in the wave log with status `failed`
6. Do NOT modify files outside your ownership list
7. Do NOT skip acceptance criteria — implement ALL of them
8. Follow existing code patterns (check prior wave outputs for style)

## Quality Gate Responsibilities

Before signaling completion, you MUST pass all automated quality checks:

### Required Commands (run in order)
```bash
# Format your code (auto-fix)
python -m ruff format app/ tests/

# Lint check (must be zero errors)
python -m ruff check app/ tests/

# Type check (no new errors in basic mode)
python -m pyright app/

# Tests + coverage (zero failures, ≥60% coverage)
python -m pytest tests/ -x --tb=short --cov=app --cov-fail-under=60

# Or run all at once:
make check
```

### Post-Completion Review
After you complete your work, a **quality gate reviewer** (specified in your story's `quality_gate` field) will verify:
- All acceptance criteria are met
- Wave log is complete and accurate
- Code follows existing patterns and conventions
- No regressions in shared files

The reviewer uses the tools listed in your story's `quality_gate_tools` field. Your work must pass this review before the wave can proceed.

### Quick Reference
| Tool | Purpose | Command |
|------|---------|---------|
| ruff | Lint + format | `python -m ruff check app/ tests/` |
| ruff format | Code formatting | `python -m ruff format app/ tests/` |
| pyright | Type checking | `python -m pyright app/` |
| pytest-cov | Tests + coverage | `python -m pytest tests/` |
| make check | All of the above | `make check` |
```

---

## Example: Filled Template for Story 2.4 (Wave 1)

```markdown
# Story Agent: 2.4 — Confidence Score Computation

## Wave Context
- **Wave**: 1
- **Parallel siblings**: 3.1 (SQLite Schema), 1.1 (Query Generation), 1.5 (SSE Progress)
- **Sequential dependency**: None

## Story Specification
[full content of docs/stories/2.4.confidence-computation.md]

## Dependency Outputs

### Story 2.1 — Pydantic Domain Models (Wave 0)
- **Files created**: app/models.py (~90 lines), app/graph/state.py (~25 lines)
- **Key decisions**: Used str Enum pattern for all enums
- **Deviations**: None
- **Warnings**: ResearchState uses TypedDict, not Pydantic

## File Ownership

### Files YOU own:
- `app/scoring/engine.py` (CREATE — confidence computation)
- `tests/test_scoring.py` (CREATE — confidence tests)

### Files you must NOT modify:
- `app/repository.py` (owned by 3.1)
- `app/graph/nodes.py` (owned by 1.1)
- `app/graph/state.py` (owned by 1.5 for progress_queue addition)
- `app/prompts/research.py` (owned by 1.1)

### Files you may READ but not WRITE:
- `app/models.py` (from Wave 0)
- `app/config.py` (from Wave 0)
- `tests/conftest.py` (from Wave 0)
```

---

## Wave Log Directory Structure

```
docs/sprints/wave-logs/
├── wave-0/
│   ├── 5.1-project-setup.md
│   └── 2.1-pydantic-domain-models.md
├── wave-1/
│   ├── 3.1-sqlite-schema.md
│   ├── 1.1-query-generation-node.md
│   ├── 1.5-sse-progress-events.md
│   └── 2.4-confidence-computation.md
├── wave-2/
│   ├── 3.2-repository-pattern.md
│   ├── 1.2-parallel-search-execution.md
│   └── 1.3-evidence-extraction.md
├── wave-3/
│   ├── 1.4-gap-analysis-loop.md
│   ├── 2.2-llm-capability-assessment.md
│   └── 2.3-score-computation.md
├── wave-4/
│   ├── 2.5-weighted-ranking.md
│   ├── 3.4-get-results-endpoint.md
│   ├── 3.6-static-file-serving.md
│   └── 3.5-job-listing-endpoint.md
├── wave-5/
│   ├── 3.3-fastapi-sse-endpoint.md
│   └── 4.4-executive-summary-backend.md
├── wave-6/
│   ├── 4.1-comparison-matrix.md
│   └── 4.5-progress-display.md
├── wave-7/
│   ├── 4.2-confidence-visualization.md
│   ├── 4.3-evidence-drill-down.md
│   └── 4.4-executive-summary-frontend.md
└── wave-8/
    ├── 5.2-ui-styling.md
    ├── 5.3-readme-documentation.md
    └── 5.4-job-history-page.md
```
