"""Deterministic documentation & demo-asset tests (PP-63).

These keep the public-facing submission surface honest: every guide the
checklist promises must exist, the demo script must stay valid bash, every
agent slug must appear in the docs, and every documented route must be a real
application route.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from fastapi.routing import APIRoute

from ppaa_showcase.main import app

REPO = Path(__file__).resolve().parent.parent
REQUIRED_DOCS = (
    "docs/SETUP.md",
    "docs/API.md",
    "docs/ARCHITECTURE.md",
    "docs/DEMO.md",
    "docs/SUBMISSION.md",
)


def _read(relative: str) -> str:
    return (REPO / relative).read_text(encoding="utf-8")


def test_required_docs_exist() -> None:
    for relative in REQUIRED_DOCS:
        path = REPO / relative
        assert path.is_file(), f"missing submission doc: {relative}"
        assert path.stat().st_size > 200, f"doc too small to be a guide: {relative}"


def test_readme_links_docs_and_demo() -> None:
    readme = _read("README.md")
    for relative in REQUIRED_DOCS:
        assert relative in readme, f"README must link {relative}"
    assert "scripts/demo.sh" in readme, "README must mention the demo script"


def test_demo_script_is_valid_bash() -> None:
    result = subprocess.run(
        ["bash", "-n", str(REPO / "scripts/demo.sh")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"scripts/demo.sh failed bash -n: {result.stderr}"


def test_demo_script_is_executable() -> None:
    assert (REPO / "scripts/demo.sh").stat().st_mode & 0o111, "demo.sh must be executable"


def test_every_agent_slug_documented() -> None:
    catalog = json.loads((REPO / "data/agents.json").read_text(encoding="utf-8"))
    api_doc = _read("docs/API.md")
    for agent in catalog["agents"]:
        assert agent["slug"] in api_doc, f"docs/API.md missing slug: {agent['slug']}"


def test_documented_api_routes_exist() -> None:
    api_doc = _read("docs/API.md")
    real_paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    for documented in ("/health", "/api/agents", "/api/agents/{slug}"):
        assert documented in api_doc, f"docs/API.md missing route {documented}"
        assert documented in real_paths, f"app no longer serves documented route {documented}"


def test_setup_doc_documents_port_rule_and_gates() -> None:
    setup = _read("docs/SETUP.md")
    assert "25432" in setup and "26379" in setup, "SETUP must list published pg/redis ports"
    assert "5432" in setup and "6379" in setup, "SETUP must explain the base-port avoidance rule"
    for gate in ("ruff", "mypy", "pytest"):
        assert gate in setup, f"SETUP must list the {gate} quality gate"
