#!/usr/bin/env bash
# Deterministic demo for the PPAA Agent Showcase (DevNetwork submission surface).
# Exit 0 = all steps passed; exit 1 = at least one failure.
set -u

API="${API_URL:-http://localhost:8005}"
WEB="${WEB_URL:-http://localhost:5174}"
failures=0

step() { printf '%-46s' "$1"; }
ok()   { printf 'PASS\n'; }
bad()  { printf 'FAIL (%s)\n' "$1"; failures=$((failures + 1)); }

require() { command -v "$1" >/dev/null 2>&1; }

if ! require curl; then
    echo "demo: curl is required" >&2
    exit 1
fi

step "1/6 backend /health (pg SELECT 1 + redis PING)"
body="$(curl -fsS "$API/health" 2>/dev/null)" \
    && printf '%s' "$body" | grep -q '"status":"healthy"' \
    && ok || bad "GET $API/health did not return status=healthy"

step "2/6 catalog /api/agents"
body="$(curl -fsS "$API/api/agents" 2>/dev/null)" \
    && printf '%s' "$body" | grep -q '"count":' \
    && printf '%s' "$body" | grep -q '"ppaa-builder"' \
    && ok || bad "GET $API/api/agents missing count or ppaa-builder"

step "3/6 agent detail /api/agents/ppaa-builder"
body="$(curl -fsS "$API/api/agents/ppaa-builder" 2>/dev/null)" \
    && printf '%s' "$body" | grep -q '"slug":"ppaa-builder"' \
    && ok || bad "GET $API/api/agents/ppaa-builder did not return the agent"

step "4/6 sponsors /api/sponsors + /api/sponsors/{id}"
body="$(curl -fsS "$API/api/sponsors" 2>/dev/null)" \
    && printf '%s' "$body" | grep -q '"count":' \
    && printf '%s' "$body" | grep -q '"devnetwork-platform"' \
    && body="$(curl -fsS "$API/api/sponsors/devnetwork-platform" 2>/dev/null)" \
    && printf '%s' "$body" | grep -q '"sponsor_id":"devnetwork-platform"' \
    && printf '%s' "$body" | grep -q '"integration":{"type":"catalog_feed"' \
    && ok || bad "GET /api/sponsors(+detail) missing count, devnetwork-platform, or catalog_feed contract"

step "5/6 unknown agent returns 404"
code="$(curl -s -o /dev/null -w '%{http_code}' "$API/api/agents/does-not-exist")" \
    && [ "$code" = "404" ] && ok || bad "expected 404, got ${code:-none}"

step "6/6 frontend UI"
code="$(curl -s -o /dev/null -w '%{http_code}' "$WEB/")" \
    && [ "$code" = "200" ] && ok || bad "GET $WEB/ returned ${code:-none}"

echo
if [ "$failures" -eq 0 ]; then
    echo "DEMO RESULT: ALL STEPS PASSED"
    exit 0
fi
echo "DEMO RESULT: ${failures} STEP(S) FAILED — see docs/SETUP.md#8-troubleshooting"
exit 1
