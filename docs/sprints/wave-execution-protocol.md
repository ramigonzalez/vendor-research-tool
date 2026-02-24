# Wave Execution Protocol

> **Purpose**: Defines entry/exit checklists, error handling, and commit protocol for parallel wave execution.
> **Used by**: Wave orchestrator and all story agents.

---

## Wave Lifecycle

```
Wave N Entry Check → Launch Parallel Agents → Agent Completion → Wave N Exit Check → Git Commit → Wave N+1
```

---

## Wave Entry Checklist

Before launching any agents in Wave N, verify ALL of the following:

### 1. Prior Wave Completion
- [ ] All stories in Wave N-1 marked complete in their wave log
- [ ] No stories in Wave N-1 have status `failed` that block Wave N stories
- [ ] If a Wave N-1 story failed: check if any Wave N story depends on it — skip dependent stories

### 2. File Existence Verification
Verify that files created by prior waves exist:

| Wave | Required Files (created by prior waves) |
|------|----------------------------------------|
| 0 | None (first wave) |
| 1 | `app/models.py`, `app/config.py`, `app/graph/state.py`, `requirements.txt`, `app/__init__.py`, `app/graph/__init__.py`, `app/scoring/__init__.py`, `app/prompts/__init__.py`, `tests/conftest.py` |
| 2 | Wave 1 files + `app/repository.py` (schema), `app/graph/nodes.py` (generate_queries), `app/scoring/engine.py` (confidence) |
| 3 | Wave 2 files + `app/repository.py` (full CRUD), `app/graph/nodes.py` (execute_searches, extract_evidence) |
| 4 | Wave 3 files + `app/graph/nodes.py` (assess_capabilities, compute_scores) |
| 5 | Wave 4 files + `app/scoring/engine.py` (rankings), `app/main.py` (static serving) |
| 6 | Wave 5 files + `app/main.py` (SSE endpoint), `app/graph/pipeline.py` |
| 7 | Wave 6 files + `static/index.html` (matrix rendering) |
| 8 | Wave 7 files + `static/index.html` (confidence + drill-down) |

### 3. Test Verification
```bash
# Run tests from prior wave
python -m pytest tests/ -x --tb=short
# Verify no import errors
python -c "from app.models import *; from app.config import *"
```

---

## Wave Exit Checklist

After ALL agents in Wave N complete:

### 1. Test Suite
```bash
python -m pytest tests/ -x --tb=short
```
- All tests must pass (zero failures)
- New tests from this wave must be included

### 2. Type Checking
```bash
python -m pyright app/
```
- No new type errors introduced (pre-existing warnings acceptable)

### 3. Import Verification
```bash
python -c "import app; import app.models; import app.config"
uvicorn app.main:app --reload &
sleep 2 && curl -s http://localhost:8000/health && kill %1
```

### 4. Wave Log Verification
- Every story in the wave has a completed log file in `docs/sprints/wave-logs/wave-N/`
- Each log file documents files created/modified, decisions, and test results

### 5. Exit Criteria from Sprint Plan
Check the specific exit criteria listed in `docs/sprints/sprint-plan.md` for Wave N.

---

## Error Handling Protocol

### Story Agent Failure

When a story agent encounters an unrecoverable error:

1. **Stop that story agent** — do not retry automatically
2. **Log the error** in `docs/sprints/wave-logs/wave-N/X.Y-story-name.md` with:
   - Error message and stack trace
   - What was completed before failure
   - Files created/modified (partial state)
   - Suggested remediation
3. **Continue other parallel agents** — a failure in one story does NOT stop sibling stories
4. **Mark story as `failed`** in the wave log
5. **Cascade check**: Before starting Wave N+1, check if any Wave N+1 story depends on the failed story. If so, skip that story too and log the skip reason.

### Dependency Cascade

```
If Story X fails in Wave N:
  → Find all stories in Wave N+1..N+8 that depend on X (directly or transitively)
  → Mark those stories as "blocked-by-failure"
  → Log in wave-logs: "Skipped: blocked by failed Story X"
  → Continue with non-dependent stories
```

### Recoverable Errors

For transient issues (network timeouts, API rate limits):
- Retry up to 2 times with exponential backoff
- If still failing after retries, treat as unrecoverable

---

## Commit Protocol

### When to Commit
- **After each wave exits successfully** (all exit checks pass)
- Never commit mid-wave (partial state could break parallel agents)
- Never commit if tests are failing

### Commit Message Format
```
feat: complete Wave N — [brief description]

Stories completed:
- X.Y: [story name]
- X.Y: [story name]

[optional: notes about skipped/failed stories]
```

### Git Commands
```bash
git add -A
git commit -m "feat: complete Wave N — [description]"
```

---

## Parallel Agent Rules

### File Ownership
- Each story agent MUST only modify files assigned to it in `file-ownership-map.md`
- If an agent needs to modify a file it doesn't own, it must document the need in its wave log and defer to the owning agent
- See `docs/sprints/file-ownership-map.md` for per-wave ownership

### Shared File Protocol
When two agents in the same wave need the same file (rare — see ownership map):
1. Designate one agent as "primary owner"
2. Primary owner writes first
3. Secondary agent waits for primary, then appends/extends
4. In practice: run them sequentially within the wave

### Communication via Wave Logs
- Agents cannot communicate directly during execution
- All inter-agent info flows through wave log files
- Downstream agents read prior wave logs for context

---

## Wave Execution Order

| Wave | Stories | Max Parallelism | Sequential Dependencies Within Wave |
|------|---------|-----------------|--------------------------------------|
| 0 | 5.1, 2.1 | 2 | None |
| 1 | 3.1, 1.1, 1.5, 2.4 | 4 | None |
| 2 | 3.2, 1.2, 1.3 | 2 then 1 | 1.3 waits for 3.2 AND 1.2 |
| 3 | 1.4, 2.2, 2.3 | 2 then 1 | 2.3 waits for 2.2 |
| 4 | 2.5, 3.4, 3.6, 3.5 | 4 | None |
| 5 | 3.3, 4.4 (backend) | 2 | None |
| 6 | 4.1, 4.5 | 2 | None |
| 7 | 4.2, 4.3, 4.4 (frontend) | 3 | None |
| 8 | 5.2, 5.3, 5.4 | 3 | None |

---

## Quick Reference: Orchestrator Script Pseudocode

```python
for wave_num in range(9):
    # 1. Entry check
    verify_prior_wave_complete(wave_num - 1)
    verify_required_files(wave_num)
    run_tests()

    # 2. Launch agents
    stories = get_wave_stories(wave_num)
    parallel, sequential = partition_by_dependencies(stories)

    # Launch parallel stories
    results = await asyncio.gather(*[
        run_story_agent(story) for story in parallel
    ], return_exceptions=True)

    # Launch sequential stories (if any)
    for story in sequential:
        if all_dependencies_met(story, results):
            result = await run_story_agent(story)
            results.append(result)

    # 3. Exit check
    run_tests()
    run_type_check()
    verify_wave_logs(wave_num)

    # 4. Commit
    git_commit(wave_num, stories)
```
