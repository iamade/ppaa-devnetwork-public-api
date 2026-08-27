"""Catalog data integrity tests."""

import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "agents.json"

REQUIRED_FIELDS = [
    "slug",
    "name",
    "role",
    "description",
    "channel",
    "jira_refs",
    "demo_routes",
    "evidence_links",
]

EXPECTED_AGENTS = {
    "ppaa-coordinator",
    "ppaa-director",
    "ppaa-builder",
    "ppaa-qa",
    "ppaa-scribe",
    "mavis",
    "amara-vps-ops",
    "akande-vps-main",
    "codex-mac-retest",
    "tobi",
}


def _catalog() -> dict[str, object]:
    return json.loads(DATA.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def test_file_loads_and_top_level_fields() -> None:
    catalog = _catalog()
    assert catalog["updated"]
    assert catalog["source"]
    assert isinstance(catalog["agents"], list)


def test_all_required_fields_present() -> None:
    catalog = _catalog()
    for agent in catalog["agents"]:
        for field in REQUIRED_FIELDS:
            assert field in agent, f"{agent.get('slug')} missing {field}"


def test_slugs_unique_and_expected_roster() -> None:
    catalog = _catalog()
    slugs = [a["slug"] for a in catalog["agents"]]
    assert len(slugs) == len(set(slugs)), "duplicate slugs"
    assert EXPECTED_AGENTS.issubset(set(slugs))


def test_jira_refs_and_routes_wellformed() -> None:
    catalog = _catalog()
    for agent in catalog["agents"]:
        for ref in agent["jira_refs"]:
            assert ref.startswith("PP-"), f"bad Jira ref {ref}"
        for route in agent["demo_routes"]:
            assert route.startswith("/"), f"demo route must be relative: {route}"
        assert len(agent["description"]) > 40, "description too thin"
