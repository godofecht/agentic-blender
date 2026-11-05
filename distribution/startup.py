"""Initialize Agentic Blender in the Blender main thread on launch."""
import os
import sys
from pathlib import Path

import bpy

addon_path = Path(__file__).resolve().parents[1] / "4.5" / "scripts" / "addons"
if str(addon_path) not in sys.path:
    sys.path.insert(0, str(addon_path))

import agentic_blender

if not hasattr(bpy.types.Scene, "agentic_port"):
    agentic_blender.register()

scene = bpy.context.scene
scene.agentic_token = os.environ.get("AGENTIC_BLENDER_TOKEN", "")
scene.agentic_port = int(os.environ.get("AGENTIC_BLENDER_PORT", "8765"))
if scene.agentic_token and not bpy.app.background:
    bpy.ops.agentic.start_bridge()
print("Agentic Blender: addon registered; bridge " + ("active" if not bpy.app.background else "disabled in background mode"))
