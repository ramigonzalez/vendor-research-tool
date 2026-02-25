"""Tests for SQLite schema, database initialization, and repository CRUD operations."""

from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path

import aiosqlite
import pytest

from app.models import (
    CapabilityLevel,
    Evidence,
    JobStatus,
    MaturityLevel,
    ResearchJob,
    ScoreResult,
    SourceType,
    VendorRanking,
)
from app.repository import (
    SQLiteResearchRepository,
    create_db_and_tables,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def memory_db() -> aiosqlite.Connection:
    """Create an in-memory database with schema applied, yield connection, then close."""
    await create_db_and_tables(":memory:")
    db = await aiosqlite.connect(":memory:")
    # Re-run creation on this connection since :memory: dbs are per-connection.
    await create_db_and_tables_on_conn(db)
    yield db
    await db.close()


@pytest.fixture
async def repo(tmp_path: Path) -> SQLiteResearchRepository:
    """Create a SQLiteResearchRepository backed by a temp file with schema initialized."""
    db_path = tmp_path / "test_repo.db"
    await create_db_and_tables(db_path)
    return SQLiteResearchRepository(str(db_path))


def _make_job(job_id: str = "job-1", status: JobStatus = JobStatus.pending) -> ResearchJob:
    """Helper to create a ResearchJob for testing."""
    return ResearchJob(
        id=job_id,
        status=status,
        created_at=datetime(2026, 1, 15, 10, 0, 0),
    )


def _make_evidence(claim: str = "Supports X") -> Evidence:
    """Helper to create an Evidence instance for testing."""
    return Evidence(
        claim=claim,
        source_url="https://example.com/docs",
        source_name="Example Docs",
        source_type=SourceType.official_docs,
        content_date="2026-01-01",
        relevance=0.9,
        supports_requirement=True,
    )


def _make_score(score: float = 8.5) -> ScoreResult:
    """Helper to create a ScoreResult for testing."""
    return ScoreResult(
        score=score,
        confidence=0.85,
        capability_level=CapabilityLevel.full,
        maturity=MaturityLevel.ga,
        justification="Strong support found",
        limitations=["Limited to v2+"],
        evidence=[],
    )


# ---------------------------------------------------------------------------
# Helpers for schema tests
# ---------------------------------------------------------------------------


async def create_db_and_tables_on_conn(db: aiosqlite.Connection) -> None:
    """Helper: apply schema directly on an existing connection."""
    from app.repository import (
        _EVIDENCE_JOB_ID_INDEX,
        _EVIDENCE_TABLE,
        _JOBS_TABLE,
        _SCORES_JOB_ID_INDEX,
        _SCORES_TABLE,
    )

    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute(_JOBS_TABLE)
    await db.execute(_EVIDENCE_TABLE)
    await db.execute(_SCORES_TABLE)
    await db.execute(_EVIDENCE_JOB_ID_INDEX)
    await db.execute(_SCORES_JOB_ID_INDEX)
    await db.commit()


async def _get_tables(db: aiosqlite.Connection) -> list[str]:
    """Return sorted list of user table names."""
    cursor = await db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    rows = await cursor.fetchall()
    return [row[0] for row in rows]


async def _get_columns(db: aiosqlite.Connection, table: str) -> list[str]:
    """Return list of column names for a table."""
    cursor = await db.execute(f"PRAGMA table_info({table})")
    rows = await cursor.fetchall()
    return [row[1] for row in rows]


async def _get_indexes(db: aiosqlite.Connection) -> list[str]:
    """Return sorted list of user-created index names."""
    cursor = await db.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    rows = await cursor.fetchall()
    return [row[0] for row in rows]


# ---------------------------------------------------------------------------
# Table creation tests
# ---------------------------------------------------------------------------


async def test_all_three_tables_created(memory_db: aiosqlite.Connection) -> None:
    """All three tables (evidence, jobs, scores) should be created."""
    tables = await _get_tables(memory_db)
    assert tables == ["evidence", "jobs", "scores"]


async def test_jobs_table_columns(memory_db: aiosqlite.Connection) -> None:
    """The jobs table should have the expected columns."""
    columns = await _get_columns(memory_db, "jobs")
    expected = [
        "id",
        "status",
        "created_at",
        "completed_at",
        "progress_pct",
        "progress_message",
        "summary",
        "rankings_json",
    ]
    assert columns == expected


async def test_evidence_table_columns(memory_db: aiosqlite.Connection) -> None:
    """The evidence table should have the expected columns."""
    columns = await _get_columns(memory_db, "evidence")
    expected = [
        "id",
        "job_id",
        "vendor",
        "requirement_id",
        "claim",
        "source_url",
        "source_name",
        "source_type",
        "content_date",
        "relevance",
        "supports_requirement",
        "created_at",
    ]
    assert columns == expected


async def test_scores_table_columns(memory_db: aiosqlite.Connection) -> None:
    """The scores table should have the expected columns."""
    columns = await _get_columns(memory_db, "scores")
    expected = [
        "id",
        "job_id",
        "vendor",
        "requirement_id",
        "score",
        "confidence",
        "capability_level",
        "maturity",
        "justification",
        "limitations_json",
    ]
    assert columns == expected


# ---------------------------------------------------------------------------
# WAL mode test (requires a real file)
# ---------------------------------------------------------------------------


async def test_wal_mode_enabled() -> None:
    """WAL journal mode should be set on a file-backed database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        await create_db_and_tables(db_path)

        async with aiosqlite.connect(str(db_path)) as db:
            cursor = await db.execute("PRAGMA journal_mode")
            row = await cursor.fetchone()
            assert row is not None
            assert row[0] == "wal"


# ---------------------------------------------------------------------------
# Constraint tests
# ---------------------------------------------------------------------------


async def test_scores_unique_constraint(memory_db: aiosqlite.Connection) -> None:
    """The UNIQUE(job_id, vendor, requirement_id) constraint should reject duplicates."""
    # Insert a job first to satisfy the FK reference.
    await memory_db.execute(
        "INSERT INTO jobs (id, status, created_at) VALUES (?, ?, ?)",
        ("job-1", "running", "2026-01-01T00:00:00"),
    )
    await memory_db.execute(
        "INSERT INTO scores (job_id, vendor, requirement_id, score) VALUES (?, ?, ?, ?)",
        ("job-1", "vendorA", "req-1", 0.8),
    )
    await memory_db.commit()

    with pytest.raises(Exception):  # noqa: B017
        await memory_db.execute(
            "INSERT INTO scores (job_id, vendor, requirement_id, score) VALUES (?, ?, ?, ?)",
            ("job-1", "vendorA", "req-1", 0.9),
        )


# ---------------------------------------------------------------------------
# Index tests
# ---------------------------------------------------------------------------


async def test_indexes_exist(memory_db: aiosqlite.Connection) -> None:
    """Both job_id indexes on evidence and scores should exist."""
    indexes = await _get_indexes(memory_db)
    assert "idx_evidence_job_id" in indexes
    assert "idx_scores_job_id" in indexes


# ---------------------------------------------------------------------------
# Idempotency test
# ---------------------------------------------------------------------------


async def test_create_is_idempotent(memory_db: aiosqlite.Connection) -> None:
    """Calling create_db_and_tables twice should not raise."""
    # The fixture already called it once; call the helper again.
    await create_db_and_tables_on_conn(memory_db)
    tables = await _get_tables(memory_db)
    assert tables == ["evidence", "jobs", "scores"]


# ---------------------------------------------------------------------------
# Repository CRUD tests
# ---------------------------------------------------------------------------


async def test_create_job_and_get_job(repo: SQLiteResearchRepository) -> None:
    """create_job followed by get_job should round-trip the data."""
    job = _make_job()
    await repo.create_job(job)

    fetched = await repo.get_job("job-1")
    assert fetched is not None
    assert fetched.id == "job-1"
    assert fetched.status == JobStatus.pending
    assert fetched.progress_pct == 0


async def test_get_job_returns_none_for_missing(repo: SQLiteResearchRepository) -> None:
    """get_job should return None for a non-existent ID."""
    result = await repo.get_job("nonexistent")
    assert result is None


async def test_update_job_status(repo: SQLiteResearchRepository) -> None:
    """update_job_status should change the job's status, progress, and message."""
    await repo.create_job(_make_job())

    await repo.update_job_status("job-1", JobStatus.running, 50, "Halfway done")

    fetched = await repo.get_job("job-1")
    assert fetched is not None
    assert fetched.status == JobStatus.running
    assert fetched.progress_pct == 50
    assert fetched.progress_message == "Halfway done"


async def test_save_evidence_and_get_results(repo: SQLiteResearchRepository) -> None:
    """save_evidence should be retrievable via get_results."""
    await repo.create_job(_make_job())
    evidence = [_make_evidence("Claim A"), _make_evidence("Claim B")]
    await repo.save_evidence("job-1", "vendorX", "req-1", evidence)

    # Also need a score for get_results to include the vendor/req
    await repo.save_score("job-1", "vendorX", "req-1", _make_score())

    results = await repo.get_results("job-1")
    assert results is not None
    assert "vendorX" in results.matrix
    assert "req-1" in results.matrix["vendorX"]
    assert len(results.matrix["vendorX"]["req-1"].evidence) == 2
    assert results.matrix["vendorX"]["req-1"].evidence[0].claim == "Claim A"


async def test_save_score_and_get_results(repo: SQLiteResearchRepository) -> None:
    """save_score should produce a valid matrix entry in get_results."""
    await repo.create_job(_make_job())
    score = _make_score(7.5)
    await repo.save_score("job-1", "vendorA", "req-2", score)

    results = await repo.get_results("job-1")
    assert results is not None
    assert "vendorA" in results.vendors
    assert results.matrix["vendorA"]["req-2"].score == 7.5
    assert results.matrix["vendorA"]["req-2"].confidence == 0.85
    assert results.matrix["vendorA"]["req-2"].capability_level == CapabilityLevel.full
    assert results.matrix["vendorA"]["req-2"].maturity == MaturityLevel.ga
    assert results.matrix["vendorA"]["req-2"].limitations == ["Limited to v2+"]


async def test_save_final_results(repo: SQLiteResearchRepository) -> None:
    """save_final_results should mark the job as completed with summary and rankings."""
    await repo.create_job(_make_job())
    rankings = [
        VendorRanking(vendor="vendorA", overall_score=85.0, rank=1),
        VendorRanking(vendor="vendorB", overall_score=72.0, rank=2),
    ]
    await repo.save_final_results("job-1", "VendorA wins overall", rankings)

    fetched = await repo.get_job("job-1")
    assert fetched is not None
    assert fetched.status == JobStatus.completed
    assert fetched.completed_at is not None

    results = await repo.get_results("job-1")
    assert results is not None
    assert results.summary == "VendorA wins overall"
    assert len(results.rankings) == 2
    assert results.rankings[0].vendor == "vendorA"
    assert results.rankings[0].rank == 1


async def test_get_results_correct_matrix_structure(repo: SQLiteResearchRepository) -> None:
    """get_results should build a proper vendor->req->ScoreResult matrix."""
    await repo.create_job(_make_job())
    await repo.save_score("job-1", "v1", "r1", _make_score(8.0))
    await repo.save_score("job-1", "v1", "r2", _make_score(6.0))
    await repo.save_score("job-1", "v2", "r1", _make_score(7.0))

    results = await repo.get_results("job-1")
    assert results is not None
    assert sorted(results.vendors) == ["v1", "v2"]
    assert len(results.requirements) == 2
    assert results.matrix["v1"]["r1"].score == 8.0
    assert results.matrix["v1"]["r2"].score == 6.0
    assert results.matrix["v2"]["r1"].score == 7.0


async def test_get_results_returns_none_for_missing_job(repo: SQLiteResearchRepository) -> None:
    """get_results should return None for a non-existent job."""
    result = await repo.get_results("nonexistent")
    assert result is None


async def test_list_jobs_respects_limit_and_sort(repo: SQLiteResearchRepository) -> None:
    """list_jobs should return jobs in descending created_at order, respecting limit."""
    job1 = ResearchJob(id="j1", status=JobStatus.pending, created_at=datetime(2026, 1, 1))
    job2 = ResearchJob(id="j2", status=JobStatus.running, created_at=datetime(2026, 1, 2))
    job3 = ResearchJob(id="j3", status=JobStatus.completed, created_at=datetime(2026, 1, 3))

    await repo.create_job(job1)
    await repo.create_job(job2)
    await repo.create_job(job3)

    # All jobs, descending order
    all_jobs = await repo.list_jobs(limit=50)
    assert len(all_jobs) == 3
    assert all_jobs[0].id == "j3"
    assert all_jobs[1].id == "j2"
    assert all_jobs[2].id == "j1"

    # Limited to 2
    limited = await repo.list_jobs(limit=2)
    assert len(limited) == 2
    assert limited[0].id == "j3"
    assert limited[1].id == "j2"


async def test_save_score_replace_on_duplicate(repo: SQLiteResearchRepository) -> None:
    """save_score should replace an existing score for the same vendor/req pair."""
    await repo.create_job(_make_job())
    await repo.save_score("job-1", "vendorA", "req-1", _make_score(5.0))
    await repo.save_score("job-1", "vendorA", "req-1", _make_score(9.0))

    results = await repo.get_results("job-1")
    assert results is not None
    assert results.matrix["vendorA"]["req-1"].score == 9.0
