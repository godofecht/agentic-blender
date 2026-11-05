#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 -m venv "$HERE/agentic/venv"
"$HERE/agentic/venv/bin/python" -m pip install --upgrade pip
"$HERE/agentic/venv/bin/python" -m pip install "mcp>=1.28,<3"
echo "MCP host command: $HERE/agentic/venv/bin/python -m server.server"
echo "Set PYTHONPATH=$HERE/agentic and AGENTIC_BLENDER_TOKEN to the token file contents."
