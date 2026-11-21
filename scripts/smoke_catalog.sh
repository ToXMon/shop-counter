#!/usr/bin/env bash
# Live check: Shopify Global Catalog search, no API key.
# Usage: scripts/smoke_catalog.sh ["espresso machine"] [max_minor=30000]
set -euo pipefail
Q="${1:-espresso machine}"
MAX="${2:-30000}"

curl -sS --max-time 20 https://catalog.shopify.com/api/ucp/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json' \
  -d "$(cat <<JSON
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"search_catalog","arguments":{
  "meta":{"ucp-agent":{"profile":"https://shopify.dev/ucp/agent-profiles/examples/2026-08-25/valid-with-capabilities.json"}},
  "catalog":{"query":"$Q","context":{"address_country":"US","currency":"USD"},
             "filters":{"price":{"max":$MAX}},"pagination":{"limit":5}}}}}
JSON
)" | python3 -c '
import sys, json
b = json.load(sys.stdin)
if "error" in b: sys.exit("JSON-RPC error: " + b["error"]["message"])
d = b["result"]["structuredContent"]
assert d["ucp"]["status"] == "success", d.get("messages")
print("OK status=success total=%s" % d["pagination"]["total_count"])
for p in d["products"]:
    v = p["variants"][0]
    print(" - %-55s $%7.2f  %s" % (p["title"][:55], v["price"]["amount"]/100, v["seller"]["name"]))
'
