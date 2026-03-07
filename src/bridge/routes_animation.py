import bpy


def handle_get_animation_info(params: dict) -> dict:
    """Animation info: fps, frame range, actions, fcurves."""
    scene = bpy.context.scene
    data = {
        "fps": scene.render.fps,
        "frame_start": scene.frame_start,
        "frame_end": scene.frame_end,
        "frame_current": scene.frame_current,
        "actions": [],
    }

    # Object-specific
    obj_name = params.get("object")
    if obj_name:
        obj = bpy.data.objects.get(obj_name)
        if obj and obj.animation_data and obj.animation_data.action:
            act = obj.animation_data.action
            fcurves = []
            for fc in act.fcurves:
                fcurves.append({
                    "data_path": fc.data_path,
                    "array_index": fc.array_index,
                    "keyframe_count": len(fc.keyframe_points),
                })
            data["object_action"] = {"name": act.name, "fcurves": fcurves}

    # Enumerate all actions
    for act in bpy.data.actions:
        data["actions"].append({
            "name": act.name,
            "frame_range": list(act.frame_range),
            "fcurve_count": len(act.fcurves),
        })

    return {"status": "success", "data": data}


def handle_manage_keyframes(params: dict) -> dict:
    """Keyframe CRUD: insert/delete/read/clear_all."""
    action = params.get("action")
    obj_name = params.get("object")
    obj = bpy.data.objects.get(obj_name)
    if not obj:
        return {"status": "error", "message": f"Object '{obj_name}' not found."}

    prop = params.get("property", "location")
    frame = params.get("frame", bpy.context.scene.frame_current)

    if action == "insert":
        try:
            if "value" in params:
                # Set the value first
                val = params["value"]
                parts = prop.split(".")
                target = obj
                for part in parts[:-1]:
                    target = getattr(target, part)
                if isinstance(val, (list, tuple)):
                    setattr(target, parts[-1], val)
                else:
                    setattr(target, parts[-1], val)

            obj.keyframe_insert(data_path=prop, frame=frame)
            return {"status": "success", "message": f"Keyframe inserted at frame {frame} for '{prop}'."}
        except Exception as e:
            return {"status": "error", "message": f"Keyframe insert failed: {e}"}

    elif action == "delete":
        try:
            obj.keyframe_delete(data_path=prop, frame=frame)
            return {"status": "success", "message": f"Keyframe deleted at frame {frame}."}
        except Exception as e:
            return {"status": "error", "message": f"Keyframe delete failed: {e}"}

    elif action == "read":
        if not obj.animation_data or not obj.animation_data.action:
            return {"status": "success", "data": {"keyframes": []}}
        keyframes = []
        for fc in obj.animation_data.action.fcurves:
            if fc.data_path == prop:
                for kp in fc.keyframe_points:
                    keyframes.append({
                        "frame": kp.co[0],
                        "value": kp.co[1],
                        "array_index": fc.array_index,
                        "interpolation": kp.interpolation,
                    })
        return {"status": "success", "data": {"keyframes": keyframes}}

    elif action == "clear_all":
        if obj.animation_data:
            obj.animation_data_clear()
        return {"status": "success", "message": f"All keyframes cleared from '{obj_name}'."}

    return {"status": "error", "message": f"Unknown keyframes action: {action}"}


def handle_manage_timeline(params: dict) -> dict:
    """Timeline: set_range/set_fps/set_frame/play/stop."""
    action = params.get("action")
    scene = bpy.context.scene

    if action == "set_range":
        if "frame_start" in params:
            scene.frame_start = params["frame_start"]
        if "frame_end" in params:
            scene.frame_end = params["frame_end"]
        return {"status": "success", "message": f"Timeline range: {scene.frame_start}-{scene.frame_end}"}

    elif action == "set_fps":
        if "fps" in params:
            scene.render.fps = params["fps"]
        return {"status": "success", "message": f"FPS set to {scene.render.fps}"}

    elif action == "set_frame":
        frame = params.get("frame", 1)
        scene.frame_set(frame)
        return {"status": "success", "message": f"Frame set to {scene.frame_current}"}

    elif action == "play":
        bpy.ops.screen.animation_play()
        return {"status": "success", "message": "Animation playing."}

    elif action == "stop":
        bpy.ops.screen.animation_cancel()
        return {"status": "success", "message": "Animation stopped."}

    return {"status": "error", "message": f"Unknown timeline action: {action}"}
