# Demo Walkthrough — PPAA Agent Showcase

A deterministic demo script ships with the repo:

```bash
bash scripts/demo.sh
```

It exercises, in order: dependency health → full catalog → agent detail →
(404 handling) → frontend availability, and prints a one-line PASS/FAIL per
step with a final verdict. Use it as the backbone for screen recordings
(PP-81 submission video): start the stack, run the script, then click through
the UI at http://localhost:5174.

## Manual walkthrough (≈2 minutes)

1. **Health** — `curl -s http://localhost:8005/health`
   Shows real PostgreSQL (SELECT 1) and Redis (PING) verification, not a stub.
2. **Fleet catalog** — `curl -s http://localhost:8005/api/agents`
   10 agents with role, channel, Jira refs, demo routes, evidence links.
3. **Agent detail** — `curl -s http://localhost:8005/api/agents/ppaa-builder`
   Per-agent deep link; try `mavis`, `codex-mac-retest`, `tobi`.
4. **Unknown agent** — `curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8005/api/agents/nope`
   Returns 404 with a helpful detail body.
5. **UI** — open `http://localhost:5174`
   Static nginx-served catalog; desktop (≥1440×900) and mobile (≤390×844) layouts.
6. **Interactive API docs** — open `http://localhost:8005/docs`

## Script exit codes

| Code | Meaning                                            |
|------|----------------------------------------------------|
| 0    | All demo steps passed                              |
| 1    | One or more steps failed (stack not up, port clash) |
