import bpy

def handle_get_animation_info(params: dict) -> dict:
    """GET /api/animation/info"""
    scene = bpy.context.scene
    return {
        "status": "success", 
        "data": {
            "fps": scene.render.fps,
            "frame_start": scene.frame_start,
            "frame_end": scene.frame_end,
            "frame_current": scene.frame_current,
        }
    }

def handle_manage_keyframes(params: dict) -> dict:
    """POST /api/animation/keyframes"""
    action = params.get("action")
    obj = bpy.data.objects.get(params.get("object"))
    if not obj: return {"status": "error", "message": "Object not found."}

    if action == "insert":
        prop = params.get("property", "location")
        frame = params.get("frame", bpy.context.scene.frame_current)
        obj.keyframe_insert(data_path=prop, frame=frame)
        return {"status": "success", "message": "Keyframe inserted."}
    return {"status": "error", "message": f"Unknown action: {action}"}

def handle_manage_timeline(params: dict) -> dict:
    """POST /api/animation/timeline"""
    action = params.get("action")
    scene = bpy.context.scene
    if action == "set_frame":
        scene.frame_set(params.get("frame", 1))
        return {"status": "success", "message": f"Frame set to {scene.frame_current}"}
    return {"status": "error", "message": f"Unknown action: {action}"}
