"""SQLite database initialization for the Vendor Research Tool.

Provides schema creation for jobs, evidence, and scores tables
using aiosqlite with WAL journal mode.
"""

from __future__ import annotations

from pathlib import Path

import aiosqlite

DB_PATH = Path(__file__).parent.parent / "research.db"

_JOBS_TABLE = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    progress_pct INTEGER DEFAULT 0,
    progress_message TEXT DEFAULT '',
    summary TEXT,
    rankings_json TEXT
)
"""

_EVIDENCE_TABLE = """
CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL REFERENCES jobs(id),
    vendor TEXT NOT NULL,
    requirement_id TEXT NOT NULL,
    claim TEXT,
    source_url TEXT,
    source_name TEXT,
    source_type TEXT,
    content_date TEXT,
    relevance REAL,
    supports_requirement INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

_SCORES_TABLE = """
CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL REFERENCES jobs(id),
    vendor TEXT NOT NULL,
    requirement_id TEXT NOT NULL,
    score REAL,
    confidence REAL,
    capability_level TEXT,
    maturity TEXT,
    justification TEXT,
    limitations_json TEXT,
    UNIQUE(job_id, vendor, requirement_id)
)
"""

_EVIDENCE_JOB_ID_INDEX = "CREATE INDEX IF NOT EXISTS idx_evidence_job_id ON evidence(job_id)"
_SCORES_JOB_ID_INDEX = "CREATE INDEX IF NOT EXISTS idx_scores_job_id ON scores(job_id)"


async def create_db_and_tables(db_path: Path | str | None = None) -> None:
    """Create the SQLite database and all required tables.

    Args:
        db_path: Optional override for the database file path.
                 Defaults to DB_PATH (research.db at project root).
                 Pass ":memory:" for in-memory databases in tests.
    """
    path = str(db_path) if db_path is not None else str(DB_PATH)

    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(_JOBS_TABLE)
        await db.execute(_EVIDENCE_TABLE)
        await db.execute(_SCORES_TABLE)
        await db.execute(_EVIDENCE_JOB_ID_INDEX)
        await db.execute(_SCORES_JOB_ID_INDEX)
        await db.commit()
