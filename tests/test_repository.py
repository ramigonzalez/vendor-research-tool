"""Tests for SQLite schema and database initialization."""

from __future__ import annotations

import tempfile
from pathlib import Path

import aiosqlite
import pytest

from app.repository import create_db_and_tables


@pytest.fixture
async def memory_db() -> aiosqlite.Connection:
    """Create an in-memory database with schema applied, yield connection, then close."""
    await create_db_and_tables(":memory:")
    db = await aiosqlite.connect(":memory:")
    # Re-run creation on this connection since :memory: dbs are per-connection.
    await create_db_and_tables_on_conn(db)
    yield db
    await db.close()


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
