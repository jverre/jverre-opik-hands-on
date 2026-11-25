#!/usr/bin/env bash
# Post the three sample submissions in data/submissions.json to the webhook.
# Each POST is one workflow execution, which n8n-observability exports as one Opik trace.
set -euo pipefail
cd "$(dirname "$0")"
WEBHOOK="${WEBHOOK:-http://localhost:5678/webhook/hackathon-screening}"

python3 -c 'import json; [print(json.dumps(s)) for s in json.load(open("data/submissions.json"))]' |
while read -r body; do
  team=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["team"])' "$body")
  echo "-- $team"
  ok=""
  # The webhook registers a few seconds after activation, so retry for ~30 s.
  for _ in $(seq 1 15); do
    if out=$(curl -sf -X POST "$WEBHOOK" -H 'Content-Type: application/json' -d "$body"); then
      echo "$out" | python3 -m json.tool; ok=yes; break
    fi
    sleep 2
  done
  [ -n "$ok" ] || { echo "no answer from $WEBHOOK - did ./setup.sh finish?" >&2; exit 1; }
done
echo "Open the n8n-hackathon-screening project in Opik: one trace per submission."
