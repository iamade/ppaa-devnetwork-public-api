"""Multi-sponsor integration adapter tests (PP-80).

Covers the adapter contract, registry integrity, sponsor attribution, and the
/api/sponsors endpoints — including negative controls (unknown integration
type, dangling agent slug, duplicate sponsor id all rejected).
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ppaa_showcase import main
from ppaa_showcase.catalog import load_catalog
from ppaa_showcase.sponsors import (
    SUPPORTED_INTEGRATION_TYPES,
    Sponsor,
    SponsorIntegration,
    SponsorRegistry,
    UnknownIntegrationTypeError,
    adapter_errors,
    build_adapter,
    load_sponsors,
    sponsor_attributions,
)

REPO = Path(__file__).resolve().parent.parent
SPONSORS_JSON = REPO / "data" / "sponsors.json"


@pytest.fixture()
def client() -> TestClient:
    return TestClient(main.app)


@pytest.fixture()
def registry() -> SponsorRegistry:
    return load_sponsors()


# --- adapter layer ---------------------------------------------------------


def test_supported_integration_types_stable() -> None:
    assert SUPPORTED_INTEGRATION_TYPES == ("api_key", "catalog_feed", "webhook")


@pytest.mark.parametrize(
    ("integration_type", "adapter_name"),
    [
        ("catalog_feed", "CatalogFeedAdapter"),
        ("webhook", "WebhookAdapter"),
        ("api_key", "APIKeyAdapter"),
    ],
)
def test_registry_uses_every_adapter_type(
    registry: SponsorRegistry, integration_type: str, adapter_name: str
) -> None:
    types = {s.integration.type for s in registry.sponsors}
    assert integration_type in types, f"registry must exercise the {adapter_name}"


def test_build_adapter_rejects_unknown_type() -> None:
    sponsor = Sponsor(
        sponsor_id="bad",
        name="Bad",
        tier="example",
        summary="s",
        challenge_title="c",
        challenge_category="cat",
        integration=SponsorIntegration(type="carrier_pigeon", config_keys=["roost"]),
        agent_slugs=["ppaa-builder"],
    )
    with pytest.raises(UnknownIntegrationTypeError, match="carrier_pigeon"):
        build_adapter(sponsor)


def test_adapter_contract_mismatch_detected() -> None:
    """A webhook sponsor declaring feed keys violates its adapter contract."""
    sponsor = Sponsor(
        sponsor_id="miswired",
        name="Miswired",
        tier="example",
        summary="s",
        challenge_title="c",
        challenge_category="cat",
        integration=SponsorIntegration(type="webhook", config_keys=["feed_url"]),
        agent_slugs=["ppaa-builder"],
    )
    errors = adapter_errors(
        SponsorRegistry(updated="2026-08-27T00:00:00Z", source="t", sponsors=[sponsor]),
        load_catalog(),
    )
    joined = " | ".join(errors)
    assert "do not match the webhook contract" in joined


def test_registry_integrity_against_catalog(registry: SponsorRegistry) -> None:
    assert adapter_errors(registry, load_catalog()) == []


def test_dangling_agent_slug_reported(registry: SponsorRegistry) -> None:
    broken = copy.deepcopy(registry)
    broken.sponsors[0].agent_slugs.append("no-such-agent")
    errors = adapter_errors(broken, load_catalog())
    assert any("unknown agent slug" in e for e in errors)


def test_duplicate_sponsor_id_reported(registry: SponsorRegistry) -> None:
    dup = copy.deepcopy(registry)
    clone = copy.deepcopy(registry.sponsors[0])
    dup.sponsors.append(clone)
    errors = adapter_errors(dup, load_catalog())
    assert any("duplicate sponsor_id" in e for e in errors)


def test_sponsor_attributions_map(registry: SponsorRegistry) -> None:
    attributions = sponsor_attributions(registry, load_catalog())
    assert attributions["ppaa-builder"] == [
        "devnetwork-platform",
        "sample-webhook-sponsor",
    ]
    # every attributed slug is a real catalog agent
    catalog_slugs = {a.slug for a in load_catalog().agents}
    assert set(attributions) <= catalog_slugs


# --- API endpoints ---------------------------------------------------------


def test_list_sponsors_shape(client: TestClient) -> None:
    res = client.get("/api/sponsors")
    assert res.status_code == 200
    body = res.json()
    assert body["count"] == len(body["sponsors"]) >= 3
    assert sorted(body["integration_types"]) == ["api_key", "catalog_feed", "webhook"]
    first = body["sponsors"][0]
    for field in ("sponsor_id", "name", "tier", "integration", "agent_slugs"):
        assert field in first


def test_sponsor_detail_with_agents(client: TestClient) -> None:
    res = client.get("/api/sponsors/devnetwork-platform")
    assert res.status_code == 200
    body = res.json()
    assert body["sponsor_id"] == "devnetwork-platform"
    assert body["integration"]["type"] == "catalog_feed"
    assert len(body["agents"]) == len(body["agent_slugs"])
    assert {a["slug"] for a in body["agents"]} >= {"ppaa-builder"}


def test_sponsor_detail_404(client: TestClient) -> None:
    res = client.get("/api/sponsors/does-not-exist")
    assert res.status_code == 404


def test_agents_payload_carries_sponsor_attribution(client: TestClient) -> None:
    res = client.get("/api/agents")
    assert res.status_code == 200
    agents = res.json()["agents"]
    by_slug = {a["slug"]: a for a in agents}
    assert by_slug["ppaa-builder"]["sponsors"] == [
        "devnetwork-platform",
        "sample-webhook-sponsor",
    ]
    assert by_slug["amara-vps-ops"]["sponsors"] == []
    detail = client.get("/api/agents/ppaa-builder")
    assert detail.json()["sponsors"] == ["devnetwork-platform", "sample-webhook-sponsor"]


# --- data file -------------------------------------------------------------


def test_sponsors_json_is_valid_and_deterministic() -> None:
    raw = json.loads(SPONSORS_JSON.read_text(encoding="utf-8"))
    assert raw["updated"].endswith("Z")
    assert len(raw["sponsors"]) >= 3
    # examples are explicitly labelled so judges never mistake them for real sponsors
    for sponsor in raw["sponsors"]:
        if sponsor["sponsor_id"].startswith("sample-"):
            assert sponsor["example"] is True
