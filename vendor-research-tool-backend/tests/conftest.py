"""Pytest fixtures for the Vendor Research Tool test suite."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.models import (
    Evidence,
    JobStatus,
    Requirement,
    ResearchJob,
    ResearchResults,
    ScoreResult,
    VendorRanking,
)
from app.repository import ResearchRepository


class MockResearchRepository(ResearchRepository):
    """In-memory mock repository implementing the ResearchRepository ABC.

    Stores all data in plain dicts for fast, isolated test execution.
    """

    def __init__(self) -> None:
        self._jobs: dict[str, ResearchJob] = {}
        self._evidence: dict[str, list[tuple[str, str, Evidence]]] = {}  # job_id -> [(vendor, req_id, Evidence)]
        self._scores: dict[str, list[tuple[str, str, ScoreResult]]] = {}  # job_id -> [(vendor, req_id, ScoreResult)]
        self._summaries: dict[str, str] = {}
        self._rankings: dict[str, list[VendorRanking]] = {}
        self._audit_events: dict[str, list[dict]] = {}  # job_id -> [audit_event]

    async def create_job(self, job: ResearchJob) -> None:
        self._jobs[job.id] = job.model_copy()

    async def update_job_status(self, job_id: str, status: JobStatus, progress_pct: int, progress_message: str) -> None:
        if job_id in self._jobs:
            job = self._jobs[job_id]
            self._jobs[job_id] = job.model_copy(
                update={"status": status, "progress_pct": progress_pct, "progress_message": progress_message}
            )

    async def save_evidence(self, job_id: str, vendor: str, req_id: str, evidence: list[Evidence]) -> None:
        entries = self._evidence.setdefault(job_id, [])
        for ev in evidence:
            entries.append((vendor, req_id, ev))

    async def save_score(self, job_id: str, vendor: str, req_id: str, score_result: ScoreResult) -> None:
        entries = self._scores.setdefault(job_id, [])
        # Replace existing score for same vendor/req_id
        entries[:] = [(v, r, s) for v, r, s in entries if not (v == vendor and r == req_id)]
        entries.append((vendor, req_id, score_result))

    async def get_job(self, job_id: str) -> ResearchJob | None:
        job = self._jobs.get(job_id)
        return job.model_copy() if job else None

    async def get_results(self, job_id: str) -> ResearchResults | None:
        if job_id not in self._jobs:
            return None

        score_entries = self._scores.get(job_id, [])
        evidence_entries = self._evidence.get(job_id, [])

        # Build evidence lookup
        ev_map: dict[tuple[str, str], list[Evidence]] = {}
        for vendor, req_id, ev in evidence_entries:
            ev_map.setdefault((vendor, req_id), []).append(ev)

        # Build matrix
        vendors_set: set[str] = set()
        req_ids_set: set[str] = set()
        matrix: dict[str, dict[str, ScoreResult]] = {}
        for vendor, req_id, sr in score_entries:
            vendors_set.add(vendor)
            req_ids_set.add(req_id)
            ev_list = ev_map.get((vendor, req_id), [])
            sr_with_ev = sr.model_copy(update={"evidence": ev_list})
            matrix.setdefault(vendor, {})[req_id] = sr_with_ev

        vendors = sorted(vendors_set)
        requirements = [Requirement(id=rid, description=rid, priority="medium") for rid in sorted(req_ids_set)]

        return ResearchResults(
            vendors=vendors,
            requirements=requirements,
            matrix=matrix,
            rankings=self._rankings.get(job_id, []),
            summary=self._summaries.get(job_id, ""),
        )

    async def list_jobs(self, limit: int = 50) -> list[ResearchJob]:
        jobs = sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)
        return [j.model_copy() for j in jobs[:limit]]

    async def save_final_results(self, job_id: str, summary: str, rankings: list[VendorRanking]) -> None:
        self._summaries[job_id] = summary
        self._rankings[job_id] = rankings
        if job_id in self._jobs:
            job = self._jobs[job_id]
            self._jobs[job_id] = job.model_copy(
                update={
                    "status": JobStatus.completed,
                    "completed_at": datetime.now(UTC),
                }
            )

    async def save_audit_event(self, job_id: str, event_type: str, payload: dict) -> None:
        events = self._audit_events.setdefault(job_id, [])
        events.append({
            "event_type": event_type,
            "payload": payload,
            "created_at": datetime.now(UTC).isoformat(),
        })

    async def get_audit_events(self, job_id: str) -> list[dict]:
        return list(self._audit_events.get(job_id, []))


@pytest.fixture
def mock_repository() -> MockResearchRepository:
    """Provide a fresh mock repository for each test."""
    return MockResearchRepository()
