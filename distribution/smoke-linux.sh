#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT=".cache/agentic-blender"
test -x "$ROOT/blender"
test -f "$ROOT/4.5/scripts/addons/agentic_blender/__init__.py"
test -f "$ROOT/agentic/server/server.py"
test -s dist/agentic-blender-4.5.14-linux-x64.tar.xz
"$ROOT/blender" -b --factory-startup --python distribution/smoke_blender.py
echo "Blender binary and Agentic addon smoke test passed"
