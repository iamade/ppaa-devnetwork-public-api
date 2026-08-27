"""FastAPI application for the PPAA Agent Showcase catalog (PP-79).

Sponsor endpoints (PP-80) expose the multi-sponsor integration adapter layer.
"""

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .catalog import Agent, get_agent, load_catalog
from .config import settings
from .health import check_postgres, check_redis
from .sponsors import (
    SUPPORTED_INTEGRATION_TYPES,
    adapter_errors,
    agents_with_sponsors,
    get_sponsor,
    load_sponsors,
    sponsor_attributions,
)


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
    """Return the full agent catalog with sponsor attribution (PP-80)."""
    catalog = load_catalog()
    attributions = sponsor_attributions(catalog=catalog)
    return {
        "count": len(catalog.agents),
        "updated": catalog.updated,
        "agents": agents_with_sponsors(catalog.agents, attributions),
    }


@app.get("/api/agents/{slug}")
def agent_detail(slug: str) -> dict[str, object]:
    """Return one agent entry by slug, with sponsor attribution (PP-80)."""
    agent = get_agent(slug)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"agent not found: {slug}")
    payload = agents_with_sponsors([agent])
    return payload[0]


@app.get("/api/sponsors")
def list_sponsors() -> dict[str, object]:
    """List the multi-sponsor registry with integration adapter metadata (PP-80)."""
    registry = load_sponsors()
    catalog = load_catalog()
    errors = adapter_errors(registry, catalog)
    if errors:
        raise HTTPException(
            status_code=500,
            detail={"message": "sponsor registry invalid", "errors": errors},
        )
    return {
        "count": len(registry.sponsors),
        "updated": registry.updated,
        "integration_types": list(SUPPORTED_INTEGRATION_TYPES),
        "sponsors": [sponsor.model_dump() for sponsor in registry.sponsors],
    }


@app.get("/api/sponsors/{sponsor_id}")
def sponsor_detail(sponsor_id: str) -> dict[str, object]:
    """Return one sponsor with its integration contract and attributed agents (PP-80)."""
    sponsor = get_sponsor(sponsor_id)
    if sponsor is None:
        raise HTTPException(status_code=404, detail=f"sponsor not found: {sponsor_id}")
    catalog = load_catalog()
    errors = adapter_errors(load_sponsors(), catalog)
    if errors:
        raise HTTPException(
            status_code=500,
            detail={"message": "sponsor registry invalid", "errors": errors},
        )
    by_slug: dict[str, Agent] = {agent.slug: agent for agent in catalog.agents}
    attributed = [by_slug[slug].model_dump() for slug in dict.fromkeys(sponsor.agent_slugs)]
    return {**sponsor.model_dump(), "agents": attributed}


# Serve the static catalog frontend from the same origin when mounted
# alongside the API (single-container mode); nginx serves it separately on 5174.
if FRONTEND_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(FRONTEND_DIR / "index.html")
