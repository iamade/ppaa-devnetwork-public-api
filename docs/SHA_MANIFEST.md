# SHA Manifest — DevNetwork submission surface

Complete, verifiable lineage of every delivered unit on
`iamade/ppaa-devnetwork-public-api`. All runtime code on `staging` descends
from these exact commits; `main` stays at the initial public commit until Ade
approves the final submission (checklist row 11).

| Ticket | Commit | Branch / line | Content |
|--------|--------|---------------|---------|
| repo init | `a4935a8` | `main` (protected) | Initial public commit: README + Apache-2.0 LICENSE only — no private code, no credentials |
| PP-79 | `ffa387b` | `feat/pp-79-agent-showcase-catalog` | Agent showcase catalog: FastAPI `/health` (pg `SELECT 1` + redis `PING`), `/api/agents`, static UI, loopback compose stack, 13 deterministic tests |
| PP-63 | `ef3ca87` | `feature/pp-63-docs-public-demo` | Submission docs (SETUP/API/ARCHITECTURE/DEMO/SUBMISSION) + scripted public demo `scripts/demo.sh` |
| PP-63 | `d95f135` | `feature/pp-63-docs-public-demo` | Repo hygiene: add `.gitignore`, drop committed pycache artifact |
| PP-79 | `51e0e99` | `feat/pp-79-agent-showcase-catalog` | QA-PASS fix: null-safe `chip()` guard in catalog UI + Node render smoke tests |
| PP-79 + PP-63 | `f6d0fcf` | `staging` | Staging tip carrying PP-79 QA PASS + PP-63 docs/demo — Mac Retest surface |
| PP-80 | `2ec6bf9` | `feat/pp-80-sponsor-adapters` | Multi-sponsor integration adapters: registry `data/sponsors.json`, adapter layer `sponsors.py`, `/api/sponsors`(+`/{id}`), UI strip + badges, 15 tests |
| PP-80 | `ea053d6` | `staging` | Merge of PP-80 into staging — staging tip used as the PP-81 base |
| PP-81 | see delivery packet | `feat/pp-81-submission-packaging` (from `ea053d6`) | Final submission packaging: demo video, this SHA manifest, SUBMISSION.md refresh, packaging tests |

## Evidence artifacts (versioned paths — SHA/timestamp in filename, never overwritten)

| Artifact | Path | Verification |
|----------|------|--------------|
| Demo video (PP-81) | `evidence/demo/devnetwork-demo-ea053d68-20260827T2041Z.mp4` | MP4 (H.264 yuv420p), 1440×900, 74 s, recorded live from the running stack 2026-08-27 20:38–20:41 UTC; frames are real screenshots / real API responses / real `demo.sh` output; enforced by `tests/test_submission_packaging.py` |
| Packaged artifact | `dist/ppaa-devnetwork-submission-<sha8>-<UTC-timestamp>.tar.gz` (generated from the exact delivery commit via `git archive`; sha256 recorded in the delivery packet) | `tar tzf` + sha256 |

## Reproducing any line

```bash
git fetch origin
git checkout <sha>            # any commit above
docker compose up -d --build  # loopback-only: 8005 / 5174 / 25432 / 26379
bash scripts/demo.sh          # 6/6 PASS expected
```

Rules carried into every gate: AFD-108 (Docker PostgreSQL 16 + Redis 7-alpine
dev/staging; managed services production-only) · PP-83 port rule (no base
5432/6379 host mappings, loopback-only publishes) · `feature/*` → `staging`,
`main` only with Ade's approval · every PASS claim tied to an exact SHA.
