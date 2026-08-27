# Setup Guide — PPAA Agent Showcase (DevNetwork submission surface)

Target audience: judges, reviewers, and new developers cloning
`iamade/ppaa-devnetwork-public-api` for the first time.

## 1. Prerequisites

| Requirement     | Version tested       |
|-----------------|----------------------|
| Docker Engine   | 24+ (with Compose v2)|
| Docker Compose  | v2.20+               |
| curl            | any                  |
| (optional) Python | 3.12+ for non-Docker dev & tests |

No cloud accounts, API keys, or secrets are required. Development/staging runs
entirely on Docker **PostgreSQL 16** and **Redis 7-alpine** (AFD-108 rule);
Supabase/managed services are production-only and out of scope locally.

## 2. Clone and configure

```bash
git clone https://github.com/iamade/ppaa-devnetwork-public-api.git
cd ppaa-devnetwork-public-api
git checkout staging                 # staging candidate branch
cp .env.example .env                 # local defaults work as-is
```

`.env` variables (all optional — defaults match `docker-compose.yml`):

| Variable             | Default                          | Purpose                                   |
|----------------------|----------------------------------|-------------------------------------------|
| `APP_PORT`           | `8005`                           | FastAPI backend host port                 |
| `WEB_PORT`           | `5174`                           | nginx static frontend host port           |
| `POSTGRES_HOST_PORT` | `25432`                          | Published Postgres port (loopback only)   |
| `REDIS_HOST_PORT`    | `26379`                          | Published Redis port (loopback only)      |
| `ALLOWED_ORIGINS`    | `http://localhost:5174,...`      | CORS origins permitted to call the API    |

Port rule (PP-83 delivery rule): published host ports never retain the base
`5432`/`6379` mappings and every published port binds to `127.0.0.1` only.
This is asserted deterministically by `tests/test_compose_ports.py`.

## 3. Start the stack

```bash
docker compose up -d --build
docker compose ps        # wait until postgres and redis report (healthy)
```

Expected: four services — `app` (FastAPI), `web` (nginx static UI),
`postgres` (pg16-alpine), `redis` (redis7-alpine).

## 4. Verify

```bash
curl -fsS http://localhost:8005/health     # 200 {"status":"healthy","checks":{"postgres":true,"redis":true}}
curl -fsS http://localhost:8005/api/agents # 200 catalog JSON, count = 10
open http://localhost:5174                 # catalog UI renders the fleet
```

Or run the scripted demo: `bash scripts/demo.sh` (see `docs/DEMO.md`).

## 5. Stop / reset

```bash
docker compose down          # stop and remove containers
docker compose down -v       # also remove the Postgres data volume
```

## 6. Development without Docker (Python only)

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
uvicorn ppaa_showcase.main:app --port 8005
```

Note: `/health` reports `postgres:false, redis:false` (503) until Postgres and
Redis are reachable; point `POSTGRES_HOST`/`REDIS_HOST` at the published
loopback ports (127.0.0.1:25432 / 127.0.0.1:26379) to reuse the Docker ones.

## 7. Quality gates

```bash
ruff check src tests
mypy src
pytest -q
pytest tests/test_compose_ports.py -v
```

## 8. Troubleshooting

| Symptom                                   | Fix                                                                |
|-------------------------------------------|--------------------------------------------------------------------|
| Port already in use                       | Change `APP_PORT`/`WEB_PORT`/`*_HOST_PORT` in `.env`               |
| `/health` returns 503                     | `docker compose ps` — wait for pg/redis `healthy`, then retry       |
| Frontend loads but API calls blocked       | Check `ALLOWED_ORIGINS` includes the origin you opened the UI from |
| `docker compose config` fails             | Ensure `.env` exists (`cp .env.example .env`)                      |
