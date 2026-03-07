import bpy
import math


def handle_manage_armature(params: dict) -> dict:
    """Full rigging: create/add_bone/remove_bone/list_bones/rename_bone/set_bone_parent/set_pose/reset_pose/set_ik/parent_mesh."""
    action = params.get("action")
    name = params.get("name", "Armature")

    if action == "create":
        loc = tuple(params.get("location", (0, 0, 0)))
        bpy.ops.object.armature_add(location=loc)
        arm = bpy.context.active_object
        arm.name = name
        arm.data.name = name
        return {"status": "success", "data": {"name": arm.name}}

    elif action == "add_bone":
        arm = bpy.data.objects.get(name)
        if not arm or arm.type != 'ARMATURE':
            return {"status": "error", "message": f"Armature '{name}' not found."}
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode='EDIT')
        try:
            bone_name = params.get("bone_name", "Bone")
            bone = arm.data.edit_bones.new(bone_name)
            if "head" in params:
                bone.head = tuple(params["head"])
            if "tail" in params:
                bone.tail = tuple(params["tail"])
            else:
                bone.tail = (bone.head[0], bone.head[1], bone.head[2] + 0.5)
            if "parent_bone" in params:
                parent = arm.data.edit_bones.get(params["parent_bone"])
                if parent:
                    bone.parent = parent
                    bone.use_connect = params.get("connected", False)
            if "roll" in params:
                bone.roll = math.radians(params["roll"])
            result_name = bone.name
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')
        return {"status": "success", "data": {"bone_name": result_name}}

    elif action == "remove_bone":
        arm = bpy.data.objects.get(name)
        if not arm or arm.type != 'ARMATURE':
            return {"status": "error", "message": f"Armature '{name}' not found."}
        bone_name = params.get("bone_name")
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode='EDIT')
        try:
            bone = arm.data.edit_bones.get(bone_name)
            if bone:
                arm.data.edit_bones.remove(bone)
            else:
                return {"status": "error", "message": f"Bone '{bone_name}' not found."}
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')
        return {"status": "success", "message": f"Bone '{bone_name}' removed."}

    elif action == "list_bones":
        arm = bpy.data.objects.get(name)
        if not arm or arm.type != 'ARMATURE':
            return {"status": "error", "message": f"Armature '{name}' not found."}
        bones = []
        for bone in arm.data.bones:
            bones.append({
                "name": bone.name,
                "head": list(bone.head_local),
                "tail": list(bone.tail_local),
                "parent": bone.parent.name if bone.parent else None,
                "connected": bone.use_connect,
                "children": [c.name for c in bone.children],
                "length": round(bone.length, 4),
            })
        return {"status": "success", "data": bones}

    elif action == "rename_bone":
        arm = bpy.data.objects.get(name)
        if not arm or arm.type != 'ARMATURE':
            return {"status": "error", "message": f"Armature '{name}' not found."}
        bone_name = params.get("bone_name")
        new_name = params.get("new_name")
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode='EDIT')
        try:
            bone = arm.data.edit_bones.get(bone_name)
            if bone:
                bone.name = new_name
            else:
                return {"status": "error", "message": f"Bone '{bone_name}' not found."}
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')
        return {"status": "success", "message": f"Bone renamed to '{new_name}'."}

    elif action == "set_bone_parent":
        arm = bpy.data.objects.get(name)
        if not arm or arm.type != 'ARMATURE':
            return {"status": "error", "message": f"Armature '{name}' not found."}
        bone_name = params.get("bone_name")
        parent_bone = params.get("parent_bone")
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode='EDIT')
        try:
            bone = arm.data.edit_bones.get(bone_name)
            parent = arm.data.edit_bones.get(parent_bone) if parent_bone else None
            if bone:
                bone.parent = parent
                bone.use_connect = params.get("connected", False)
            else:
                return {"status": "error", "message": f"Bone '{bone_name}' not found."}
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')
        return {"status": "success", "message": f"Parent set for bone '{bone_name}'."}

    elif action == "set_pose":
        arm = bpy.data.objects.get(name)
        if not arm or arm.type != 'ARMATURE':
            return {"status": "error", "message": f"Armature '{name}' not found."}
        bone_name = params.get("bone_name")
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode='POSE')
        try:
            pbone = arm.pose.bones.get(bone_name)
            if not pbone:
                return {"status": "error", "message": f"Pose bone '{bone_name}' not found."}
            if "location" in params:
                pbone.location = tuple(params["location"])
            if "rotation" in params:
                rot = params["rotation"]
                pbone.rotation_euler = tuple(rot)
            if "scale" in params:
                pbone.scale = tuple(params["scale"])
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')
        return {"status": "success", "message": f"Pose set for bone '{bone_name}'."}

    elif action == "reset_pose":
        arm = bpy.data.objects.get(name)
        if not arm or arm.type != 'ARMATURE':
            return {"status": "error", "message": f"Armature '{name}' not found."}
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode='POSE')
        try:
            for pbone in arm.pose.bones:
                pbone.location = (0, 0, 0)
                pbone.rotation_euler = (0, 0, 0)
                pbone.rotation_quaternion = (1, 0, 0, 0)
                pbone.scale = (1, 1, 1)
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')
        return {"status": "success", "message": "Pose reset."}

    elif action == "set_ik":
        arm = bpy.data.objects.get(name)
        if not arm or arm.type != 'ARMATURE':
            return {"status": "error", "message": f"Armature '{name}' not found."}
        bone_name = params.get("bone_name")
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode='POSE')
        try:
            pbone = arm.pose.bones.get(bone_name)
            if not pbone:
                return {"status": "error", "message": f"Bone '{bone_name}' not found."}
            ik = pbone.constraints.new('INVERSE_KINEMATICS')
            if "ik_target" in params:
                target = bpy.data.objects.get(params["ik_target"])
                if target:
                    ik.target = target
            if "chain_length" in params:
                ik.chain_count = params["chain_length"]
            if "pole_target" in params:
                pole = bpy.data.objects.get(params["pole_target"])
                if pole:
                    ik.pole_target = pole
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')
        return {"status": "success", "message": f"IK constraint added to '{bone_name}'."}

    elif action == "parent_mesh":
        arm = bpy.data.objects.get(name)
        mesh_name = params.get("mesh")
        mesh_obj = bpy.data.objects.get(mesh_name)
        if not arm or arm.type != 'ARMATURE':
            return {"status": "error", "message": f"Armature '{name}' not found."}
        if not mesh_obj:
            return {"status": "error", "message": f"Mesh '{mesh_name}' not found."}

        method = params.get("method", "ARMATURE_AUTO")
        bpy.ops.object.select_all(action='DESELECT')
        mesh_obj.select_set(True)
        arm.select_set(True)
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.parent_set(type=method)
        return {"status": "success", "message": f"Mesh '{mesh_name}' parented to armature '{name}' with {method}."}

    return {"status": "error", "message": f"Unknown armature action: {action}"}


def handle_manage_weight_paint(params: dict) -> dict:
    """Weight painting: auto_weights/assign_vertex_group/normalize/clean/get_weights/list_groups/remove_group."""
    obj_name = params.get("object")
    obj = bpy.data.objects.get(obj_name)
    if not obj or obj.type != 'MESH':
        return {"status": "error", "message": f"Mesh '{obj_name}' not found."}

    action = params.get("action")

    if action == "auto_weights":
        arm_name = params.get("armature")
        arm = bpy.data.objects.get(arm_name)
        if not arm or arm.type != 'ARMATURE':
            return {"status": "error", "message": f"Armature '{arm_name}' not found."}
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        arm.select_set(True)
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.parent_set(type='ARMATURE_AUTO')
        return {"status": "success", "message": "Automatic weights applied."}

    elif action == "assign_vertex_group":
        group_name = params.get("group")
        vertices = params.get("vertices", [])
        weight = params.get("weight", 1.0)
        vg = obj.vertex_groups.get(group_name)
        if not vg:
            vg = obj.vertex_groups.new(name=group_name)
        vg.add(vertices, weight, 'REPLACE')
        return {"status": "success", "message": f"Vertices assigned to group '{group_name}'."}

    elif action == "normalize":
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
        try:
            bpy.ops.object.vertex_group_normalize_all()
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')
        return {"status": "success", "message": "Vertex groups normalized."}

    elif action == "clean":
        threshold = params.get("threshold", 0.01)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
        try:
            bpy.ops.object.vertex_group_clean(group_select_mode='ALL', limit=threshold)
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')
        return {"status": "success", "message": "Vertex groups cleaned."}

    elif action == "get_weights":
        group_name = params.get("group")
        vg = obj.vertex_groups.get(group_name)
        if not vg:
            return {"status": "error", "message": f"Vertex group '{group_name}' not found."}
        weights = []
        for v in obj.data.vertices:
            try:
                w = vg.weight(v.index)
                if w > 0.001:
                    weights.append({"vertex": v.index, "weight": round(w, 4)})
            except RuntimeError:
                pass
        return {"status": "success", "data": weights}

    elif action == "list_groups":
        groups = [{"name": g.name, "index": g.index} for g in obj.vertex_groups]
        return {"status": "success", "data": groups}

    elif action == "remove_group":
        group_name = params.get("group")
        vg = obj.vertex_groups.get(group_name)
        if vg:
            obj.vertex_groups.remove(vg)
            return {"status": "success", "message": f"Vertex group '{group_name}' removed."}
        return {"status": "error", "message": f"Vertex group '{group_name}' not found."}

    return {"status": "error", "message": f"Unknown weight_paint action: {action}"}
