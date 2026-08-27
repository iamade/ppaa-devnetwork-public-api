"""Deterministic docker compose port assertions (PP-83 lesson applied to PP-79).

Asserts the canonical Mac-facing staging targets:
- backend  127.0.0.1:8005
- frontend 127.0.0.1:5174
- postgres 127.0.0.1:25432 (never bare 5432 on the host)
- redis    127.0.0.1:26379 (never bare 6379 on the host)
"""

import json
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent

EXPECTED_HOST_PORTS = {"app": "8005", "web": "5174", "postgres": "25432", "redis": "26379"}
EXPECTED_TARGETS = {"app": "8005", "web": "80", "postgres": "5432", "redis": "6379"}


def compose_config() -> dict[str, object]:
    """Run `docker compose config --format json` and return the parsed config."""
    proc = subprocess.run(
        ["docker", "compose", "-f", str(REPO / "docker-compose.yml"), "config", "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        pytest.skip(f"docker compose unavailable: {proc.stderr.strip()[:200]}")
    return json.loads(proc.stdout)  # type: ignore[no-any-return]


def test_all_ports_bound_to_loopback() -> None:
    config = compose_config()
    services = config["services"]
    assert isinstance(services, dict)
    for name, service in services.items():
        for entry in service.get("ports", []):
            host_ip = str(entry.get("host_ip", ""))
            assert host_ip == "127.0.0.1", f"{name} binds {host_ip!r}, expected 127.0.0.1"


def test_canonical_host_ports_and_targets() -> None:
    config = compose_config()
    services = config["services"]
    assert isinstance(services, dict)
    for service_name, host_port in EXPECTED_HOST_PORTS.items():
        ports = services[service_name]["ports"]
        assert len(ports) == 1, f"{service_name} should publish exactly one port"
        entry = ports[0]
        assert str(entry["published"]) == host_port, f"{service_name} host port wrong"
        assert str(entry["target"]) == EXPECTED_TARGETS[service_name], (
            f"{service_name} container target wrong"
        )


def test_no_base_5432_6379_host_mappings() -> None:
    """The staging stack must never retain base 5432/6379 host mappings (PP-83)."""
    config = compose_config()
    services = config["services"]
    assert isinstance(services, dict)
    for name, service in services.items():
        for entry in service.get("ports", []):
            published_host = str(entry["published"])
            assert published_host not in {"5432", "6379"}, (
                f"{name} retains base host port {published_host}"
            )


def test_app_is_local_build_and_data_deps_pinned() -> None:
    config = compose_config()
    services = config["services"]
    assert isinstance(services, dict)
    assert services["app"].get("build") is not None, "app must build from repo"
    assert "postgres:16" in str(services["postgres"]["image"])
    assert "redis:7" in str(services["redis"]["image"])
