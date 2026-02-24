# Epic 3: API & Persistence Layer

**Epic Goal**: Build the FastAPI backend with SQLite persistence, repository pattern, SSE streaming endpoint, and all REST endpoints needed for the frontend.

**Integration Requirements**: Depends on domain models (E2-S1). Wraps the research pipeline (Epic 1) and scoring engine (Epic 2). Serves the frontend (Epic 4).

**MoSCoW**: All stories = Must Have (E3-S1 through E3-S4) + Could Have (E3-S5, E3-S6)
**Total Story Points**: 12

---

## Story 3.1 — SQLite Schema & Database Initialization

**As a** persistence layer,
**I want** a SQLite database schema with jobs, evidence, and scores tables,
**so that** all research results are persisted and resumable without re-running the expensive pipeline.

### Acceptance Criteria
1. Schema creates 3 tables: `jobs`, `evidence`, `scores`.
2. `jobs` table: `id TEXT PK`, `status TEXT`, `created_at TIMESTAMP`, `completed_at TIMESTAMP`, `progress_pct INTEGER`, `progress_message TEXT`, `summary TEXT`, `rankings_json TEXT`.
3. `evidence` table: `id INTEGER PK AUTOINCREMENT`, `job_id TEXT FK`, `vendor TEXT`, `requirement_id TEXT`, `claim TEXT`, `source_url TEXT`, `source_name TEXT`, `source_type TEXT`, `content_date TEXT`, `relevance REAL`, `supports_requirement INTEGER`, `created_at TIMESTAMP`.
4. `scores` table: `id INTEGER PK AUTOINCREMENT`, `job_id TEXT FK`, `vendor TEXT`, `requirement_id TEXT`, `score REAL`, `confidence REAL`, `capability_level TEXT`, `maturity TEXT`, `justification TEXT`, `limitations_json TEXT`, `UNIQUE(job_id, vendor, requirement_id)`.
5. Indexes: `evidence(job_id)`, `scores(job_id)`, `scores(job_id, vendor)`.
6. WAL mode enabled for concurrent read during streaming.
7. Schema initialization runs on app startup via `create_db_and_tables()` async function.
8. Database file: `research.db` in project root (created at runtime, not committed).

**Executor**: @data-engineer | **Quality Gate**: @dev
**Story Points**: 2

---

## Story 3.2 — Repository Pattern Implementation

**As a** API layer,
**I want** a `ResearchRepository` abstract interface with a `SQLiteResearchRepository` implementation,
**so that** data access is type-safe, testable, and can be swapped to PostgreSQL without business logic changes.

### Acceptance Criteria
1. Abstract `ResearchRepository` class in `app/repository.py` with async methods: `create_job()`, `update_job_status()`, `save_evidence()`, `save_score()`, `get_job()`, `get_results()`, `list_jobs()`.
2. `SQLiteResearchRepository` implements all abstract methods using `aiosqlite`.
3. `get_results()` returns `ResearchResults` assembled from joined `jobs + evidence + scores` tables.
4. `list_jobs()` returns `list[ResearchJob]` sorted by `created_at DESC`.
5. All methods use parameterized queries (no string formatting — prevents SQL injection).
6. Repository instance created once on startup and injected via FastAPI `Depends()`.
7. `MockResearchRepository` implemented for unit testing (in-memory dict, no SQLite).

**Executor**: @data-engineer | **Quality Gate**: @dev
**Story Points**: 3

---

## Story 3.3 — POST /api/research with SSE Streaming

**As a** frontend,
**I want** to trigger research via POST and receive real-time progress via Server-Sent Events,
**so that** research runs asynchronously and the UI updates continuously without polling.

### Acceptance Criteria
1. `POST /api/research` accepts JSON body (optional: vendor list override, requirement list override).
2. Endpoint creates a new job in SQLite, launches pipeline as background coroutine.
3. Returns `StreamingResponse` with `Content-Type: text/event-stream`.
4. SSE events streamed: `started` → `progress` (multiple) → `completed` or `error`.
5. Each event line formatted as: `data: {json_string}\n\n`.
6. Frontend uses `fetch + ReadableStream` to consume SSE (not EventSource — POST not supported).
7. Pipeline errors are caught and emitted as `{"type": "error", "message": "..."}` before stream close.
8. Job status updated in SQLite at each phase transition and on completion/failure.
9. CORS headers allow localhost development (configurable).

**Executor**: @dev | **Quality Gate**: @architect
**Story Points**: 3

---

## Story 3.4 — GET /api/research/{job_id}

**As a** frontend,
**I want** to retrieve cached research results by job ID,
**so that** completed results can be viewed without re-running the pipeline.

### Acceptance Criteria
1. `GET /api/research/{job_id}` returns `ResearchResults` JSON for completed jobs.
2. Returns 404 if job_id not found.
3. Returns `{"status": "running", "progress_pct": N}` for in-progress jobs.
4. Returns `{"status": "failed", "error": "..."}` for failed jobs.
5. Response includes full matrix: `matrix[vendor][requirement_id] = ScoreResult`.
6. Response includes `rankings: list[VendorRanking]` and `summary: str`.
7. Response time < 200ms for completed jobs (single SQLite read).

**Executor**: @dev | **Quality Gate**: @architect
**Story Points**: 2

---

## Story 3.5 — GET /api/jobs Listing

**As a** frontend,
**I want** to retrieve a list of previous research jobs,
**so that** users can navigate to past research results without re-running.

### Acceptance Criteria
1. `GET /api/jobs` returns `list[ResearchJob]` sorted by `created_at DESC`.
2. Each job includes: `id`, `status`, `created_at`, `completed_at`, `progress_pct`.
3. Returns empty list `[]` if no jobs exist.
4. Maximum 50 jobs returned (pagination not required for MVP).

**Executor**: @dev | **Quality Gate**: @architect
**Story Points**: 1

---

## Story 3.6 — Static File Serving & App Entry Point

**As a** developer,
**I want** FastAPI to serve `static/index.html` as the root route,
**so that** the frontend is accessible at `http://localhost:8000` without a separate web server.

### Acceptance Criteria
1. `GET /` returns `static/index.html` as HTML response.
2. `StaticFiles` mount serves any additional static assets from `static/` directory.
3. `app/main.py` creates FastAPI app, mounts router, mounts static files, configures CORS.
4. `uvicorn app.main:app --reload` starts the application correctly.
5. App startup triggers `create_db_and_tables()` (lifespan event).
6. Health check: `GET /health` returns `{"status": "ok"}`.

**Executor**: @dev | **Quality Gate**: @architect
**Story Points**: 1
