# PPAA Agent Showcase (PP-79)

Public-facing agent demo catalog and presentation layer for the People Protocol
AI (PPAA) fleet — the DevNetwork submission surface (deadline 2026-09-03).

Repository: `iamade/ppaa-devnetwork-public-api` · License: Apache-2.0 · Branch: `feat/pp-79-agent-showcase-catalog`

## What it shows

- A catalog UI of the PPAA agent fleet (Coordinator, Director, Builder, QA,
  Scribe, Mavis, Amara, Akande, Codex Mac Retest, Tobi) with role
  descriptions, channel/Jira references, demo routes, and evidence links.
- A small FastAPI backend serving `/api/agents`, `/api/agents/{slug}` and a
  `/health` endpoint that verifies PostgreSQL and Redis connectivity.

## Architecture (AFD-108)

Development/staging uses Docker **PostgreSQL 16** and **Redis 7-alpine**.
Supabase/managed services are production-only. All published ports bind to
`127.0.0.1` only and never retain base `5432`/`6379` host mappings (PP-83 rule).

| Service  | Image              | Host target (canonical) |
|----------|--------------------|-------------------------|
| backend  | built (`app`)      | http://localhost:8005   |
| frontend | nginx:1.27-alpine  | http://localhost:5174   |
| postgres | postgres:16-alpine | 127.0.0.1:25432 → 5432  |
| redis    | redis:7-alpine     | 127.0.0.1:26379 → 6379  |

## Setup

```bash
git clone https://github.com/iamade/ppaa-devnetwork-public-api.git
cd ppaa-devnetwork-public-api
cp .env.example .env   # defaults work locally; no secrets required
```

## Run (staging stack)

Start:

```bash
docker compose up -d --build
```

Verify:

```bash
curl -fsS http://localhost:8005/health    # {"status":"healthy",...}
curl -fsS http://localhost:8005/api/agents
open http://localhost:5174                # catalog UI
```

Stop:

```bash
docker compose down
```

## Development (no Docker for Python)

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
uvicorn ppaa_showcase.main:app --port 8005
```

## Tests / checks

```bash
ruff check src tests
mypy src
pytest -q
pytest tests/test_compose_ports.py -v   # deterministic compose port assertions
```

## Layout

```
src/ppaa_showcase/   FastAPI app (config, catalog model, health, main)
data/agents.json     catalog source of truth
frontend/            static catalog UI (HTML/CSS/JS, no build step)
tests/               API, catalog-data, and compose-port tests
docker-compose.yml   postgres 16 / redis 7 / app / web staging stack
```
