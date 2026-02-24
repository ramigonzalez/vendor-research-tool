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

### 3. Quality Verification
```bash
# Run full quality gate from prior wave
make check
# Verify no import errors (redundant with make check, but explicit)
python -c "from app.models import *; from app.config import *"
```

---

## Wave Exit Checklist — 3-Layer Quality Gate

After ALL agents in Wave N complete, the wave must pass **all three layers** sequentially (fail-fast).

---

### Layer 1: Automated Quality Gates (mandatory, every wave)

**Single command**: `make check` — runs lint → format-check → typecheck → test+coverage sequentially, fail-fast.

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| **Linting** | `python -m ruff check app/ tests/` | Zero errors |
| **Formatting** | `python -m ruff format --check app/ tests/` | All files conform |
| **Type checking** | `python -m pyright app/` | No new type errors (basic mode) |
| **Tests + coverage** | `python -m pytest tests/` | Zero failures, ≥60% coverage |
| **Import verification** | `python -c "import app; ..."` + uvicorn healthcheck | Clean startup |

```bash
# Run all Layer 1 checks at once:
make check

# If make is not yet available (Wave 0), run individually:
python -m ruff check app/ tests/ && \
python -m ruff format --check app/ tests/ && \
python -m pyright app/ && \
python -m pytest tests/ -x --tb=short --cov=app --cov-fail-under=60
```

**Layer 1 FAIL → wave cannot proceed. Fix issues and re-run.**

---

### Layer 2: Per-Story Quality Gate Agent Review (every wave, after Layer 1)

For each story in the wave:

1. **Read** the story's `quality_gate` field from its YAML header (e.g., `quality_gate: "@architect"`)
2. **Activate** the quality gate agent (e.g., @architect or @qa) to review the story's output
3. **Agent uses** the story's `quality_gate_tools` (e.g., `["Read", "Grep", "mcp__ide__getDiagnostics"]`) to verify:
   - All acceptance criteria are met (checkbox each AC)
   - Wave log is complete and accurate
   - Code follows existing patterns and conventions
   - No regressions introduced in shared files
4. **Agent writes verdict** in the wave log: `PASS` | `FAIL` | `PASS_WITH_NOTES`
5. **FAIL blocks wave exit** — agent must document what needs fixing

**Review protocol per story**:
```
For story X.Y in Wave N:
  1. Read docs/stories/X.Y.story-name.md → get quality_gate agent
  2. Read docs/sprints/wave-logs/wave-N/X.Y-story-name.md → verify completeness
  3. Review each AC → confirm implementation matches spec
  4. Run quality_gate_tools checks → verify no diagnostics issues
  5. Write verdict → PASS / FAIL / PASS_WITH_NOTES
```

**Recommended for Waves 2–5**: Also run @qa agent review on edge cases in async/LLM code (search execution, evidence extraction, gap analysis).

---

### Layer 3: Human @architect Review (milestone waves only)

Layer 3 triggers only at key milestones to keep velocity high during the prototype sprint.

| Checkpoint | After Wave | Focus Areas |
|------------|-----------|-------------|
| **MVP Gate** | Wave 6 | End-to-end flow works, architecture sound, no critical debt |
| **Final Delivery** | Wave 8 | Polish quality, docs complete, demo-ready |

**Layer 3 review includes**:
- Architecture consistency across all completed waves
- Security review (API key handling, input validation)
- Performance sanity check (no obvious bottlenecks)
- Documentation completeness (README, inline docs)

---

### Post-Gate: Wave Log & Sprint Plan Verification

After all 3 layers pass:

1. Every story in the wave has a completed log file in `docs/sprints/wave-logs/wave-N/`
2. Each log file documents files created/modified, decisions, and test results
3. Check the specific exit criteria listed in `docs/sprints/sprint-plan.md` for Wave N

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
MILESTONE_WAVES = {6, 8}  # Layer 3 human review checkpoints

for wave_num in range(9):
    # 1. Entry check
    verify_prior_wave_complete(wave_num - 1)
    verify_required_files(wave_num)
    run_quality_gate("make check")  # Layer 1 on prior state

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

    # 3. Layer 1: Automated quality gates
    run_quality_gate("make check")  # lint → format → typecheck → test+cov

    # 4. Layer 2: Per-story quality gate agent review
    for story in stories:
        gate_agent = story.yaml_header["quality_gate"]  # e.g., "@architect"
        gate_tools = story.yaml_header["quality_gate_tools"]
        verdict = await run_quality_gate_review(gate_agent, story, gate_tools)
        if verdict == "FAIL":
            raise WaveExitFailed(f"Layer 2 FAIL: {story.id} — {verdict.reason}")

    # 5. Layer 3: Human review (milestone waves only)
    if wave_num in MILESTONE_WAVES:
        await request_human_architect_review(wave_num)

    # 6. Verify wave logs + commit
    verify_wave_logs(wave_num)
    git_commit(wave_num, stories)
```
