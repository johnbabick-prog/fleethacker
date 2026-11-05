#!/bin/sh
set -eu
cd "$(dirname "$0")"
# Fixed separate data root prevents accidental sharing of the imported MH-60R corpus.
export HATCH_DATA="$PWD/data/team-review"
export HATCH_SHARED_DEMO=1
python3 scripts/seed_shared_demo.py
printf '\nHATCH team review: http://<this-Mac-LAN-IP>:8766\nSame-network access; shared demo records; no authentication.\nUse synthetic uploads only. Stop with Control+C.\n\n'
exec python3 -m uvicorn hatch.app:app --host 0.0.0.0 --port 8766
