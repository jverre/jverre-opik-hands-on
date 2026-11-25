#!/usr/bin/env bash
# Headless setup, no browser needed:
#   1. build and start n8n with the Opik OpenTelemetry hooks baked in
#   2. claim the instance (local owner account) and mint an n8n API key
#   3. create the OpenAI credential from $OPENAI_API_KEY (never written to a file)
#   4. import workflow/hackathon-screening.json and activate it
# Needs: docker, curl, python3. Keys come from the shell or the repo-root .env.
set -euo pipefail
cd "$(dirname "$0")"

N8N_URL="http://localhost:5678"
OWNER_EMAIL="judge@example.com"      # local-only demo account, n8n requires one
OWNER_PASSWORD="Hackathon-demo-1"
PROJECT="n8n-hackathon-screening"

# --- 0. Resolve settings -----------------------------------------------------
if [ -f ../.env ]; then set -a; . ../.env; set +a; fi
: "${OPENAI_API_KEY:?Set OPENAI_API_KEY (shell env or repo-root .env)}"
OPIK_URL_OVERRIDE="${OPIK_URL_OVERRIDE:-http://localhost:5173/api/}"
OPIK_WORKSPACE="${OPIK_WORKSPACE:-default}"

# Opik: the container cannot reach the host's "localhost", so point the OTLP
# exporter at host.docker.internal. Opik ingests OTLP under /v1/private/otel.
OPIK_OTLP_ENDPOINT="$(echo "${OPIK_URL_OVERRIDE%/}" | sed -e 's#//localhost#//host.docker.internal#' -e 's#//127\.0\.0\.1#//host.docker.internal#')/v1/private/otel"
# Opik: Comet-Workspace picks the workspace, projectName picks the project.
# A local Opik needs no Authorization header; Opik Cloud does.
OPIK_OTLP_HEADERS="Comet-Workspace=${OPIK_WORKSPACE},projectName=${PROJECT}"
if [ -n "${OPIK_API_KEY:-}" ]; then OPIK_OTLP_HEADERS="Authorization=${OPIK_API_KEY},${OPIK_OTLP_HEADERS}"; fi
export OPIK_OTLP_ENDPOINT OPIK_OTLP_HEADERS
echo "==> Opik OTLP endpoint: $OPIK_OTLP_ENDPOINT (project $PROJECT)"

json() { python3 -c "import json,sys; d=json.load(sys.stdin); print(d$1)"; }

# --- 1. Start n8n ------------------------------------------------------------
echo "==> Building and starting n8n"
docker compose up -d --build

echo -n "==> Waiting for n8n"
for _ in $(seq 1 90); do
  if curl -sf "$N8N_URL/healthz/readiness" >/dev/null 2>&1; then echo " up"; break; fi
  echo -n "."; sleep 2
done
curl -sf "$N8N_URL/healthz/readiness" >/dev/null || { echo "n8n did not come up"; exit 1; }

# --- 2. Owner account + API key ----------------------------------------------
# n8n ties the session cookie to a browser id; a fixed browser-id header stands in for one.
COOKIES="$(mktemp)"; trap 'rm -f "$COOKIES"' EXIT
BROWSER_ID="setup-script"
SETUP_BODY=$(printf '{"email":"%s","firstName":"Demo","lastName":"Judge","password":"%s"}' "$OWNER_EMAIL" "$OWNER_PASSWORD")
LOGIN_BODY=$(printf '{"emailOrLdapLoginId":"%s","password":"%s"}' "$OWNER_EMAIL" "$OWNER_PASSWORD")
AUTHED=""
for _ in $(seq 1 15); do
  if curl -sf -c "$COOKIES" -H 'Content-Type: application/json' -H "browser-id: $BROWSER_ID" \
       -X POST "$N8N_URL/rest/owner/setup" -d "$SETUP_BODY" >/dev/null 2>&1; then AUTHED=yes; break; fi
  if curl -sf -c "$COOKIES" -H 'Content-Type: application/json' -H "browser-id: $BROWSER_ID" \
       -X POST "$N8N_URL/rest/login" -d "$LOGIN_BODY" >/dev/null 2>&1; then AUTHED=yes; break; fi
  sleep 2
done
[ -n "$AUTHED" ] || { echo "could not log in to n8n"; exit 1; }

echo "==> Minting an n8n API key"
API_KEY=$(curl -sf -b "$COOKIES" -H 'Content-Type: application/json' -H "browser-id: $BROWSER_ID" \
  -X POST "$N8N_URL/rest/api-keys" \
  -d "{\"label\":\"setup-$(date +%s)\",\"expiresAt\":null,\"scopes\":[\"workflow:create\",\"workflow:read\",\"workflow:update\",\"workflow:delete\",\"workflow:list\",\"workflow:activate\",\"workflow:deactivate\",\"credential:create\",\"credential:delete\"]}" \
  | json "['data']['rawApiKey']")

api() { # method path [json-body]
  if [ -n "${3:-}" ]; then
    curl -sf -X "$1" "$N8N_URL/api/v1$2" -H "X-N8N-API-KEY: $API_KEY" -H 'Content-Type: application/json' -d "$3"
  else
    curl -sf -X "$1" "$N8N_URL/api/v1$2" -H "X-N8N-API-KEY: $API_KEY"
  fi
}

# --- 3. OpenAI credential (value from env, never committed) --------------------
echo "==> Creating the OpenAI credential"
CRED_ID=$(api POST /credentials \
  "$(python3 -c 'import json,os; print(json.dumps({"name":"OpenAI (hackathon screening)","type":"openAiApi","data":{"apiKey":os.environ["OPENAI_API_KEY"]}}))')" \
  | json "['id']")

# --- 4. Import + activate the workflow (idempotent) ----------------------------
api GET "/workflows?name=Hackathon%20screening" \
  | python3 -c "import json,sys; [print(w['id']) for w in json.load(sys.stdin).get('data',[])]" \
  | while read -r wid; do api DELETE "/workflows/$wid" >/dev/null; echo "    removed old copy $wid"; done

echo "==> Importing workflow/hackathon-screening.json"
WF_BODY=$(python3 -c 'import json,sys; print(json.dumps(json.load(open("workflow/hackathon-screening.json"))).replace("__OPENAI_CREDENTIAL_ID__", sys.argv[1]))' "$CRED_ID")
WF_ID=$(api POST /workflows "$WF_BODY" | json "['id']")
api POST "/workflows/$WF_ID/activate" "" >/dev/null

echo
echo "Done. n8n UI:     $N8N_URL  (login: $OWNER_EMAIL / $OWNER_PASSWORD)"
echo "Webhook:          $N8N_URL/webhook/hackathon-screening"
echo "Send submissions: ./demo.sh"
