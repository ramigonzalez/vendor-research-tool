"""API router for research job endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from app.models import JobStatus
from app.repository import ResearchRepository, get_repository

router = APIRouter()


@router.get("/api/research/{job_id}")
async def get_research_results(
    job_id: str,
    repo: ResearchRepository = Depends(get_repository),  # noqa: B008
):
    """Retrieve research job status or completed results."""
    job = await repo.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status == JobStatus.running:
        return {"status": "running", "progress_pct": job.progress_pct}

    if job.status == JobStatus.failed:
        return {"status": "failed", "error": job.progress_message}

    if job.status == JobStatus.pending:
        return {"status": "pending", "progress_pct": 0}

    # completed
    results = await repo.get_results(job_id)
    if results is None:
        raise HTTPException(status_code=500, detail="Results not found for completed job")
    return results.model_dump(mode="json")


@router.get("/api/jobs")
async def list_jobs(
    repo: ResearchRepository = Depends(get_repository),  # noqa: B008
):
    """List previous research jobs, most recent first."""
    jobs = await repo.list_jobs(limit=50)
    return [j.model_dump(mode="json") for j in jobs]
