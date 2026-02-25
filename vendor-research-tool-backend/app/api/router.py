"""API router for research job endpoints."""

import asyncio
import json
import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.graph.pipeline import run_pipeline
from app.graph.state import build_initial_state
from app.models import JobStatus, ResearchJob
from app.repository import ResearchRepository, get_repository

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/research/{job_id}")
async def get_research_results(
    job_id: str,
    repo: ResearchRepository = Depends(get_repository),  # noqa: B008
):
    """Retrieve research job status or completed results."""
    logger.debug("GET /api/research/%s", job_id)
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
    logger.debug("GET /api/jobs")
    jobs = await repo.list_jobs(limit=50)
    return [j.model_dump(mode="json") for j in jobs]


@router.post("/api/research")
async def run_research(
    repo: ResearchRepository = Depends(get_repository),  # noqa: B008
):
    """Launch research pipeline and stream progress via SSE."""
    job_id = str(uuid.uuid4())
    job = ResearchJob(id=job_id, status=JobStatus.running, created_at=datetime.now())
    await repo.create_job(job)
    logger.info("Research started job_id=%s", job_id)

    queue: asyncio.Queue = asyncio.Queue()  # type: ignore[type-arg]

    async def event_generator():
        yield f"data: {json.dumps({'type': 'started', 'job_id': job_id})}\n\n"

        state = build_initial_state(job_id, queue)
        pipeline_task = asyncio.create_task(run_pipeline(state, repo))

        while not pipeline_task.done() or not queue.empty():
            try:
                event = await asyncio.wait_for(queue.get(), timeout=0.5)
                yield f"data: {json.dumps(event)}\n\n"
            except TimeoutError:
                continue

        if pipeline_task.exception():
            err = str(pipeline_task.exception())
            logger.error("Research failed job_id=%s error=%s", job_id, err)
            yield f"data: {json.dumps({'type': 'error', 'message': err})}\n\n"
            await repo.update_job_status(job_id, JobStatus.failed, 100, err)
        else:
            logger.info("Research completed job_id=%s", job_id)
            results = await repo.get_results(job_id)
            if results:
                yield f"data: {json.dumps({'type': 'completed', 'results': results.model_dump(mode='json')})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'completed', 'results': {}})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
