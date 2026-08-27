"""Agent catalog model and loader."""

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

_REPO_CATALOG = Path(__file__).resolve().parent.parent.parent / "data" / "agents.json"
_CONTAINER_CATALOG = Path("/srv/data/agents.json")


def _default_catalog_path() -> Path:
    """Resolve the catalog JSON: env override, repo layout, then container layout."""
    env_path = os.environ.get("CATALOG_PATH", "")
    if env_path:
        return Path(env_path)
    if _REPO_CATALOG.is_file():
        return _REPO_CATALOG
    return _CONTAINER_CATALOG


class Agent(BaseModel):
    """A single PPAA fleet agent entry in the public showcase catalog."""

    slug: str
    name: str
    role: str
    description: str
    channel: str
    jira_refs: list[str] = Field(default_factory=list)
    demo_routes: list[str] = Field(default_factory=list)
    evidence_links: list[str] = Field(default_factory=list)


class Catalog(BaseModel):
    """The full catalog payload served by the API."""

    updated: str
    source: str
    agents: list[Agent]


@lru_cache(maxsize=1)
def load_catalog(path: str | None = None) -> Catalog:
    """Load and validate the agent catalog from JSON.

    Args:
        path: Optional explicit JSON path (defaults to the resolved catalog path).

    Returns:
        Validated Catalog.

    Raises:
        FileNotFoundError: If the catalog file is missing.
        ValueError: If the catalog JSON does not match the schema.
    """
    catalog_path = Path(path) if path else _default_catalog_path()
    raw: dict[str, Any] = json.loads(catalog_path.read_text(encoding="utf-8"))
    return Catalog.model_validate(raw)


def get_agent(slug: str, path: str | None = None) -> Agent | None:
    """Return the agent with the given slug, or None."""
    catalog = load_catalog(path)
    for agent in catalog.agents:
        if agent.slug == slug:
            return agent
    return None
