#!/usr/bin/env bash
# Ask the Basalt Wall front desk four questions through Dify's service API, the same
# API a gym website chat widget would call. The questions share one conversation.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE="$HERE/.dify-state.json"
[ -f "$STATE" ] || { echo "No .dify-state.json - run ./setup.sh first." >&2; exit 1; }

python3 - "$STATE" <<'PY'
import json, sys, urllib.request

state = json.load(open(sys.argv[1]))
url, key = state["dify_url"], state["app_api_key"]
QUESTIONS = [
    "I'm a student. What's the cheapest way to climb twice a week, and what do I need to show?",
    "I'm travelling for six weeks this summer. Can I pause my monthly membership, and what does it cost?",
    "I've only bouldered so far. What do I need before I can top-rope, and what about lead?",
    "Is the cave open on Tuesday morning? I want to try the new problems.",
]
conversation_id = ""
for i, q in enumerate(QUESTIONS, 1):
    print(f"\n[{i}/{len(QUESTIONS)}] Climber: {q}")
    req = urllib.request.Request(
        f"{url}/v1/chat-messages",
        data=json.dumps({"inputs": {}, "query": q, "response_mode": "blocking",
                         "conversation_id": conversation_id, "user": "demo-climber",
                         # Dify would otherwise call the model once more to title a new conversation,
                         # and that call shows up in Opik as an extra generate_conversation_name trace.
                         "auto_generate_name": False}).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        body = json.load(resp)
    conversation_id = body.get("conversation_id", conversation_id)
    print(f"Front desk: {body['answer']}")
PY
