#!/usr/bin/env bash
# Build, start the service on :4300, send the scripted questions, stop the service.
# Usage: ./run.sh            (scripted demo, then exit)
#        ./run.sh serve      (leave the service running for your own curl calls)
set -euo pipefail
cd "$(dirname "$0")"

# Load keys from the repo-root .env or a local .env, if present.
for env_file in ../.env .env; do
  if [[ -f "$env_file" ]]; then
    set -a; source "$env_file"; set +a
  fi
done
: "${OPENAI_API_KEY:?Set OPENAI_API_KEY (see .env.example)}"

export OPIK_WORKSPACE="${OPIK_WORKSPACE:-default}"
export OPIK_PROJECT_NAME="${OPIK_PROJECT_NAME:-quarkus-langchain4j-pharmacy-faq}"
# The OTLP endpoint is Opik's API base plus /v1/private/otel.
OPIK_API_BASE="${OPIK_URL_OVERRIDE:-http://localhost:5173/api/}"
export OPIK_OTEL_ENDPOINT="${OPIK_OTEL_ENDPOINT:-${OPIK_API_BASE%/}/v1/private/otel}"

mvn -q -B package -DskipTests
java -jar target/quarkus-app/quarkus-run.jar > target/app.log 2>&1 &
APP_PID=$!
# SIGTERM lets the OpenTelemetry batch processor flush the last spans before the JVM exits.
stop_app() { kill "$APP_PID" 2>/dev/null && wait "$APP_PID" 2>/dev/null || true; }
trap stop_app EXIT

# Wait for the startup log line rather than probing HTTP, so no stray probe request becomes a trace.
for _ in $(seq 1 90); do
  grep -q "Listening on" target/app.log 2>/dev/null && break
  kill -0 "$APP_PID" 2>/dev/null || { cat target/app.log; exit 1; }
  sleep 1
done

if [[ "${1:-demo}" == "serve" ]]; then
  echo "Serving on http://localhost:4300/ask?q=... (Ctrl-C to stop)"
  wait "$APP_PID"
  exit 0
fi

ask() {
  echo "Q: $1"
  printf 'A: '
  curl -sf --get --data-urlencode "q=$1" http://localhost:4300/ask
  printf '\n\n'
}

ask "How should I store the Calmorex syrup once it is open?"
ask "Can I take Lumidine and Ferravel together?"
ask "I take Clotavar. Is Tendrix okay for my back pain?"
ask "What dose of Calmorex should I give my 3 year old?"
ask "Does the pharmacy stock Zentavo for migraines?"

sleep 3   # give the exporter a moment before the trap stops the JVM
