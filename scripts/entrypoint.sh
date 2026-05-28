#!/bin/sh
set -e

if [ "${PROVIDER:-ollama}" = "ollama" ]; then
    BASE_URL="${OLLAMA_BASE_URL:-http://ollama:11434}"
    MODEL="${OLLAMA_MODEL:-llama3.2}"

    printf "[entrypoint] Waiting for Ollama at %s ...\n" "$BASE_URL"
    until curl -sf "$BASE_URL/api/tags" > /dev/null 2>&1; do
        sleep 3
    done

    printf "[entrypoint] Pulling model '%s' (first run may take several minutes)...\n" "$MODEL"
    curl -sf -X POST "$BASE_URL/api/pull" \
        --max-time 600 \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"$MODEL\"}" > /dev/null

    printf "[entrypoint] Model ready.\n"
fi

exec "$@"
