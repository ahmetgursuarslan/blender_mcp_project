import bpy

def handle_manage_armature(params: dict) -> dict:
    """POST /api/armature/manage"""
    action = params.get("action")
    name = params.get("name", "Armature")
    
    if action == "create":
        bpy.ops.object.armature_add()
        arm = bpy.context.active_object
        arm.name = name
        return {"status": "success", "data": {"name": arm.name}}
    
    elif action == "add_bone":
        arm = bpy.data.objects.get(name)
        if arm and arm.type == 'ARMATURE':
            bpy.context.view_layer.objects.active = arm
            bpy.ops.object.mode_set(mode='EDIT')
            bone = arm.data.edit_bones.new(params.get("bone_name", "Bone"))
            if "head" in params: bone.head = params["head"]
            if "tail" in params: bone.tail = params["tail"]
            bpy.ops.object.mode_set(mode='OBJECT')
            return {"status": "success", "message": f"Bone added to '{name}'."}

    return {"status": "error", "message": f"Unknown action: {action}"}

def handle_manage_weight_paint(params: dict) -> dict:
    """POST /api/weight_paint/manage"""
    obj = bpy.data.objects.get(params.get("object"))
    if not obj or obj.type != 'MESH': return {"status": "error", "message": "Mesh not found."}

    action = params.get("action")
    if action == "auto_weights":
        arm = bpy.data.objects.get(params.get("armature"))
        if arm:
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            arm.select_set(True)
            bpy.context.view_layer.objects.active = arm
            bpy.ops.object.parent_set(type='ARMATURE_AUTO')
            return {"status": "success", "message": "Automatic weights applied."}

    return {"status": "error", "message": f"Unknown action: {action}"}
