#!/usr/bin/env bash
# What the device will send, from the laptop. Proves the two device routes.
# Usage: device/smoke_http.sh [base_url]
set -euo pipefail
BASE="${1:-http://localhost:8787}"
echo "== utterance"
R=$(curl -sS --max-time 10 -X POST "$BASE/utterance" -H 'Content-Type: application/json' \
  -d '{"text":"find me an espresso machine under three hundred dollars"}')
echo "$R" | python3 -c 'import sys,json; d=json.load(sys.stdin); print("session:",d["session_id"]); print("speak :",d["reply"]["speech"])'
SID=$(echo "$R" | python3 -c 'import sys,json;print(json.load(sys.stdin)["session_id"])')
echo "== intent (button)"
curl -sS --max-time 10 -X POST "$BASE/intent" -H 'Content-Type: application/json' \
  -d "{\"session_id\":\"$SID\",\"type\":\"buy\",\"source\":\"button\"}" \
  | python3 -c 'import sys,json; d=json.load(sys.stdin); print("status:",d["handoff"]["status"]); print("speak :",d["reply"]["speech"]); assert "continue_url" not in json.dumps(d)'
echo "== clear"
curl -sS --max-time 10 -X POST "$BASE/session/clear" -H 'Content-Type: application/json' -d "{\"session_id\":\"$SID\"}"; echo
echo "device contract OK"
