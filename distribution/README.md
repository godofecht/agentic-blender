# Agentic Blender Linux distribution

The `Build Agentic Blender Linux` workflow downloads and verifies the official Blender 4.5.14 LTS Linux x64 binary, adds the in-process Blender add-on, launch scripts, and Python MCP server sources, and publishes a complete portable `.tar.xz` artifact.

This is a fully packaged distribution based on the official Blender binary, **not a locally recompiled Blender source fork**. Blender's version remains 4.5.14.

Unpack, run `./setup-mcp.sh` once (requires Python 3.10+ and internet access), then `./run-agentic-blender.sh`. The launcher generates a token at `~/.config/agentic-blender/bridge-token` (or under `XDG_CONFIG_HOME`).

For your MCP host, set the command to `<unpacked path>/agentic/venv/bin/python`, arguments `["-m", "server.server"]`, and environment `PYTHONPATH=<unpacked path>/agentic`, `AGENTIC_BLENDER_TOKEN=<token file contents>`, `AGENTIC_BLENDER_PORT=8765`. Do not expose the bridge port.

Verify download integrity using the bundled `SHA256SUMS`. The workflow runs the actual Blender binary headlessly and exercises creation, transform, material assignment and deletion before uploading artifacts.

The Blender executable and its bundled dependencies retain their existing licences. Consult Blender's redistributing requirements before distributing modified bundles.
