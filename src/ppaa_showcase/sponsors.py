"""Multi-sponsor integration adapters (PP-80).

Each sponsor in ``data/sponsors.json`` declares an integration descriptor
(type + required config keys). The adapter classes in this module normalize
those descriptors behind one interface so the showcase API can:

1. validate every sponsor's integration contract at load time,
2. attribute catalog agents to the sponsors they serve, and
3. expose sponsor-scoped endpoints without sponsor-specific code paths.

Adding a sponsor = adding a ``data/sponsors.json`` entry; adding a new
integration *type* = subclassing :class:`SponsorAdapter` once. No sponsor
credentials are ever stored here — adapters describe shapes, not secrets.
"""

import json
import os
from abc import ABC
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

from .catalog import Agent, Catalog, load_catalog

_REPO_SPONSORS = Path(__file__).resolve().parent.parent.parent / "data" / "sponsors.json"
_CONTAINER_SPONSORS = Path("/srv/data/sponsors.json")


def _default_sponsors_path() -> Path:
    """Resolve the sponsor registry JSON: env override, repo layout, container layout."""
    env_path = os.environ.get("SPONSORS_PATH", "")
    if env_path:
        return Path(env_path)
    if _REPO_SPONSORS.is_file():
        return _REPO_SPONSORS
    return _CONTAINER_SPONSORS


class SponsorIntegration(BaseModel):
    """The integration contract a sponsor declares (type + required config keys)."""

    type: str
    config_keys: list[str] = Field(default_factory=list)

    @field_validator("type")
    @classmethod
    def _type_is_slug(cls, value: str) -> str:
        if not value or value.lower() != value or " " in value:
            raise ValueError(f"integration type must be a lowercase slug: {value!r}")
        return value

    @field_validator("config_keys")
    @classmethod
    def _config_keys_nonempty(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("integration must declare at least one config key")
        return value


class Sponsor(BaseModel):
    """One sponsor entry in the multi-sponsor registry."""

    sponsor_id: str
    name: str
    tier: str
    summary: str
    challenge_title: str
    challenge_category: str
    integration: SponsorIntegration
    agent_slugs: list[str] = Field(default_factory=list)
    example: bool = False

    @field_validator("sponsor_id")
    @classmethod
    def _id_is_slug(cls, value: str) -> str:
        if not value or value.lower() != value or " " in value:
            raise ValueError(f"sponsor_id must be a lowercase slug: {value!r}")
        return value


class SponsorRegistry(BaseModel):
    """The full sponsor payload served by the API."""

    updated: str
    source: str
    sponsors: list[Sponsor]


class SponsorAdapter(ABC):
    """Base class for sponsor integration adapters.

    An adapter wraps one :class:`Sponsor` and exposes the normalized surface
    (required config keys, agent attribution) that the API and tests rely on.
    """

    integration_type: str
    #: Config keys whose *values* are supplied per-deployment (never stored here).
    default_config_keys: tuple[str, ...] = ()

    def __init__(self, sponsor: Sponsor) -> None:
        self.sponsor = sponsor

    def required_config_keys(self) -> tuple[str, ...]:
        """Config keys this sponsor's integration requires (from the registry)."""
        return tuple(self.sponsor.integration.config_keys)

    def validate_contract(self) -> list[str]:
        """Return a list of contract violations (empty list = valid)."""
        errors: list[str] = []
        if self.sponsor.integration.type != self.integration_type:
            errors.append(
                f"{self.sponsor.sponsor_id}: adapter {self.integration_type!r} cannot serve "
                f"integration type {self.sponsor.integration.type!r}"
            )
        if not self.sponsor.agent_slugs:
            errors.append(f"{self.sponsor.sponsor_id}: must attribute at least one agent")
        return errors

    def attributed_agent_slugs(self) -> list[str]:
        """Agent slugs this sponsor integrates with, deduplicated and ordered."""
        return list(dict.fromkeys(self.sponsor.agent_slugs))


class CatalogFeedAdapter(SponsorAdapter):
    """Pull-based adapter: the showcase consumes a sponsor catalog feed."""

    integration_type = "catalog_feed"
    default_config_keys = ("feed_url", "sync_interval")


class WebhookAdapter(SponsorAdapter):
    """Push-based adapter: the sponsor triggers the showcase via signed webhook."""

    integration_type = "webhook"
    default_config_keys = ("endpoint_url", "signature_header")


class APIKeyAdapter(SponsorAdapter):
    """Request-based adapter: the showcase calls sponsor APIs with a keyed env var."""

    integration_type = "api_key"
    default_config_keys = ("key_env_var", "base_url")


_ADAPTER_TYPES: dict[str, type[SponsorAdapter]] = {
    cls.integration_type: cls for cls in (CatalogFeedAdapter, WebhookAdapter, APIKeyAdapter)
}

#: Integration types the adapter layer understands (stable, tested surface).
SUPPORTED_INTEGRATION_TYPES: tuple[str, ...] = tuple(sorted(_ADAPTER_TYPES))


class UnknownIntegrationTypeError(ValueError):
    """Raised when a sponsor declares an integration type no adapter implements."""


def build_adapter(sponsor: Sponsor) -> SponsorAdapter:
    """Return the adapter instance for a sponsor's declared integration type.

    Raises:
        UnknownIntegrationTypeError: If no adapter implements the type.
    """
    adapter_cls = _ADAPTER_TYPES.get(sponsor.integration.type)
    if adapter_cls is None:
        raise UnknownIntegrationTypeError(
            f"{sponsor.sponsor_id}: no adapter for integration type "
            f"{sponsor.integration.type!r} (supported: {', '.join(SUPPORTED_INTEGRATION_TYPES)})"
        )
    return adapter_cls(sponsor)


@lru_cache(maxsize=1)
def load_sponsors(path: str | None = None) -> SponsorRegistry:
    """Load and validate the sponsor registry from JSON.

    Raises:
        FileNotFoundError: If the registry file is missing.
        ValueError: If the JSON does not match the schema.
    """
    sponsors_path = Path(path) if path else _default_sponsors_path()
    raw: dict[str, Any] = json.loads(sponsors_path.read_text(encoding="utf-8"))
    return SponsorRegistry.model_validate(raw)


def get_sponsor(sponsor_id: str, path: str | None = None) -> Sponsor | None:
    """Return the sponsor with the given id, or None."""
    registry = load_sponsors(path)
    for sponsor in registry.sponsors:
        if sponsor.sponsor_id == sponsor_id:
            return sponsor
    return None


def adapter_errors(
    registry: SponsorRegistry, catalog: Catalog | None = None
) -> list[str]:
    """Cross-validate the sponsor registry (deterministic integrity checks).

    Checks: unique sponsor ids, a known adapter per integration, non-empty
    attribution, and — when a catalog is provided — that every attributed
    slug resolves to a real catalog agent.
    """
    errors: list[str] = []
    seen: set[str] = set()
    for sponsor in registry.sponsors:
        if sponsor.sponsor_id in seen:
            errors.append(f"duplicate sponsor_id: {sponsor.sponsor_id}")
        seen.add(sponsor.sponsor_id)
        try:
            adapter = build_adapter(sponsor)
        except UnknownIntegrationTypeError as exc:
            errors.append(str(exc))
            continue
        errors.extend(adapter.validate_contract())
        if adapter.required_config_keys() != adapter.default_config_keys:
            errors.append(
                f"{sponsor.sponsor_id}: config keys {list(adapter.required_config_keys())} "
                f"do not match the {adapter.integration_type} contract "
                f"{list(adapter.default_config_keys)}"
            )
        if catalog is not None:
            known = {agent.slug for agent in catalog.agents}
            for slug in adapter.attributed_agent_slugs():
                if slug not in known:
                    errors.append(
                        f"{sponsor.sponsor_id}: attributes unknown agent slug {slug!r}"
                    )
    return errors


def sponsor_attributions(
    registry: SponsorRegistry | None = None,
    catalog: Catalog | None = None,
) -> dict[str, list[str]]:
    """Map agent slug -> ordered sponsor ids that integrate with it.

    Args:
        registry: Optional registry (defaults to the loaded one).
        catalog: Optional catalog; when given, unattributable slugs raise
            ValueError (call adapter_errors first to report instead).

    Returns:
        Mapping of slug to sponsor-id list (agents with no sponsors omitted).
    """
    if registry is None:
        registry = load_sponsors()
    known: set[str] | None = None
    if catalog is not None:
        known = {agent.slug for agent in catalog.agents}
    attributions: dict[str, list[str]] = {}
    for sponsor in registry.sponsors:
        for slug in dict.fromkeys(sponsor.agent_slugs):
            if known is not None and slug not in known:
                raise ValueError(f"{sponsor.sponsor_id}: unknown agent slug {slug!r}")
            attributions.setdefault(slug, []).append(sponsor.sponsor_id)
    return attributions


def agents_with_sponsors(
    agents: list[Agent], attributions: Mapping[str, list[str]] | None = None
) -> list[dict[str, Any]]:
    """Serialize agents with an added ``sponsors`` attribution field.

    When no attribution map is supplied, one is derived from the full registry
    validated against the full catalog (never a synthetic subset), so a single
    serialized agent sees the same attribution it would inside /api/agents.
    """
    if attributions is None:
        attributions = sponsor_attributions(load_sponsors(), load_catalog())
    out: list[dict[str, Any]] = []
    for agent in agents:
        payload = agent.model_dump()
        payload["sponsors"] = list(attributions.get(agent.slug, []))
        out.append(payload)
    return out
