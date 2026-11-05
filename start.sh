#!/bin/sh
set -eu
cd "$(dirname "$0")"

# Prefer the GPU-accelerated model if available
if curl -sf http://127.0.0.1:18080/v1/models >/dev/null 2>&1; then
  export HATCH_LLM_URL="http://127.0.0.1:18080/v1/chat/completions"
  echo "Using GPU model on port 18080"
fi

exec python3 scripts/launch.py
