# Bridge Addon Guide

> Installation, configuration, and internals of the **Elite MCP Bridge v2** Blender Addon.

---

## Overview

The Elite MCP Bridge v2 is a **multi-file Blender addon** that creates a secure HTTP REST server inside Blender's background thread. This server receives commands from the MCP Server and executes them on Blender's main thread via a queue-based architecture.

---

## Installation

### Automated (Recommended)
```cmd
> install_bridge.bat
```
This script copies the addon files to:
```
%APPDATA%\Blender Foundation\Blender\5.0\scripts\addons\elite_mcp_bridge_v2\
```

### Manual
1. Copy the entire `src/bridge/` directory to the Blender addons path:
   ```
   C:\Users\{username}\AppData\Roaming\Blender Foundation\Blender\5.0\scripts\addons\elite_mcp_bridge_v2\
   ```
2. Ensure all files are present (15 Python modules).

### Activation
1. Open Blender 5.0
2. Go to **Edit > Preferences > Add-ons**
3. Search for `"Elite MCP Bridge v2"`
4. Enable the checkbox
5. The addon will start an HTTP server on port 5000+

---

## Addon Structure

```
elite_mcp_bridge_v2/
├── __init__.py              # Addon lifecycle, HTTP server, request handler
├── security.py              # AST-based code validator
├── routes_scene.py          # Scene, objects, collections
├── routes_material.py       # Materials, shader nodes
├── routes_mesh.py           # BMesh operations
├── routes_modifier.py       # Modifier CRUD
├── routes_render.py         # Render, camera, lights
├── routes_animation.py      # Keyframes, timeline, NLA
├── routes_file.py           # File I/O, import/export
├── routes_world.py          # World, HDRI, sky
├── routes_armature.py       # Armature, bones, weights
├── routes_uv.py             # UV, images, bake
├── routes_geometry_nodes.py # GeoNodes, node groups
├── routes_curves.py         # Curves, text, grease pencil
└── routes_advanced.py       # Shape keys, drivers, compositor, physics
```

---

## How It Works

### 1. Server Startup
When the addon is enabled, `register()` is called:
1. A random security token is generated
2. A lock file is written to `~/.blender_mcp_lock` with `{"port": 5000, "token": "..."}`
3. An HTTP server (`MCPBridgeRequestHandler`) starts in a background thread
4. A `bpy.app.timers` callback (`process_execution_queue`) is registered

### 2. Request Handling
```
HTTP Request → Background Thread → execution_queue → Main Thread Timer → bpy execution
```

All Blender API calls (`bpy.*`) must run on the main thread. The addon:
1. Receives HTTP requests on a **background thread**
2. Enqueues the operation with a `threading.Event`
3. The **main thread timer** dequeues and executes the operation
4. Sets a `result` attribute and signals the event
5. The background thread reads the result and sends the HTTP response

### 3. Route Registry
Each `routes_*.py` module registers its handlers in the global `ROUTE_REGISTRY`:
```python
# In routes_scene.py
ROUTE_REGISTRY["manage_object"] = handle_manage_object
ROUTE_REGISTRY["get_scene_hierarchy"] = handle_get_scene_hierarchy
```

### 4. Security
- **Bearer Token**: Every request must include `Authorization: Bearer {token}`
- **AST Checker**: For `execute_blender_code`, the code is parsed through `security.py` which blocks dangerous imports
- **Undo Push**: Before each code execution, `bpy.ops.ed.undo_push()` is called

---

## Configuration

### Port Selection
The addon defaults to port 5000. If occupied, it increments up to 5010.

### Lock File
Located at `~/.blender_mcp_lock`:
```json
{
  "port": 5000,
  "token": "a8f3b2c1-d4e5-6789-abcd-ef0123456789"
}
```

### Allowed Python Modules (Sandbox)
| Module | Available | Usage |
|--------|:---------:|-------|
| `bpy` | ✅ | Full Blender API |
| `math` | ✅ | Standard math library |
| `bmesh` | ✅ | Advanced mesh editing |
| `mathutils` | ✅ | Vector, Matrix, Euler, Quaternion |
| `os`, `sys` | ❌ | Blocked by AST checker |
| `subprocess` | ❌ | Blocked by AST checker |
| `socket`, `urllib` | ❌ | Blocked by AST checker |
| `eval`, `exec`, `open` | ❌ | Blocked by AST checker |

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Addon not found in Blender | Wrong install path | Verify files are in `%APPDATA%\Blender Foundation\Blender\5.0\scripts\addons\elite_mcp_bridge_v2\` |
| "No module named 'bridge'" | Missing `__init__.py` or wrong folder name | Re-run `install_bridge.bat` |
| Duplicate addon entries | Installed in both `addons` and `addons_core` | Remove from `addons_core` |
| Port already in use | Previous Blender instance still running | Close all Blender instances, delete `~/.blender_mcp_lock` |
| Token mismatch (403) | Stale lock file | Restart Blender addon |
