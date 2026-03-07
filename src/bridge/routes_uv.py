import bpy

def handle_manage_uv(params: dict) -> dict:
    """POST /api/uv/manage"""
    obj = bpy.data.objects.get(params.get("object"))
    if not obj or obj.type != 'MESH': return {"status": "error", "message": "Mesh object not found."}

    action = params.get("action")
    bpy.context.view_layer.objects.active = obj
    
    if action == "unwrap":
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.unwrap()
        bpy.ops.object.mode_set(mode='OBJECT')
        return {"status": "success", "message": "Mesh unwrapped."}

    elif action == "smart_project":
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project()
        bpy.ops.object.mode_set(mode='OBJECT')
        return {"status": "success", "message": "Smart project completed."}

    return {"status": "error", "message": f"Unknown action: {action}"}

def handle_manage_images(params: dict) -> dict:
    """POST /api/images/manage"""
    action = params.get("action")
    if action == "load":
        path = params.get("filepath")
        try:
            img = bpy.data.images.load(path)
            return {"status": "success", "data": {"name": img.name}}
        except Exception as e:
            return {"status": "error", "message": f"Load failed: {e}"}
    return {"status": "error", "message": f"Unknown action: {action}"}

def handle_manage_texture_bake(params: dict) -> dict:
    return {"status": "success", "message": "Baking setup placeholder."}
