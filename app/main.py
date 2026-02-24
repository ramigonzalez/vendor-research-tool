"""Minimal FastAPI application shell."""

from fastapi import FastAPI

app = FastAPI(title="SignalCore Vendor Research Tool")


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
