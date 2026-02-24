"""FastAPI application with static file serving and database initialization."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.repository import create_db_and_tables

STATIC_DIR = Path(__file__).parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize database on startup."""
    await create_db_and_tables()
    yield


app = FastAPI(title="SignalCore Vendor Research Tool", lifespan=lifespan)

# Include API router - import here to avoid circular imports
try:
    from app.api.router import router

    app.include_router(router)
except ImportError:
    pass

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def root() -> FileResponse:
    """Serve the frontend."""
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
