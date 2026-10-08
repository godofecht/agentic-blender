#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
TOKENFILE="${XDG_CONFIG_HOME:-$HOME/.config}/agentic-blender/bridge-token"
mkdir -p "$(dirname "$TOKENFILE")"
chmod 700 "$(dirname "$TOKENFILE")"
if [[ ! -s "$TOKENFILE" ]]; then
  ( umask 077; python3 -c 'import secrets; print(secrets.token_hex(24))' > "$TOKENFILE" )
fi
export AGENTIC_BLENDER_TOKEN="$(cat "$TOKENFILE")"
export AGENTIC_BLENDER_PORT="${AGENTIC_BLENDER_PORT:-8765}"
exec "$HERE/blender" --python "$HERE/agentic/startup.py" "$@"
