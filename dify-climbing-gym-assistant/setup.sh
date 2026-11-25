#!/usr/bin/env bash
# Start Dify (release 1.17.1, vendored in dify-docker/) and configure it with no clicking.
# Safe to re-run: every step checks before it creates.
# Needs: Docker, python3, and OPENAI_API_KEY (shell env or the repo-root .env).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$HERE/dify-docker"

for envfile in "$HERE/../.env" "$HERE/.env"; do
  if [ -f "$envfile" ]; then set -a; . "$envfile"; set +a; fi
done

DIFY_PORT="${DIFY_PORT:-8090}"   # Dify's nginx serves the UI and APIs here

# 1. First run: create dify-docker/.env from the upstream template, plus two overrides.
if [ ! -f "$DOCKER_DIR/.env" ]; then
  cp "$DOCKER_DIR/env.example" "$DOCKER_DIR/.env"
  printf '\n# --- dify-climbing-gym-assistant overrides ---\nCOMPOSE_PROJECT_NAME=dify-climbing-gym-assistant\nEXPOSE_NGINX_PORT=%s\n' "$DIFY_PORT" >> "$DOCKER_DIR/.env"
  echo "Created dify-docker/.env (port $DIFY_PORT)"
fi

# 2. Start the stack. The first run pulls about ten images and takes a few minutes.
echo "Starting Dify..."
docker compose -f "$DOCKER_DIR/docker-compose.yaml" --project-directory "$DOCKER_DIR" up -d

# 3. Admin account, OpenAI plugin + key, app import, Opik tracing, service API key.
DIFY_URL="http://localhost:$DIFY_PORT" python3 "$HERE/configure_dify.py"

echo
echo "Dify UI:  http://localhost:$DIFY_PORT  (login: desk@basaltwall.example / BasaltWall-2026)"
echo "Stop:     docker compose -f dify-docker/docker-compose.yaml --project-directory dify-docker down   (-v also drops the data)"
