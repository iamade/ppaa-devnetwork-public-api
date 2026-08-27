# DevNetwork Submission Checklist — Sep 3, 2026

Tracking sheet for the DevNetwork hackathon submission surface
(`iamade/ppaa-devnetwork-public-api`, Jira epic PP-63). Owner lanes per sprint:
Builder = build/evidence, QA = visual verification (#ppaa-qa-evidence),
Director = acceptance, Ade = final submission approval.

| # | Requirement                          | Status | Evidence / owner                                    |
|---|--------------------------------------|--------|-----------------------------------------------------|
| 1 | Dedicated public repository          | ✅ Done | github.com/iamade/ppaa-devnetwork-public-api (public, Apache-2.0, main protected) |
| 2 | Isolated public-API surface (no credentials) | ✅ Done | Initial commit `a4935a8` — README/LICENSE only; no PPAA-private code |
| 3 | Agent showcase catalog (PP-79)       | ✅ Delivered | `ffa387b` — FastAPI `/api/agents` + static UI; In Review (QA visual pending) |
| 4 | Setup documentation                  | ✅ Done | `docs/SETUP.md` (this branch) |
| 5 | API reference                        | ✅ Done | `docs/API.md` (this branch) |
| 6 | Architecture overview + diagram      | ✅ Done | `docs/ARCHITECTURE.md` (this branch) |
| 7 | Public demo (scripted)               | ✅ Done | `scripts/demo.sh` + `docs/DEMO.md` (this branch) |
| 8 | Deterministic quality gates          | ✅ Done | ruff / mypy strict / pytest incl. compose-port + docs tests |
| 9 | Multi-sponsor integration adapters (PP-80) | ✅ Delivered | `feat/pp-80-sponsor-adapters` — `/api/sponsors`(+`/{id}`), adapter layer `sponsors.py`, UI strip + badges; example sponsors labelled until final list publishes |
| 10| Submission packaging + demo video (PP-81) | ⏳ Pending | Gated on PP-80; video skeleton = `scripts/demo.sh` walk + UI click-through |
| 11| Final submission                     | ⏳ Pending | Ade approval only |

## Rules carried into every gate

- AFD-108: Docker PostgreSQL 16 + Redis 7-alpine for dev/staging; managed
  services are production-only.
- PP-83 port rule: no base `5432`/`6379` host mappings; all published ports
  loopback-only — enforced by tests.
- `feature/*` → `staging`; `main`/production only with Ade's approval.
- Every PASS claim is tied to an exact candidate SHA verified live.
