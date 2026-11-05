bl_info = {
    "name": "Agentic Blender",
    "author": "Agentic Blender contributors",
    "version": (0, 1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Agentic",
    "description": "Authenticated local MCP bridge for Blender",
    "category": "3D View",
}

import json
import math
import queue
import secrets
import socket
import threading

import bpy

_WORK = queue.Queue(maxsize=128)
_STOP = threading.Event()
_THREAD = None
_LISTENER = None
_MAX_MESSAGE = 65536
_OPS = {"scene_info", "create_primitive", "set_transform", "delete_object", "set_material_color"}


def _vector(value, length, label):
    if not isinstance(value, list) or len(value) != length:
        raise ValueError(f"{label} must be a list of {length} numbers")
    if any(isinstance(x, bool) or not isinstance(x, (float, int)) or not math.isfinite(x) for x in value):
        raise ValueError(f"{label} must contain finite numbers")
    return value


def _get_object(name):
    if not isinstance(name, str) or not name:
        raise ValueError("An object name is required")
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Object not found: {name}")
    return obj


def _snapshot(obj):
    return {
        "name": obj.name,
        "type": obj.type,
        "location": list(obj.location),
        "rotation": list(obj.rotation_euler),
        "scale": list(obj.scale),
    }


def _dispatch(operation, params):
    if operation == "scene_info":
        return {
            "scene": bpy.context.scene.name,
            "objects": [_snapshot(obj) for obj in bpy.context.scene.objects],
            "selected": [obj.name for obj in bpy.context.selected_objects],
        }

    if operation == "create_primitive":
        primitive = params.get("primitive")
        operations = {
            "CUBE": bpy.ops.mesh.primitive_cube_add,
            "UV_SPHERE": bpy.ops.mesh.primitive_uv_sphere_add,
            "CYLINDER": bpy.ops.mesh.primitive_cylinder_add,
            "CONE": bpy.ops.mesh.primitive_cone_add,
            "TORUS": bpy.ops.mesh.primitive_torus_add,
            "PLANE": bpy.ops.mesh.primitive_plane_add,
        }
        if primitive not in operations:
            raise ValueError("Unsupported primitive")
        location = params.get("location")
        kwargs = {"location": _vector(location, 3, "location")} if location is not None else {}
        operations[primitive](**kwargs)
        obj = bpy.context.object
        name = params.get("name", "")
        if name:
            if not isinstance(name, str) or len(name) > 128:
                raise ValueError("name must be a string up to 128 characters")
            obj.name = name
        return _snapshot(obj)

    if operation == "set_transform":
        obj = _get_object(params.get("name"))
        for key, attribute in (("location", "location"), ("rotation", "rotation_euler"), ("scale", "scale")):
            value = params.get(key)
            if value is not None:
                setattr(obj, attribute, _vector(value, 3, key))
        return _snapshot(obj)

    if operation == "delete_object":
        obj = _get_object(params.get("name"))
        name = obj.name
        bpy.data.objects.remove(obj, do_unlink=True)
        return {"deleted": name}

    if operation == "set_material_color":
        obj = _get_object(params.get("name"))
        if obj.type != "MESH":
            raise ValueError("Materials can only be set on mesh objects")
        rgba = _vector(params.get("rgba"), 4, "rgba")
        if any(v < 0 or v > 1 for v in rgba):
            raise ValueError("RGBA channels must be between 0 and 1")
        mat = bpy.data.materials.new(name=f"Agentic_{obj.name}")
        mat.diffuse_color = rgba
        mat.use_nodes = True
        principled = mat.node_tree.nodes.get("Principled BSDF")
        if principled:
            principled.inputs["Base Color"].default_value = rgba
            principled.inputs["Alpha"].default_value = rgba[3]
        obj.data.materials.clear()
        obj.data.materials.append(mat)
        return {"object": obj.name, "material": mat.name, "rgba": rgba}

    raise ValueError("Unsupported operation")


def _pump():
    for _ in range(32):
        try:
            job = _WORK.get_nowait()
        except queue.Empty:
            break
        operation, params, done, result = job
        try:
            result["value"] = {"ok": True, "result": _dispatch(operation, params)}
        except Exception as error:
            result["value"] = {"ok": False, "error": str(error)}
        finally:
            done.set()
    return None if _STOP.is_set() else 0.05


def _client(connection, token):
    with connection:
        connection.settimeout(16)
        try:
            with connection.makefile("rb") as reader:
                line = reader.readline(_MAX_MESSAGE + 2)
            if len(line) > _MAX_MESSAGE or not line.endswith(b"\n"):
                raise ValueError("Invalid or oversized request")
            message = json.loads(line)
            if not isinstance(message, dict) or not secrets.compare_digest(str(message.get("token", "")), token):
                raise ValueError("Unauthorized")
            operation = message.get("operation")
            if operation not in _OPS:
                raise ValueError("Unsupported operation")
            params = message.get("params")
            if not isinstance(params, dict):
                raise ValueError("params must be an object")
            done = threading.Event()
            result = {}
            _WORK.put((operation, params, done, result), timeout=1)
            if not done.wait(12):
                raise TimeoutError("Blender main thread did not respond")
            response = result["value"]
        except Exception as error:
            response = {"ok": False, "error": str(error)}
        try:
            encoded = json.dumps(response, allow_nan=False).encode("utf-8") + b"\n"
            if len(encoded) > _MAX_MESSAGE:
                encoded = b'{"ok":false,"error":"Response too large"}\n'
            connection.sendall(encoded)
        except OSError:
            pass


def _listen(port, token):
    global _LISTENER
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            _LISTENER = listener
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind(("127.0.0.1", port))
            listener.listen(16)
            listener.settimeout(0.5)
            while not _STOP.is_set():
                try:
                    connection, _ = listener.accept()
                except socket.timeout:
                    continue
                threading.Thread(target=_client, args=(connection, token), daemon=True).start()
    except OSError as error:
        print(f"Agentic Blender bridge error: {error}")
    finally:
        _LISTENER = None


class AGENTIC_OT_token(bpy.types.Operator):
    bl_idname = "agentic.generate_token"
    bl_label = "Generate token"
    bl_description = "Rotate the local bridge secret; restart the bridge after rotation"

    def execute(self, context):
        context.scene.agentic_token = secrets.token_hex(24)
        self.report({"INFO"}, "New token generated; restart bridge if running")
        return {"FINISHED"}


class AGENTIC_OT_start(bpy.types.Operator):
    bl_idname = "agentic.start_bridge"
    bl_label = "Start bridge"

    def execute(self, context):
        global _THREAD
        if _THREAD and _THREAD.is_alive():
            self.report({"INFO"}, "Bridge is already running")
            return {"FINISHED"}
        if not context.scene.agentic_token:
            self.report({"ERROR"}, "Generate a token first")
            return {"CANCELLED"}
        _STOP.clear()
        _THREAD = threading.Thread(
            target=_listen,
            args=(context.scene.agentic_port, context.scene.agentic_token),
            daemon=True,
        )
        _THREAD.start()
        if not bpy.app.timers.is_registered(_pump):
            bpy.app.timers.register(_pump, first_interval=0.05, persistent=True)
        self.report({"INFO"}, "Starting local bridge")
        return {"FINISHED"}


class AGENTIC_OT_stop(bpy.types.Operator):
    bl_idname = "agentic.stop_bridge"
    bl_label = "Stop bridge"

    def execute(self, context):
        _STOP.set()
        if _LISTENER:
            try:
                _LISTENER.close()
            except OSError:
                pass
        self.report({"INFO"}, "Stopping bridge")
        return {"FINISHED"}


class AGENTIC_PT_panel(bpy.types.Panel):
    bl_label = "Agentic Blender"
    bl_idname = "AGENTIC_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Agentic"

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "agentic_port")
        layout.prop(context.scene, "agentic_token", text="Token")
        layout.operator("agentic.generate_token")
        running = _THREAD is not None and _THREAD.is_alive() and not _STOP.is_set()
        layout.label(text="Running" if running else "Stopped")
        layout.operator("agentic.stop_bridge" if running else "agentic.start_bridge")


_CLASSES = (AGENTIC_OT_token, AGENTIC_OT_start, AGENTIC_OT_stop, AGENTIC_PT_panel)


def register():
    bpy.types.Scene.agentic_port = bpy.props.IntProperty(name="Port", default=8765, min=1024, max=65535)
    bpy.types.Scene.agentic_token = bpy.props.StringProperty(name="Token", default="")
    for cls in _CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    _STOP.set()
    if _LISTENER:
        try:
            _LISTENER.close()
        except OSError:
            pass
    if bpy.app.timers.is_registered(_pump):
        bpy.app.timers.unregister(_pump)
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.agentic_token
    del bpy.types.Scene.agentic_port
