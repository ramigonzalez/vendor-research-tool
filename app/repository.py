"""SQLite database initialization and repository pattern for the Vendor Research Tool.

Provides schema creation for jobs, evidence, and scores tables
using aiosqlite with WAL journal mode, plus an abstract repository
interface and its SQLite implementation.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path

import aiosqlite

from app.models import (
    CapabilityLevel,
    Evidence,
    JobStatus,
    MaturityLevel,
    Priority,
    Requirement,
    ResearchJob,
    ResearchResults,
    ScoreResult,
    SourceType,
    VendorRanking,
)

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


# ---------------------------------------------------------------------------
# Abstract Repository
# ---------------------------------------------------------------------------


class ResearchRepository(ABC):
    """Abstract base class defining the research data access interface."""

    @abstractmethod
    async def create_job(self, job: ResearchJob) -> None: ...

    @abstractmethod
    async def update_job_status(
        self, job_id: str, status: JobStatus, progress_pct: int, progress_message: str
    ) -> None: ...

    @abstractmethod
    async def save_evidence(self, job_id: str, vendor: str, req_id: str, evidence: list[Evidence]) -> None: ...

    @abstractmethod
    async def save_score(self, job_id: str, vendor: str, req_id: str, score_result: ScoreResult) -> None: ...

    @abstractmethod
    async def get_job(self, job_id: str) -> ResearchJob | None: ...

    @abstractmethod
    async def get_results(self, job_id: str) -> ResearchResults | None: ...

    @abstractmethod
    async def list_jobs(self, limit: int = 50) -> list[ResearchJob]: ...

    @abstractmethod
    async def save_final_results(self, job_id: str, summary: str, rankings: list[VendorRanking]) -> None: ...


# ---------------------------------------------------------------------------
# SQLite Implementation
# ---------------------------------------------------------------------------


class SQLiteResearchRepository(ResearchRepository):
    """SQLite-backed implementation of the ResearchRepository interface."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    async def _connect(self) -> aiosqlite.Connection:
        """Open a new connection to the database."""
        db = await aiosqlite.connect(self._db_path)
        db.row_factory = aiosqlite.Row
        return db

    async def create_job(self, job: ResearchJob) -> None:
        """Insert a new research job record."""
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "INSERT INTO jobs (id, status, created_at, completed_at, progress_pct, progress_message) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    job.id,
                    job.status.value,
                    job.created_at.isoformat(),
                    job.completed_at.isoformat() if job.completed_at else None,
                    job.progress_pct,
                    job.progress_message,
                ),
            )
            await db.commit()

    async def update_job_status(self, job_id: str, status: JobStatus, progress_pct: int, progress_message: str) -> None:
        """Update the status, progress percentage, and message for a job."""
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "UPDATE jobs SET status = ?, progress_pct = ?, progress_message = ? WHERE id = ?",
                (status.value, progress_pct, progress_message, job_id),
            )
            await db.commit()

    async def save_evidence(self, job_id: str, vendor: str, req_id: str, evidence: list[Evidence]) -> None:
        """Bulk-insert evidence records for a vendor-requirement pair."""
        async with aiosqlite.connect(self._db_path) as db:
            for ev in evidence:
                await db.execute(
                    "INSERT INTO evidence (job_id, vendor, requirement_id, claim, source_url, "
                    "source_name, source_type, content_date, relevance, supports_requirement) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        job_id,
                        vendor,
                        req_id,
                        ev.claim,
                        ev.source_url,
                        ev.source_name,
                        ev.source_type.value,
                        ev.content_date,
                        ev.relevance,
                        int(ev.supports_requirement),
                    ),
                )
            await db.commit()

    async def save_score(self, job_id: str, vendor: str, req_id: str, score_result: ScoreResult) -> None:
        """Insert or replace a score record for a vendor-requirement pair."""
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO scores (job_id, vendor, requirement_id, score, confidence, "
                "capability_level, maturity, justification, limitations_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    job_id,
                    vendor,
                    req_id,
                    score_result.score,
                    score_result.confidence,
                    score_result.capability_level.value,
                    score_result.maturity.value,
                    score_result.justification,
                    json.dumps(score_result.limitations),
                ),
            )
            await db.commit()

    async def save_final_results(self, job_id: str, summary: str, rankings: list[VendorRanking]) -> None:
        """Mark a job as completed and store summary and rankings."""
        rankings_data = [{"vendor": r.vendor, "overall_score": r.overall_score, "rank": r.rank} for r in rankings]
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "UPDATE jobs SET summary = ?, rankings_json = ?, completed_at = ?, status = ? WHERE id = ?",
                (
                    summary,
                    json.dumps(rankings_data),
                    datetime.now(UTC).isoformat(),
                    JobStatus.completed.value,
                    job_id,
                ),
            )
            await db.commit()

    async def get_job(self, job_id: str) -> ResearchJob | None:
        """Retrieve a single job by ID, or None if not found."""
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = await cursor.fetchone()
            if row is None:
                return None
            return _row_to_job(row)

    async def get_results(self, job_id: str) -> ResearchResults | None:
        """Assemble full ResearchResults by joining jobs, scores, and evidence."""
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row

            # Fetch job
            cursor = await db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            job_row = await cursor.fetchone()
            if job_row is None:
                return None

            summary = job_row["summary"] or ""
            rankings_raw = job_row["rankings_json"]
            rankings: list[VendorRanking] = []
            if rankings_raw:
                for r in json.loads(rankings_raw):
                    rankings.append(VendorRanking(vendor=r["vendor"], overall_score=r["overall_score"], rank=r["rank"]))

            # Fetch scores
            cursor = await db.execute(
                "SELECT vendor, requirement_id, score, confidence, capability_level, maturity, "
                "justification, limitations_json FROM scores WHERE job_id = ?",
                (job_id,),
            )
            score_rows = await cursor.fetchall()

            # Fetch evidence
            cursor = await db.execute(
                "SELECT vendor, requirement_id, claim, source_url, source_name, source_type, "
                "content_date, relevance, supports_requirement FROM evidence WHERE job_id = ?",
                (job_id,),
            )
            evidence_rows = await cursor.fetchall()

            # Build evidence lookup: (vendor, req_id) -> list[Evidence]
            evidence_map: dict[tuple[str, str], list[Evidence]] = {}
            for erow in evidence_rows:
                key = (erow["vendor"], erow["requirement_id"])
                ev = Evidence(
                    claim=erow["claim"] or "",
                    source_url=erow["source_url"] or "",
                    source_name=erow["source_name"] or "",
                    source_type=SourceType(erow["source_type"]) if erow["source_type"] else SourceType.blog,
                    content_date=erow["content_date"],
                    relevance=erow["relevance"] or 0.0,
                    supports_requirement=bool(erow["supports_requirement"]),
                )
                evidence_map.setdefault(key, []).append(ev)

            # Build matrix and collect vendors/requirements
            vendors_set: set[str] = set()
            req_ids_set: set[str] = set()
            matrix: dict[str, dict[str, ScoreResult]] = {}

            for srow in score_rows:
                vendor = srow["vendor"]
                req_id = srow["requirement_id"]
                vendors_set.add(vendor)
                req_ids_set.add(req_id)

                limitations = json.loads(srow["limitations_json"]) if srow["limitations_json"] else []
                ev_list = evidence_map.get((vendor, req_id), [])

                score_result = ScoreResult(
                    score=srow["score"] or 0.0,
                    confidence=srow["confidence"] or 0.0,
                    capability_level=CapabilityLevel(srow["capability_level"])
                    if srow["capability_level"]
                    else CapabilityLevel.unknown,
                    maturity=MaturityLevel(srow["maturity"]) if srow["maturity"] else MaturityLevel.unknown,
                    justification=srow["justification"] or "",
                    limitations=limitations,
                    evidence=ev_list,
                )

                matrix.setdefault(vendor, {})[req_id] = score_result

            vendors = sorted(vendors_set)
            # Build Requirement objects from req IDs (description not stored in scores,
            # so we use the ID as a placeholder description)
            requirements = [
                Requirement(id=rid, description=rid, priority=Priority.medium) for rid in sorted(req_ids_set)
            ]

            return ResearchResults(
                vendors=vendors,
                requirements=requirements,
                matrix=matrix,
                rankings=rankings,
                summary=summary,
            )

    async def list_jobs(self, limit: int = 50) -> list[ResearchJob]:
        """List jobs ordered by creation time descending, up to limit."""
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            rows = await cursor.fetchall()
            return [_row_to_job(row) for row in rows]


def _row_to_job(row: aiosqlite.Row) -> ResearchJob:
    """Convert a database row to a ResearchJob model."""
    return ResearchJob(
        id=row["id"],
        status=JobStatus(row["status"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
        progress_pct=row["progress_pct"] or 0,
        progress_message=row["progress_message"] or "",
    )


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_repository: SQLiteResearchRepository | None = None


def get_repository() -> SQLiteResearchRepository:
    """Return the singleton SQLiteResearchRepository instance."""
    global _repository
    if _repository is None:
        _repository = SQLiteResearchRepository(str(DB_PATH))
    return _repository
