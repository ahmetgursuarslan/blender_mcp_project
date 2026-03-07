import bpy

def handle_manage_modifier(params: dict) -> dict:
    """POST /api/modifier/manage"""
    name = params.get("object")
    obj = bpy.data.objects.get(name)
    if not obj: return {"status": "error", "message": f"Object '{name}' not found."}

    action = params.get("action")
    
    if action == "add":
        mtype = params.get("modifier_type", "SUBSURF")
        mname = params.get("name", mtype)
        mod = obj.modifiers.new(name=mname, type=mtype)
        props = params.get("properties", {})
        for k, v in props.items():
            if hasattr(mod, k): setattr(mod, k, v)
        return {"status": "success", "data": {"name": mod.name}}
    
    elif action == "remove":
        mod = obj.modifiers.get(params.get("name"))
        if mod:
            obj.modifiers.remove(mod)
            return {"status": "success", "message": f"Modifier '{params.get('name')}' removed."}
        return {"status": "error", "message": "Modifier not found."}

    elif action == "apply":
        mod = obj.modifiers.get(params.get("name"))
        if mod:
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.modifier_apply(modifier=mod.name)
            return {"status": "success", "message": f"Modifier '{mod.name}' applied."}
        return {"status": "error", "message": "Modifier not found."}

    return {"status": "error", "message": f"Unknown action: {action}"}

def handle_manage_constraint(params: dict) -> dict:
    """POST /api/constraint/manage"""
    name = params.get("object")
    obj = bpy.data.objects.get(name)
    if not obj: return {"status": "error", "message": f"Object '{name}' not found."}

    action = params.get("action")
    if action == "add":
        ctype = params.get("constraint_type", "TRACK_TO")
        con = obj.constraints.new(type=ctype)
        if "name" in params: con.name = params["name"]
        props = params.get("properties", {})
        for k, v in props.items():
            if k == "target": v = bpy.data.objects.get(v)
            if hasattr(con, k): setattr(con, k, v)
        return {"status": "success", "data": {"name": con.name}}

    return {"status": "error", "message": f"Unknown action: {action}"}
