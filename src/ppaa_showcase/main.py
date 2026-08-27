"""FastAPI application for the PPAA Agent Showcase catalog (PP-79)."""

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .catalog import get_agent, load_catalog
from .config import settings
from .health import check_postgres, check_redis


def _frontend_dir() -> Path:
    """Resolve the static frontend dir: env override, repo layout, container layout."""
    env_dir = os.environ.get("FRONTEND_DIR", "")
    if env_dir:
        return Path(env_dir)
    repo_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
    if repo_dir.is_dir():
        return repo_dir
    return Path("/srv/frontend")


FRONTEND_DIR = _frontend_dir()

app = FastAPI(title="PPAA Agent Showcase", version=__version__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, object]:
    """Liveness + dependency readiness. 200 when Postgres and Redis are reachable."""
    pg_ok, pg_err = check_postgres()
    rd_ok, rd_err = check_redis()
    checks = {"postgres": pg_ok, "redis": rd_ok}
    errors: dict[str, str] = {}
    if not pg_ok:
        errors["postgres"] = pg_err
    if not rd_ok:
        errors["redis"] = rd_err
    body: dict[str, object] = {"status": "healthy" if not errors else "unhealthy", "checks": checks}
    if errors:
        body["errors"] = errors
    if errors:
        raise HTTPException(status_code=503, detail=body)
    return body


@app.get("/api/agents")
def list_agents() -> dict[str, object]:
    """Return the full agent catalog."""
    catalog = load_catalog()
    return {
        "count": len(catalog.agents),
        "updated": catalog.updated,
        "agents": [agent.model_dump() for agent in catalog.agents],
    }


@app.get("/api/agents/{slug}")
def agent_detail(slug: str) -> dict[str, object]:
    """Return one agent entry by slug."""
    agent = get_agent(slug)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"agent not found: {slug}")
    return agent.model_dump()


# Serve the static catalog frontend from the same origin when mounted
# alongside the API (single-container mode); nginx serves it separately on 5174.
if FRONTEND_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(FRONTEND_DIR / "index.html")
