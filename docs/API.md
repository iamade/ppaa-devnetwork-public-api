# API Reference — PPAA Agent Showcase

Base URL (local/staging): `http://localhost:8005` · All endpoints are `GET` only ·
CORS is enabled for the static frontend origins (`http://localhost:5174`,
`http://127.0.0.1:5174` by default).

Interactive docs: `http://localhost:8005/docs` (FastAPI/OpenAPI).

## `GET /health`

Liveness + dependency readiness. Returns **200** when PostgreSQL and Redis are
both reachable, **503** with per-check detail otherwise.

```bash
curl -fsS http://localhost:8005/health
```

```json
{
  "status": "healthy",
  "checks": { "postgres": true, "redis": true }
}
```

Failure shape (503):

```json
{
  "detail": {
    "status": "unhealthy",
    "checks": { "postgres": true, "redis": false },
    "errors": { "redis": "connection refused" }
  }
}
```

## `GET /api/agents`

Returns the full agent catalog. Source of truth: `data/agents.json`
(schema-validated at import and by tests).

```bash
curl -fsS http://localhost:8005/api/agents | python3 -m json.tool | head -20
```

```json
{
  "count": 10,
  "updated": "2026-08-27T04:50:00Z",
  "agents": [
    {
      "slug": "ppaa-coordinator",
      "name": "PPAA-Coordinator",
      "role": "Routing & staging-surface registry",
      "description": "…",
      "channel": "#ppaa-coordination",
      "jira_refs": ["PP-62"],
      "demo_routes": ["/api/agents/ppaa-coordinator"],
      "evidence_links": ["…"],
      "sponsors": ["devnetwork-platform"]
    }
  ]
}
```

## `GET /api/agents/{slug}`

Returns one agent entry. **404** when the slug is unknown.

Catalog slugs: `ppaa-coordinator`, `ppaa-director`, `ppaa-builder`, `ppaa-qa`, `ppaa-scribe`, `mavis`, `amara-vps-ops`, `akande-vps-main`, `codex-mac-retest`, `tobi`.

```bash
curl -fsS http://localhost:8005/api/agents/ppaa-builder
```

```json
{
  "slug": "ppaa-builder",
  "name": "PPAA-Builder",
  "role": "Staging surface creation & repair",
  "description": "Creates and repairs staging surfaces, supplies branch/SHA/start-stop proof, and runs deterministic ruff/mypy/pytest/compose checks plus live /health verification.",
  "channel": "#ppaa-build",
  "jira_refs": ["PP-83", "PP-75", "PP-79"],
  "demo_routes": ["/api/agents/ppaa-builder", "/health"],
  "evidence_links": ["Merge 61cb56d (staging->main, PP-75/76/77/83/86)", "Discord: #ppaa-build packets"]
}
```

## `GET /api/sponsors`

Returns the multi-sponsor integration registry (PP-80). Source of truth:
`data/sponsors.json`; every entry is validated against the adapter layer at
request time — a registry that violates an adapter contract fails **500**
with explicit errors instead of serving bad data.

```bash
curl -fsS http://localhost:8005/api/sponsors
```

```json
{
  "count": 3,
  "updated": "2026-08-27T14:50:00Z",
  "integration_types": ["api_key", "catalog_feed", "webhook"],
  "sponsors": [
    {
      "sponsor_id": "devnetwork-platform",
      "name": "DevNetwork Platform",
      "tier": "platform",
      "summary": "…",
      "challenge_title": "Multi-Agent Showcase",
      "challenge_category": "agent-platforms",
      "integration": { "type": "catalog_feed", "config_keys": ["feed_url", "sync_interval"] },
      "agent_slugs": ["ppaa-coordinator", "ppaa-director", "ppaa-builder", "ppaa-qa", "ppaa-scribe"],
      "example": false
    }
  ]
}
```

Adapter types: `catalog_feed` (pull), `webhook` (push), `api_key` (request).
Entries with `"example": true` are clearly-labelled adapter templates — swap
in the final published sponsor list by editing `data/sponsors.json` only.

## `GET /api/sponsors/{sponsor_id}`

Returns one sponsor with its integration contract and fully-expanded
`agents` array. **404** when the sponsor id is unknown.

```bash
curl -fsS http://localhost:8005/api/sponsors/devnetwork-platform
```

Sponsor ids: `devnetwork-platform`, `sample-webhook-sponsor`, `sample-apikey-sponsor`.

## `GET /` and `GET /static/*`

Same-origin static catalog UI (no build step). Primary frontend target is the
nginx service on `http://localhost:5174`; the same files are served by the API
container for single-port demos.

## Agent schema

| Field           | Type           | Notes                                    |
|-----------------|----------------|------------------------------------------|
| `slug`          | string         | unique identifier, used in the detail URL |
| `name`          | string         | display name                             |
| `role`          | string         | one-line role summary                    |
| `description`   | string         | fuller description                       |
| `channel`       | string         | home channel                             |
| `jira_refs`     | list[string]   | related Jira tickets                     |
| `demo_routes`   | list[string]   | routes to hit when demoing this agent    |
| `evidence_links`| list[string]   | public evidence pointers                 |
| `sponsors`      | list[string]   | sponsor ids integrating this agent (PP-80; empty list = none) |
