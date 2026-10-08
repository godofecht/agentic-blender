# Agentic Blender

An MCP-native control layer for **Blender**, consisting of an in-process Blender add-on and a standards-based MCP server. This is the first working foundation for a dedicated Blender distribution, **not yet a compiled fork or binary release**.

## Architecture

```text
MCP host (Claude Desktop, Cursor, etc.)
        | stdio / MCP
        v
agentic_blender/server.py  (Python 3.10+, external process)
        | authenticated JSON-lines over 127.0.0.1 TCP
        v
Blender add-on (socket thread -> queue -> bpy.app.timers main thread)
        |
        v
Blender bpy scene
```

Operations are explicitly allowlisted; there is no arbitrary Python execution tool. Requests time out, only local loopback is bound, and a per-session token is required.

## Install and run

1. Install Blender 4.2+ and enable the add-on from `blender_addon/agentic_blender/__init__.py` using **Edit → Preferences → Add-ons → Install from Disk** (or copy the `agentic_blender` directory into a Blender scripts/addons directory and enable it).
2. In the **3D Viewport → Sidebar → Agentic** panel, click **Generate token** then **Start bridge**. Copy the displayed token into the local MCP environment variable.
3. On your system's Python 3.10+ install, run `python -m pip install -e .` from this repository.
4. Configure your MCP host's stdio server using the example below (replace paths and token):

```json
{
  "mcpServers": {
    "agentic-blender": {
      "command": "python",
      "args": ["-m", "agentic_blender.server"],
      "env": {
        "AGENTIC_BLENDER_TOKEN": "TOKEN_FROM_BLENDER",
        "AGENTIC_BLENDER_HOST": "127.0.0.1",
        "AGENTIC_BLENDER_PORT": "8765"
      }
    }
  }
}
```

The bridge must be running within Blender before tools can connect. The host's `python` must be the environment in which `mcp` is installed.

## Available MCP tools

`scene_info` returns object names, types, transforms and current selection.
`create_primitive` creates a cube, sphere, cylinder, cone, torus or plane.
`set_transform` sets an object's location, rotation (Euler radians) or scale.
`delete_object` removes a named object.
`set_material_color` assigns or updates a simple Principled BSDF color material.

## Development

Run `python -m unittest discover -s tests -v` for transport protocol unit tests without Blender. Use `python -m compileall -q agentic_blender blender_addon tests` for syntax checks. Integration testing requires a live Blender installation and is not covered by the protocol unit tests.

## Security

The socket binds only to `127.0.0.1`, requires a token, and serves a fixed set of supported operations. Do not expose it through a proxy, tunnel, or port-forwarding arrangement. Treat MCP clients as capable of changing the open Blender scene. For untrusted sessions work on a disposable Blender file.

## Roadmap

Embed the MCP host lifecycle in a Blender-specific launcher, offer extension bundles/installers for macOS/Linux/Windows, package CI and signed releases, add typed asset import and rendering with path confinement, undo checkpoints, progress, notifications, and a full Blender-source distribution build pipeline. Blender remains available under its applicable GPL license; redistributions must comply with Blender and dependency licensing.
