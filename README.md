# PPAA Agent Showcase

Public-facing agent demo catalog and presentation layer for the People Protocol
AI (PPAA) fleet — the DevNetwork 2026 submission surface (Jira epic **PP-63**,
deadline **2026-09-03**). Catalog layer delivered as PP-79.

Repository: `iamade/ppaa-devnetwork-public-api` · License: Apache-2.0 · Staging branch: `staging`

## What it shows

- A catalog UI of the PPAA agent fleet (Coordinator, Director, Builder, QA,
  Scribe, Mavis, Amara, Akande, Codex Mac Retest, Tobi) with role
  descriptions, channel/Jira references, demo routes, and evidence links.
- A small FastAPI backend serving `/api/agents`, `/api/agents/{slug}`,
  `/api/sponsors`, `/api/sponsors/{sponsor_id}` and a `/health` endpoint that
  verifies PostgreSQL and Redis connectivity.
- A multi-sponsor integration adapter layer (PP-80): data-driven sponsor
  registry (`data/sponsors.json`) with `catalog_feed` / `webhook` / `api_key`
  adapters, agent-to-sponsor attribution in the API and UI sponsor badges.
  Template sponsors are clearly labelled until the final published list lands.

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

## Demo

One-command scripted demo (health → catalog → detail → 404 → UI):

```bash
bash scripts/demo.sh
```

Full walkthrough: [docs/DEMO.md](docs/DEMO.md).

## Setup

Detailed guide (prerequisites, env vars, troubleshooting, reset):
[docs/SETUP.md](docs/SETUP.md). Quick start:

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
curl -fsS http://localhost:8005/api/sponsors
open http://localhost:5174                # catalog UI + sponsor strip
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

## Documentation

- [docs/SETUP.md](docs/SETUP.md) — install, configure, verify, troubleshoot
- [docs/API.md](docs/API.md) — endpoint reference with examples
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system overview + mermaid diagram
- [docs/DEMO.md](docs/DEMO.md) — scripted and manual demo walkthroughs
- [docs/SUBMISSION.md](docs/SUBMISSION.md) — DevNetwork submission checklist
- [docs/SHA_MANIFEST.md](docs/SHA_MANIFEST.md) — verifiable commit lineage + evidence artifacts for the final submission

## Tests / checks

```bash
ruff check src tests
mypy src
pytest -q
pytest tests/test_compose_ports.py -v   # deterministic compose port assertions
```

## Layout

```
src/ppaa_showcase/   FastAPI app (config, catalog, sponsors, health, main)
data/agents.json     catalog source of truth
data/sponsors.json   multi-sponsor registry (adapter-validated)
frontend/            static catalog UI (HTML/CSS/JS, no build step)
scripts/demo.sh      deterministic scripted demo
docs/                SETUP, API, ARCHITECTURE, DEMO, SUBMISSION, SHA_MANIFEST guides
evidence/             versioned submission artifacts (demo video)
tests/               API, catalog-data, sponsor-adapter, render-smoke, compose-port, and docs tests
docker-compose.yml   postgres 16 / redis 7 / app / web staging stack
```
