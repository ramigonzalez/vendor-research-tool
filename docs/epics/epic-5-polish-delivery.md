# Epic 5: Polish & Delivery

**Epic Goal**: Project setup, UI styling polish, complete documentation, and optional job history page to make the tool demo-ready and evaluator-friendly.

**Integration Requirements**: Builds on all previous epics. E5-S1 (project setup) should actually be implemented first in the build order — it provides the scaffold for all other epics.

**MoSCoW**: E5-S1 (Must Have — critical-path first story), E5-S3 (Should Have), E5-S2 + E5-S4 (Could Have)
**Total Story Points**: 7

---

## Story 5.1 — Project Setup & Environment

**As a** developer setting up the project,
**I want** a complete project scaffold with dependencies, configuration, and environment setup,
**so that** the tool runs with `git clone → pip install -r requirements.txt → uvicorn app.main:app`.

### Acceptance Criteria
1. `requirements.txt` lists all dependencies with pinned versions: `fastapi`, `uvicorn[standard]`, `langchain`, `langgraph`, `langchain-anthropic`, `tavily-python`, `aiosqlite`, `pydantic-settings`, `python-dotenv`.
2. `.env.example` contains placeholder entries: `ANTHROPIC_API_KEY=sk-ant-xxx`, `TAVILY_API_KEY=tvly-xxx`.
3. `app/config.py` uses `pydantic-settings` `BaseSettings` to load API keys from environment.
4. `app/config.py` defines `VENDORS: list[str]` (4 vendors) and `REQUIREMENTS: list[Requirement]` (6 requirements with weights).
5. Running `uvicorn app.main:app --reload` from project root starts server without errors.
6. `__init__.py` files present in `app/`, `app/graph/`, `app/scoring/`, `app/prompts/`.
7. `tests/` directory with `conftest.py` and one smoke test.

**Executor**: @dev | **Quality Gate**: @architect
**Story Points**: 2

---

## Story 5.2 — UI Styling Polish

**As a** evaluator reviewing the tool,
**I want** a clean, professional visual design,
**so that** the tool looks production-quality and the data is easy to read.

### Acceptance Criteria
1. CSS custom properties define color tokens: `--color-high`, `--color-medium`, `--color-low`, `--color-bg`, `--color-surface`, `--color-text`.
2. Matrix table has clear visual hierarchy: sticky header row, alternating row backgrounds.
3. Responsive design: matrix scrollable horizontally on screens < 900px wide.
4. Typography: system font stack, 14px base size for matrix cells, 16px for body text.
5. Loading state: animated pulse/skeleton for cells during data load.
6. Vendor header cells display vendor name + overall rank badge.
7. "Could Have" — not blocking MVP if cut for time.

**Executor**: @dev | **Quality Gate**: @architect
**Story Points**: 2

---

## Story 5.3 — README & Documentation

**As a** new developer or evaluator,
**I want** a comprehensive README,
**so that** I can set up, run, and understand the tool without reading the source code.

### Acceptance Criteria
1. `README.md` includes: project description, setup instructions (clone → .env → pip install → run), API key requirements with links.
2. Architecture overview section: C4 context diagram (text/ASCII or embedded image), LangGraph pipeline description, scoring methodology summary.
3. Configuration section: how to modify vendors, requirements, weights in `config.py`.
4. Scaling section: brief description of how architecture would scale to 50 vendors × 200 requirements.
5. Known limitations section: fixed vendors, no auth, local-only.
6. Setup verified: instructions tested against clean environment.

**Executor**: @dev | **Quality Gate**: @architect
**Story Points**: 2

---

## Story 5.4 — Job History Page

**As a** user,
**I want** to see a list of previous research runs,
**so that** I can revisit past results without re-running the expensive pipeline.

### Acceptance Criteria
1. Job history section (collapsible or separate tab) shows list of completed jobs.
2. Each job entry shows: creation timestamp, status badge, "View Results" button.
3. "View Results" loads results from `GET /api/research/{job_id}` and renders matrix.
4. Failed jobs shown with error indicator.
5. Empty state shown when no previous jobs exist.
6. "Could Have" — cut if time-constrained.

**Executor**: @dev | **Quality Gate**: @architect
**Story Points**: 1
