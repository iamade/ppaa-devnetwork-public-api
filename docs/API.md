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
      "evidence_links": ["…"]
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
