import bpy
import base64
from pathlib import Path

def handle_get_render_settings(params: dict) -> dict:
    """GET /api/render/settings"""
    scene = bpy.context.scene
    return {
        "status": "success",
        "data": {
            "engine": scene.render.engine,
            "resolution_x": scene.render.resolution_x,
            "resolution_y": scene.render.resolution_y,
            "samples": getattr(scene.cycles, "samples", 0),
            "output_format": scene.render.image_settings.file_format,
        }
    }

def handle_set_render_settings(params: dict) -> dict:
    """POST /api/render/settings"""
    scene = bpy.context.scene
    if "engine" in params: scene.render.engine = params["engine"]
    if "resolution_x" in params: scene.render.resolution_x = params["resolution_x"]
    if "resolution_y" in params: scene.render.resolution_y = params["resolution_y"]
    if "samples" in params and scene.render.engine == 'CYCLES': scene.cycles.samples = params["samples"]
    if "output_format" in params: scene.render.image_settings.file_format = params["output_format"]
    return {"status": "success", "message": "Render settings updated."}

def handle_render_image(params: dict) -> dict:
    """POST /api/render/image"""
    scene = bpy.context.scene
    path = params.get("filepath", str(Path.home() / "mcp_render.png"))
    scene.render.filepath = path
    
    bpy.ops.render.render(write_still=True)
    
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode('utf-8')
    return {"status": "success", "image_base64": b64, "filepath": path}

def handle_viewport_screenshot(params: dict) -> dict:
    """POST /api/render/screenshot"""
    tmp = str(Path.home() / "mcp_viewport.png")
    bpy.context.scene.render.filepath = tmp
    try:
        bpy.ops.render.opengl(write_still=True)
        with open(tmp, "rb") as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')
        Path(tmp).unlink(missing_ok=True)
        return {"status": "success", "image_base64": b64}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def handle_manage_camera(params: dict) -> dict:
    """POST /api/render/camera"""
    action = params.get("action")
    name = params.get("name", "Camera")
    
    if action == "create":
        bpy.ops.object.camera_add()
        cam = bpy.context.active_object
        cam.name = name
        if "location" in params: cam.location = params["location"]
        if "rotation" in params: cam.rotation_euler = params["rotation"]
        if "lens" in params: cam.data.lens = params["lens"]
        return {"status": "success", "data": {"name": cam.name}}
    
    elif action == "set_active":
        cam = bpy.data.objects.get(name)
        if cam and cam.type == 'CAMERA':
            bpy.context.scene.camera = cam
            return {"status": "success", "message": f"Camera '{name}' set as active."}
        return {"status": "error", "message": "Camera not found."}

    return {"status": "error", "message": f"Unknown action: {action}"}

def handle_manage_light(params: dict) -> dict:
    """POST /api/render/light"""
    action = params.get("action")
    ltype = params.get("light_type", "POINT")
    name = params.get("name", "Light")
    
    if action == "create":
        bpy.ops.object.light_add(type=ltype)
        light = bpy.context.active_object
        light.name = name
        if "location" in params: light.location = params["location"]
        if "energy" in params: light.data.energy = params["energy"]
        if "color" in params: light.data.color = params["color"]
        return {"status": "success", "data": {"name": light.name}}

    return {"status": "error", "message": f"Unknown action: {action}"}
