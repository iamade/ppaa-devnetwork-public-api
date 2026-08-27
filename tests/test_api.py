"""API tests using FastAPI TestClient with monkeypatched health checks."""

import pytest
from fastapi.testclient import TestClient

from ppaa_showcase import main
from ppaa_showcase.catalog import load_catalog


@pytest.fixture()
def client() -> TestClient:
    return TestClient(main.app)


def test_health_ok(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "check_postgres", lambda: (True, ""))
    monkeypatch.setattr(main, "check_redis", lambda: (True, ""))
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "healthy"
    assert body["checks"] == {"postgres": True, "redis": True}
    assert body.get("errors", {}) == {}


def test_health_reports_failures(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "check_postgres", lambda: (False, "OperationalError: down"))
    monkeypatch.setattr(main, "check_redis", lambda: (True, ""))
    res = client.get("/health")
    assert res.status_code == 503
    detail = res.json()["detail"]
    assert detail["checks"]["postgres"] is False
    assert detail["errors"]["postgres"] == "OperationalError: down"


def test_list_agents_shape(client: TestClient) -> None:
    res = client.get("/api/agents")
    assert res.status_code == 200
    body = res.json()
    assert body["count"] == len(body["agents"]) >= 10
    first = body["agents"][0]
    for field in ("slug", "name", "role", "description", "channel"):
        assert field in first


def test_agent_detail_and_404(client: TestClient) -> None:
    slug = load_catalog().agents[0].slug
    res = client.get(f"/api/agents/{slug}")
    assert res.status_code == 200
    assert res.json()["slug"] == slug
    assert client.get("/api/agents/does-not-exist").status_code == 404


def test_root_serves_frontend(client: TestClient) -> None:
    res = client.get("/")
    assert res.status_code == 200
    assert "PPAA Agent Showcase" in res.text
