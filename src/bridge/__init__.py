"""
Elite MCP Bridge v2.0 — Modular Blender Addon
RESTful HTTP bridge for external MCP servers.
"""

bl_info = {
    "name": "Elite MCP Bridge v2",
    "author": "Antigravity AI",
    "version": (2, 5, 0),
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
import traceback
import atexit
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

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
}

ROUTE_REGISTRY = {}

def _ensure_routes():
    global ROUTE_REGISTRY
    if ROUTE_REGISTRY: return
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

class MCPBridgeRequestHandler(BaseHTTPRequestHandler):
    def _send_response(self, status, payload):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode('utf-8'))

    def _check_auth(self):
        auth_header = self.headers.get('Authorization')
        if not auth_header or auth_header != f"Bearer {SECURITY_TOKEN}":
            self._send_response(403, {"status": "error", "message": "Unauthorized"})
            return False
        return True

    def do_GET(self):
        if not self._check_auth(): return
        parsed = urlparse(self.path)
        if parsed.path == '/ping': self._send_response(200, {"status": "success", "message": "pong"})
        elif parsed.path == '/state':
            res_q = queue.Queue()
            execution_queue.put({"type": "state", "result_queue": res_q})
            self._send_response(200, res_q.get(timeout=10))
        elif parsed.path == '/screenshot':
            res_q = queue.Queue()
            execution_queue.put({"type": "route", "tool": "viewport_screenshot", "params": {}, "result_queue": res_q})
            self._send_response(200, res_q.get(timeout=120))

    def do_POST(self):
        if not self._check_auth(): return
        parsed = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        body = json.loads(post_data.decode('utf-8'))

        res_q = queue.Queue()
        if parsed.path == '/execute':
            is_safe, err = validate_code(body.get("code", ""))
            if not is_safe:
                self._send_response(403, {"status": "error", "message": err})
                return
            execution_queue.put({"type": "execute", "code": body["code"], "result_queue": res_q})
        elif parsed.path == '/api':
            execution_queue.put({"type": "route", "tool": body["tool"], "params": body.get("params", {}), "result_queue": res_q})
        
        self._send_response(200, res_q.get(timeout=120))

def process_execution_queue():
    try:
        task = execution_queue.get_nowait()
        t_type = task["type"]
        res_q = task["result_queue"]
        if t_type == "execute":
            try:
                old_stdout = sys.stdout
                sys.stdout = captured = io.StringIO()
                try:
                    exec(task["code"], persistent_globals)
                    output = captured.getvalue()
                    res_q.put({"status": "success", "message": "Executed.", "output": output})
                finally:
                    sys.stdout = old_stdout
            except Exception as e:
                if 'old_stdout' in locals(): sys.stdout = old_stdout
                res_q.put({"status": "error", "message": str(e), "traceback": traceback.format_exc()})
        elif t_type == "state":
            try:
                active = bpy.context.view_layer.objects.active
                res_q.put({"status": "success", "data": {"active_object": active.name if active else None}})
            except Exception as e: res_q.put({"status": "error", "message": str(e)})
        elif t_type == "route":
            _ensure_routes()
            handler = ROUTE_REGISTRY.get(task["tool"])
            if handler: res_q.put(handler(task["params"]))
            else: res_q.put({"status": "error", "message": "Not found"})
    except queue.Empty: pass
    return 0.1

def cleanup_server():
    global httpd
    if httpd: httpd.server_close()
    if LOCK_FILE.exists(): LOCK_FILE.unlink()

def start_server_in_thread():
    global httpd, SECURITY_TOKEN
    SECURITY_TOKEN = str(uuid.uuid4())
    port = None
    for p in range(5000, 5011):
        try:
            httpd = HTTPServer(('127.0.0.1', p), MCPBridgeRequestHandler)
            port = p
            break
        except OSError:
            continue
    if port is None:
        print("[MCP Bridge] FATAL: Could not bind to any port in range 5000-5010")
        return
    with open(LOCK_FILE, "w") as f: json.dump({"port": port, "token": SECURITY_TOKEN}, f)
    print(f"[MCP Bridge] Server started on port {port}")
    httpd.serve_forever()

def register():
    bpy.app.timers.register(process_execution_queue)
    threading.Thread(target=start_server_in_thread, daemon=True).start()
    atexit.register(cleanup_server)

def unregister():
    bpy.app.timers.unregister(process_execution_queue)
    cleanup_server()

if __name__ == "__main__": register()
