"""Run inside Blender to verify in-process addon operations."""
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "blender_addon"))
import agentic_blender as addon

addon.register()
assert addon._dispatch("scene_info", {})["objects"] is not None
obj = addon._dispatch("create_primitive", {"primitive": "CUBE", "name": "AgenticSmoke", "location": [1, 2, 3]})
assert obj["name"] == "AgenticSmoke", obj
obj = addon._dispatch("set_transform", {"name": "AgenticSmoke", "scale": [2, 2, 2]})
assert obj["scale"] == [2, 2, 2], obj
material = addon._dispatch("set_material_color", {"name": "AgenticSmoke", "rgba": [0.1, 0.2, 0.3, 1.0]})
assert material["object"] == "AgenticSmoke"
assert addon._dispatch("delete_object", {"name": "AgenticSmoke"})["deleted"] == "AgenticSmoke"
addon.unregister()
print("Agentic Blender smoke: PASS")
