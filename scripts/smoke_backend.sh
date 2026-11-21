#!/usr/bin/env bash
# Asserts docs/INTERFACES.md section 1 shapes against a backend on :8787 (stub or real).
# Usage: scripts/smoke_backend.sh [base_url]
set -euo pipefail
BASE="${1:-http://localhost:8787}"

check() { python3 -c "import sys,json; d=json.load(sys.stdin); $1" || { echo "FAIL: $2"; exit 1; }; echo "ok   $2"; }

curl -sS "$BASE/health" | check 'assert d["ok"] is True' "GET /health"

U=$(curl -sS -X POST "$BASE/utterance" -H 'Content-Type: application/json' \
  -d '{"text":"find me an espresso machine under three hundred dollars"}')
echo "$U" | check 'assert d["session_id"]; r=d["reply"]; assert r["speech"] and r["pick_id"]; assert len(r["speech"].split())<=45, "speech too long"' "POST /utterance (first)"
SID=$(echo "$U" | python3 -c 'import sys,json;print(json.load(sys.stdin)["session_id"])')

curl -sS -X POST "$BASE/utterance" -H 'Content-Type: application/json' \
  -d "{\"session_id\":\"$SID\",\"text\":\"under two hundred\"}" \
  | check 'assert d["reply"]["did_research"] is True, "re-search must flag did_research"' "POST /utterance (re-search)"

curl -sS "$BASE/state?session_id=$SID" | check '
assert d["phase"] in ("idle","listening","searching","comparing","pick","handoff","done")
assert 1 <= len(d["candidates"]) <= 5
assert sum(c["is_pick"] for c in d["candidates"]) == 1
c=d["candidates"][0]; assert isinstance(c["price_minor"], int) and c["seller"]["domain"]
assert d["constraints"]["budget_max_minor"] == 20000
assert d["handoff"] is None' "GET /state (pick)"

I=$(curl -sS -X POST "$BASE/intent" -H 'Content-Type: application/json' \
  -d "{\"session_id\":\"$SID\",\"type\":\"buy\",\"source\":\"button\"}")
echo "$I" | check 'assert d["handoff"]["status"] in ("ready","requires_escalation","stale_pick","error"); assert "continue_url" not in json.dumps(d), "continue_url leaked to device response"' "POST /intent (no continue_url to device)"

curl -sS "$BASE/state?session_id=$SID" | check 'h=d["handoff"]; assert h and h["continue_url"].startswith("https://"); assert d["phase"]=="handoff"' "GET /state (handoff has continue_url)"

curl -sS -X POST "$BASE/session/clear" -H 'Content-Type: application/json' -d "{\"session_id\":\"$SID\"}" \
  | check 'assert d["ok"] is True' "POST /session/clear"

curl -sS "$BASE/state?session_id=$SID" | check 'assert d["handoff"] is None and d["candidates"]==[]' "GET /state (cleared)"

echo "ALL OK against $BASE"
