"""
Elite MCP Bridge v3.0 — Modular Blender Addon
RESTful HTTP bridge for external MCP servers.
Enhanced with comprehensive state reporting and robust error handling.
"""

bl_info = {
    "name": "Elite MCP Bridge v3",
    "author": "Antigravity AI",
    "version": (3, 0, 0),
    "blender": (4, 0, 0),
    "category": "Development",
}

import bpy
import threading
import queue
import json
import uuid
import sys
import io
import math
import traceback
import atexit
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

# Configuration
LOCK_FILE = Path.home() / ".blender_mcp_lock"
execution_queue = queue.Queue()
httpd = None
SECURITY_TOKEN = ""
persistent_globals = {
    "bpy": bpy,
    "math": __import__("math"),
    "bmesh": __import__("bmesh"),
    "mathutils": __import__("mathutils"),
    "random": __import__("random"),
    "functools": __import__("functools"),
    "itertools": __import__("itertools"),
    "collections": __import__("collections"),
    "Vector": __import__("mathutils").Vector,
    "Euler": __import__("mathutils").Euler,
    "Matrix": __import__("mathutils").Matrix,
    "Quaternion": __import__("mathutils").Quaternion,
}

ROUTE_REGISTRY = {}


def _ensure_routes():
    global ROUTE_REGISTRY
    if ROUTE_REGISTRY:
        return
    try:
        from .routes_scene import handle_scene_hierarchy, handle_get_object_details, handle_manage_object, handle_manage_collection
        from .routes_material import handle_get_materials_list, handle_get_material_details, handle_manage_material, handle_manage_shader_nodes
        from .routes_modifier import handle_manage_modifier, handle_manage_constraint
        from .routes_render import handle_get_render_settings, handle_set_render_settings, handle_render_image, handle_viewport_screenshot, handle_manage_camera, handle_manage_light
        from .routes_animation import handle_get_animation_info, handle_manage_keyframes, handle_manage_timeline
        from .routes_file import handle_manage_file, handle_export_model, handle_import_model
        from .routes_mesh import handle_get_mesh_data, handle_edit_mesh, handle_manage_physics
        from .routes_geometry_nodes import handle_manage_geometry_nodes, handle_manage_node_group
        from .routes_world import handle_manage_world
        from .routes_armature import handle_manage_armature, handle_manage_weight_paint
        from .routes_uv import handle_manage_uv, handle_manage_images, handle_manage_texture_bake
        from .routes_curves import handle_manage_curve, handle_manage_text, handle_manage_grease_pencil
        from .routes_advanced import (
            handle_manage_shape_keys, handle_manage_nla, handle_manage_drivers,
            handle_manage_markers, handle_manage_compositor, handle_manage_view_layer,
            handle_manage_preferences, handle_manage_addons, handle_batch_operations,
            handle_manage_scene_settings, handle_library_link,
            handle_manage_custom_properties, handle_get_scene_statistics
        )

        ROUTE_REGISTRY.update({
            "get_scene_hierarchy": handle_scene_hierarchy,
            "get_object_details": handle_get_object_details,
            "manage_object": handle_manage_object,
            "manage_collection": handle_manage_collection,
            "get_materials_list": handle_get_materials_list,
            "get_material_details": handle_get_material_details,
            "manage_material": handle_manage_material,
            "manage_shader_nodes": handle_manage_shader_nodes,
            "manage_modifier": handle_manage_modifier,
            "manage_constraint": handle_manage_constraint,
            "get_render_settings": handle_get_render_settings,
            "set_render_settings": handle_set_render_settings,
            "render_image": handle_render_image,
            "viewport_screenshot": handle_viewport_screenshot,
            "manage_camera": handle_manage_camera,
            "manage_light": handle_manage_light,
            "get_animation_info": handle_get_animation_info,
            "manage_keyframes": handle_manage_keyframes,
            "manage_timeline": handle_manage_timeline,
            "manage_file": handle_manage_file,
            "export_model": handle_export_model,
            "import_model": handle_import_model,
            "get_mesh_data": handle_get_mesh_data,
            "edit_mesh": handle_edit_mesh,
            "manage_physics": handle_manage_physics,
            "manage_geometry_nodes": handle_manage_geometry_nodes,
            "manage_node_group": handle_manage_node_group,
            "manage_world": handle_manage_world,
            "manage_armature": handle_manage_armature,
            "manage_weight_paint": handle_manage_weight_paint,
            "manage_uv": handle_manage_uv,
            "manage_images": handle_manage_images,
            "manage_texture_bake": handle_manage_texture_bake,
            "manage_curve": handle_manage_curve,
            "manage_text": handle_manage_text,
            "manage_grease_pencil": handle_manage_grease_pencil,
            "manage_shape_keys": handle_manage_shape_keys,
            "manage_nla": handle_manage_nla,
            "manage_drivers": handle_manage_drivers,
            "manage_markers": handle_manage_markers,
            "manage_compositor": handle_manage_compositor,
            "manage_view_layer": handle_manage_view_layer,
            "manage_preferences": handle_manage_preferences,
            "manage_addons": handle_manage_addons,
            "batch_operations": handle_batch_operations,
            "manage_scene_settings": handle_manage_scene_settings,
            "library_link": handle_library_link,
            "manage_custom_properties": handle_manage_custom_properties,
            "get_scene_statistics": handle_get_scene_statistics,
        })
    except Exception as e:
        print(f"[MCP Bridge] Import Error: {e}")
        traceback.print_exc()


from .security import validate_code


def _get_enhanced_state() -> dict:
    """Comprehensive scene state for AI context."""
    try:
        scene = bpy.context.scene
        active = bpy.context.view_layer.objects.active
        selected = bpy.context.selected_objects

        # Object summary
        objects = []
        for obj in scene.objects:
            entry = {
                "name": obj.name,
                "type": obj.type,
                "location": [round(v, 3) for v in obj.location],
                "visible": obj.visible_get(),
            }
            if obj.type == 'MESH' and obj.data:
                entry["vertices"] = len(obj.data.vertices)
                entry["faces"] = len(obj.data.polygons)
                entry["materials"] = [m.name for m in obj.data.materials if m]
                entry["modifiers"] = [m.name for m in obj.modifiers]
            objects.append(entry)

        data = {
            "blender_version": bpy.app.version_string,
            "file_path": bpy.data.filepath or "(unsaved)",
            "scene_name": scene.name,
            "render_engine": scene.render.engine,
            "resolution": f"{scene.render.resolution_x}x{scene.render.resolution_y}",
            "frame_current": scene.frame_current,
            "frame_range": f"{scene.frame_start}-{scene.frame_end}",
            "active_object": active.name if active else None,
            "active_object_type": active.type if active else None,
            "selected_objects": [o.name for o in selected],
            "object_count": len(scene.objects),
            "objects": objects,
            "collections": [c.name for c in bpy.data.collections],
            "materials_count": len(bpy.data.materials),
            "total_vertices": sum(len(o.data.vertices) for o in bpy.data.objects if o.type == 'MESH' and o.data),
            "total_faces": sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH' and o.data),
        }
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}


class MCPBridgeRequestHandler(BaseHTTPRequestHandler):
    timeout = 300

    def log_message(self, format, *args):
        """Suppress HTTP logs to avoid console spam."""
        pass

    def _send_response(self, status, payload):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        try:
            self.wfile.write(json.dumps(payload, default=str).encode('utf-8'))
        except Exception:
            self.wfile.write(json.dumps({"status": "error", "message": "Serialization error"}).encode('utf-8'))

    def _check_auth(self):
        auth_header = self.headers.get('Authorization')
        if not auth_header or auth_header != f"Bearer {SECURITY_TOKEN}":
            self._send_response(403, {"status": "error", "message": "Unauthorized"})
            return False
        return True

    def do_GET(self):
        if not self._check_auth():
            return
        parsed = urlparse(self.path)
        if parsed.path == '/ping':
            self._send_response(200, {"status": "success", "message": "pong"})
        elif parsed.path == '/state':
            res_q = queue.Queue()
            execution_queue.put({"type": "state", "result_queue": res_q})
            try:
                result = res_q.get(timeout=30)
                self._send_response(200, result)
            except queue.Empty:
                self._send_response(200, {"status": "error", "message": "Blender UI thread timeout on state."})
        elif parsed.path == '/screenshot':
            res_q = queue.Queue()
            execution_queue.put({"type": "route", "tool": "viewport_screenshot", "params": {}, "result_queue": res_q})
            try:
                self._send_response(200, res_q.get(timeout=120))
            except queue.Empty:
                self._send_response(200, {"status": "error", "message": "Screenshot timeout."})

    def do_POST(self):
        if not self._check_auth():
            return
        parsed = urlparse(self.path)
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data.decode('utf-8'))
        except Exception as e:
            self._send_response(400, {"status": "error", "message": f"Invalid JSON body: {e}"})
            return

        res_q = queue.Queue()

        if parsed.path == '/execute':
            code = body.get("code", "")
            is_safe, err = validate_code(code)
            if not is_safe:
                self._send_response(403, {"status": "error", "message": err})
                return
            execution_queue.put({"type": "execute", "code": code, "result_queue": res_q})
        elif parsed.path == '/api':
            tool = body.get("tool")
            params = body.get("params", {})
            if not tool:
                self._send_response(400, {"status": "error", "message": "Missing 'tool' field in /api request."})
                return
            execution_queue.put({"type": "route", "tool": tool, "params": params, "result_queue": res_q})
        else:
            self._send_response(404, {"status": "error", "message": f"Unknown endpoint: {parsed.path}"})
            return

        try:
            result = res_q.get(timeout=300)
            self._send_response(200, result)
        except queue.Empty:
            self._send_response(200, {"status": "error", "message": "Blender UI thread timed out (300s). The operation may be too heavy."})


def process_execution_queue():
    """Timer callback: process queued tasks on Blender's main thread."""
    try:
        task = execution_queue.get_nowait()
        t_type = task["type"]
        res_q = task["result_queue"]

        if t_type == "execute":
            old_stdout = sys.stdout
            try:
                sys.stdout = captured = io.StringIO()
                exec(task["code"], persistent_globals)
                output = captured.getvalue()
                res_q.put({"status": "success", "message": "Executed.", "output": output})
            except Exception as e:
                res_q.put({"status": "error", "message": str(e), "traceback": traceback.format_exc()})
            finally:
                sys.stdout = old_stdout

        elif t_type == "state":
            res_q.put(_get_enhanced_state())

        elif t_type == "route":
            _ensure_routes()
            handler = ROUTE_REGISTRY.get(task["tool"])
            if handler:
                try:
                    result = handler(task["params"])
                    res_q.put(result)
                except Exception as e:
                    res_q.put({"status": "error", "message": str(e), "traceback": traceback.format_exc()})
            else:
                res_q.put({"status": "error", "message": f"Tool '{task['tool']}' not found in route registry."})

    except queue.Empty:
        pass
    except Exception as e:
        print(f"[MCP Bridge] Queue processing error: {e}")
        traceback.print_exc()

    return 0.05  # 50ms polling interval


def cleanup_server():
    global httpd
    if httpd:
        try:
            httpd.server_close()
        except Exception:
            pass
    if LOCK_FILE.exists():
        try:
            LOCK_FILE.unlink()
        except Exception:
            pass


def start_server_in_thread():
    global httpd, SECURITY_TOKEN
    SECURITY_TOKEN = str(uuid.uuid4())
    port = None
    for p in range(5000, 5021):
        try:
            httpd = HTTPServer(('127.0.0.1', p), MCPBridgeRequestHandler)
            httpd.timeout = 300
            port = p
            break
        except OSError:
            continue
    if port is None:
        print("[MCP Bridge] FATAL: Could not bind to any port in range 5000-5020")
        return
    with open(LOCK_FILE, "w") as f:
        json.dump({"port": port, "token": SECURITY_TOKEN}, f)
    print(f"[MCP Bridge v3] Server started on 127.0.0.1:{port}")
    httpd.serve_forever()


def register():
    # Cleanup stale lockfile from previous session
    if LOCK_FILE.exists():
        try:
            LOCK_FILE.unlink()
        except Exception:
            pass
    bpy.app.timers.register(process_execution_queue)
    threading.Thread(target=start_server_in_thread, daemon=True).start()
    atexit.register(cleanup_server)


def unregister():
    try:
        bpy.app.timers.unregister(process_execution_queue)
    except Exception:
        pass
    cleanup_server()


if __name__ == "__main__":
    register()
