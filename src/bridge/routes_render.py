import bpy
import base64
import math
from pathlib import Path


def handle_get_render_settings(params: dict) -> dict:
    """Full render settings."""
    scene = bpy.context.scene
    r = scene.render
    data = {
        "engine": r.engine,
        "resolution_x": r.resolution_x,
        "resolution_y": r.resolution_y,
        "resolution_percentage": r.resolution_percentage,
        "output_format": r.image_settings.file_format,
        "color_mode": r.image_settings.color_mode,
        "film_transparent": r.film_transparent,
        "fps": r.fps,
        "frame_start": scene.frame_start,
        "frame_end": scene.frame_end,
    }
    if r.engine == 'CYCLES':
        data["cycles"] = {
            "samples": scene.cycles.samples,
            "preview_samples": scene.cycles.preview_samples,
            "use_denoising": scene.cycles.use_denoising,
            "device": scene.cycles.device,
        }
    elif r.engine == 'BLENDER_EEVEE_NEXT':
        data["eevee"] = {
            "samples": getattr(scene.eevee, 'taa_render_samples', 64),
        }
    # Color Management
    data["color_management"] = {
        "view_transform": scene.view_settings.view_transform,
        "look": scene.view_settings.look,
        "exposure": scene.view_settings.exposure,
        "gamma": scene.view_settings.gamma,
    }
    return {"status": "success", "data": data}


def handle_set_render_settings(params: dict) -> dict:
    """Configure render engine, resolution, samples, format, etc."""
    scene = bpy.context.scene
    r = scene.render

    if "engine" in params:
        r.engine = params["engine"]
    if "resolution_x" in params:
        r.resolution_x = params["resolution_x"]
    if "resolution_y" in params:
        r.resolution_y = params["resolution_y"]
    if "film_transparent" in params:
        r.film_transparent = params["film_transparent"]
    if "output_format" in params:
        r.image_settings.file_format = params["output_format"]
    if "fps" in params:
        r.fps = params["fps"]

    # Cycles-specific
    cycles_params = params.get("cycles", {})
    if r.engine == 'CYCLES':
        if "samples" in params:
            scene.cycles.samples = params["samples"]
        for k, v in cycles_params.items():
            if hasattr(scene.cycles, k):
                setattr(scene.cycles, k, v)

    # EEVEE-specific
    eevee_params = params.get("eevee", {})
    for k, v in eevee_params.items():
        if hasattr(scene.eevee, k):
            setattr(scene.eevee, k, v)

    # Color Management
    cm_params = params.get("color_management", {})
    for k, v in cm_params.items():
        if hasattr(scene.view_settings, k):
            setattr(scene.view_settings, k, v)

    return {"status": "success", "message": "Render settings updated."}


def handle_render_image(params: dict) -> dict:
    """Full render → base64 PNG."""
    scene = bpy.context.scene
    path = params.get("filepath", str(Path.home() / "mcp_render.png"))
    fmt = params.get("format", "PNG")

    scene.render.filepath = path
    scene.render.image_settings.file_format = fmt

    try:
        bpy.ops.render.render(write_still=True)
        with open(bpy.path.abspath(scene.render.filepath), "rb") as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')
        return {"status": "success", "image_base64": b64, "filepath": path}
    except Exception as e:
        return {"status": "error", "message": f"Render failed: {e}"}


def handle_viewport_screenshot(params: dict) -> dict:
    """Capture viewport as base64 PNG."""
    tmp = str(Path.home() / "mcp_viewport.png")
    old_path = bpy.context.scene.render.filepath
    bpy.context.scene.render.filepath = tmp
    try:
        bpy.ops.render.opengl(write_still=True)
        with open(tmp, "rb") as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')
        Path(tmp).unlink(missing_ok=True)
        return {"status": "success", "image_base64": b64}
    except Exception as e:
        return {"status": "error", "message": f"Screenshot failed: {e}"}
    finally:
        bpy.context.scene.render.filepath = old_path


def handle_manage_camera(params: dict) -> dict:
    """Camera CRUD: create/modify/set_active/look_at."""
    action = params.get("action")
    name = params.get("name", "Camera")

    if action == "create":
        bpy.ops.object.camera_add()
        cam = bpy.context.active_object
        cam.name = name
        if "location" in params:
            cam.location = tuple(params["location"])
        if "rotation" in params:
            cam.rotation_euler = tuple(params["rotation"])
        if "lens" in params:
            cam.data.lens = params["lens"]
        if "clip_start" in params:
            cam.data.clip_start = params["clip_start"]
        if "clip_end" in params:
            cam.data.clip_end = params["clip_end"]
        if "dof_enabled" in params:
            cam.data.dof.use_dof = params["dof_enabled"]
        if "aperture_fstop" in params:
            cam.data.dof.aperture_fstop = params["aperture_fstop"]
        return {"status": "success", "data": {"name": cam.name}}

    elif action == "modify":
        cam = bpy.data.objects.get(name)
        if not cam or cam.type != 'CAMERA':
            return {"status": "error", "message": f"Camera '{name}' not found."}
        if "location" in params:
            cam.location = tuple(params["location"])
        if "rotation" in params:
            cam.rotation_euler = tuple(params["rotation"])
        if "lens" in params:
            cam.data.lens = params["lens"]
        if "clip_start" in params:
            cam.data.clip_start = params["clip_start"]
        if "clip_end" in params:
            cam.data.clip_end = params["clip_end"]
        if "dof_enabled" in params:
            cam.data.dof.use_dof = params["dof_enabled"]
        if "aperture_fstop" in params:
            cam.data.dof.aperture_fstop = params["aperture_fstop"]
        return {"status": "success", "message": f"Camera '{name}' modified."}

    elif action == "set_active":
        cam = bpy.data.objects.get(name)
        if cam and cam.type == 'CAMERA':
            bpy.context.scene.camera = cam
            return {"status": "success", "message": f"Camera '{name}' set as active."}
        return {"status": "error", "message": f"Camera '{name}' not found."}

    elif action == "look_at":
        cam = bpy.data.objects.get(name)
        if not cam or cam.type != 'CAMERA':
            return {"status": "error", "message": f"Camera '{name}' not found."}
        target = params.get("target")
        if isinstance(target, str):
            t_obj = bpy.data.objects.get(target)
            if t_obj:
                target_loc = t_obj.matrix_world.translation
            else:
                return {"status": "error", "message": f"Target object '{target}' not found."}
        elif isinstance(target, (list, tuple)):
            from mathutils import Vector
            target_loc = Vector(target)
        else:
            return {"status": "error", "message": "target must be object name or [x,y,z]."}

        from mathutils import Vector
        direction = target_loc - cam.matrix_world.translation
        rot_quat = direction.to_track_quat('-Z', 'Y')
        cam.rotation_euler = rot_quat.to_euler()
        return {"status": "success", "message": f"Camera '{name}' now looking at target."}

    return {"status": "error", "message": f"Unknown camera action: {action}"}


def handle_manage_light(params: dict) -> dict:
    """Light CRUD: create/modify/delete."""
    action = params.get("action")
    ltype = params.get("light_type", "POINT")
    name = params.get("name", "Light")

    if action == "create":
        bpy.ops.object.light_add(type=ltype)
        light = bpy.context.active_object
        light.name = name
        if "location" in params:
            light.location = tuple(params["location"])
        if "rotation" in params:
            light.rotation_euler = tuple(params["rotation"])
        if "energy" in params:
            light.data.energy = params["energy"]
        if "color" in params:
            light.data.color = tuple(params["color"][:3])
        if "size" in params:
            light.data.shadow_soft_size = params["size"]
        if "use_shadow" in params:
            light.data.use_shadow = params["use_shadow"]
        # Spot-specific
        if ltype == "SPOT":
            if "spot_size" in params:
                light.data.spot_size = params["spot_size"]
        # Area-specific
        if ltype == "AREA":
            if "shape" in params:
                light.data.shape = params["shape"]
            if "size" in params:
                light.data.size = params["size"]
        return {"status": "success", "data": {"name": light.name, "type": ltype}}

    elif action == "modify":
        light = bpy.data.objects.get(name)
        if not light or light.type != 'LIGHT':
            return {"status": "error", "message": f"Light '{name}' not found."}
        if "location" in params:
            light.location = tuple(params["location"])
        if "rotation" in params:
            light.rotation_euler = tuple(params["rotation"])
        if "energy" in params:
            light.data.energy = params["energy"]
        if "color" in params:
            light.data.color = tuple(params["color"][:3])
        if "size" in params:
            if light.data.type == 'AREA':
                light.data.size = params["size"]
            else:
                light.data.shadow_soft_size = params["size"]
        if "use_shadow" in params:
            light.data.use_shadow = params["use_shadow"]
        return {"status": "success", "message": f"Light '{name}' modified."}

    elif action == "delete":
        light = bpy.data.objects.get(name)
        if light and light.type == 'LIGHT':
            bpy.data.objects.remove(light, do_unlink=True)
            return {"status": "success", "message": f"Light '{name}' deleted."}
        return {"status": "error", "message": f"Light '{name}' not found."}

    return {"status": "error", "message": f"Unknown light action: {action}"}
