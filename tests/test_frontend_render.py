"""Frontend render smoke tests for the PP-79 catalog (PP-79/PP-63 fix, Aug 27 2026).

Executes the real frontend/app.js in Node against a minimal DOM shim fed with the
real /api/agents payload, then asserts #grid is non-empty and the #msg error
banner stays hidden — the exact regression QA caught at ffa387b/d95f135
(chip(null, ...) -> TypeError "Cannot read properties of null (reading
'startsWith')" -> catch -> banner + empty grid).
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ppaa_showcase import main

REPO = Path(__file__).resolve().parent.parent
HARNESS = REPO / "tests" / "render_smoke.mjs"
APP_JS = REPO / "frontend" / "app.js"

node = shutil.which("node")
pytestmark = pytest.mark.skipif(node is None, reason="node runtime not available")


@pytest.fixture()
def client() -> TestClient:
    return TestClient(main.app)


@pytest.fixture()
def agents_fixture(client: TestClient, tmp_path: Path) -> Path:
    """Dump the real packaged /api/agents payload (deterministic at this SHA)."""
    res = client.get("/api/agents")
    assert res.status_code == 200
    fixture = tmp_path / "agents_fixture.json"
    fixture.write_text(json.dumps(res.json()))
    return fixture


def run_harness(fixture: Path, frontend_dir: Path | None = None) -> dict:
    cmd = [node, str(HARNESS), str(fixture)]
    if frontend_dir is not None:
        cmd += ["--frontend", str(frontend_dir)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    out = proc.stdout.strip() or proc.stderr.strip()
    payload = {}
    try:
        payload = json.loads(out.splitlines()[-1])
    except (ValueError, IndexError):
        payload = {"raw": out}
    payload["returncode"] = proc.returncode
    return payload


def test_render_smoke_grid_nonempty_banner_hidden(agents_fixture: Path) -> None:
    """Real app.js + real payload => all cards render, banner stays hidden."""
    result = run_harness(agents_fixture)
    assert result["returncode"] == 0, result
    assert result["gridChildren"] == result["count"], result
    assert result["gridChildren"] >= 1, result
    assert result["bannerHidden"] is True, result


def test_render_smoke_catches_null_href_regression(agents_fixture: Path, tmp_path: Path) -> None:
    """Negative control: reverting the null-safe guard must FAIL the harness.

    Proves the smoke test executes the actual defect path (chip(null, ...)) and
    is not a synthetic substitute for coverage.
    """
    src = APP_JS.read_text()
    assert "href != null" in src, "null-safe guard missing from chip()"
    mutated = src.replace("href != null && href.startsWith", "href.startsWith")
    assert mutated != src
    fdir = tmp_path / "frontend"
    fdir.mkdir()
    (fdir / "app.js").write_text(mutated)
    result = run_harness(agents_fixture, frontend_dir=fdir)
    assert result["returncode"] != 0, result
    banner = str(result.get("bannerText", "")) + str(result.get("raw", ""))
    assert "startsWith" in banner, result
    assert result.get("gridChildren") == 0, result


def test_chip_null_safe_guard_in_source() -> None:
    """chip() must null-guard href before .startsWith() (jira_refs/evidence_links
    render with chip(null, ...))."""
    src = APP_JS.read_text()
    assert re.search(r"href\s*!=\s*null\s*&&\s*href\.startsWith", src), (
        "chip() must guard href against null before .startsWith()"
    )


def test_frontend_page_has_grid_and_banner(client: TestClient) -> None:
    """Root page must serve the catalog HTML with #grid and hidden #msg banner."""
    res = client.get("/")
    assert res.status_code == 200
    assert 'id="grid"' in res.text
    assert re.search(r'<p id="msg"[^>]*\bhidden\b', res.text), (
        "#msg banner must start hidden in served HTML"
    )


def test_agents_payload_shape_exercises_chip_paths(client: TestClient) -> None:
    """Every agent payload must include the fields card() renders — including the
    chip(null, ...) fields that caused the defect."""
    res = client.get("/api/agents")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == len(data["agents"]) >= 10
    for agent in data["agents"]:
        for field in ("demo_routes", "jira_refs", "evidence_links"):
            assert field in agent, f"agent {agent.get('name')} missing {field}"
