import bpy

def handle_scene_hierarchy(params: dict) -> dict:
    """GET /api/scene/hierarchy"""
    include_transform = params.get("include_transform", False)
    max_depth = params.get("max_depth", 10)

    def get_children(obj, depth):
        if depth >= max_depth: return []
        children = []
        for child in obj.children:
            entry = {
                "name": child.name,
                "type": child.type,
                "children": get_children(child, depth + 1)
            }
            if include_transform:
                entry["location"] = list(child.location)
                entry["rotation"] = list(child.rotation_euler)
                entry["scale"] = list(child.scale)
            children.append(entry)
        return children

    # Root level (objects with no parent)
    root_objects = [o for o in bpy.context.scene.objects if not o.parent]
    hierarchy = []
    for obj in root_objects:
        entry = {
            "name": obj.name,
            "type": obj.type,
            "children": get_children(obj, 1)
        }
        if include_transform:
            entry["location"] = list(obj.location)
            entry["rotation"] = list(obj.rotation_euler)
            entry["scale"] = list(obj.scale)
        hierarchy.append(entry)

    return {"status": "success", "data": hierarchy}

def handle_get_object_details(params: dict) -> dict:
    """GET /api/object/details"""
    name = params.get("name")
    obj = bpy.data.objects.get(name)
    if not obj:
        return {"status": "error", "message": f"Object '{name}' not found."}

    data = {
        "name": obj.name,
        "type": obj.type,
        "location": list(obj.location),
        "rotation": list(obj.rotation_euler),
        "scale": list(obj.scale),
    }

    if params.get("include_modifiers", False):
        data["modifiers"] = [{"name": m.name, "type": m.type, "show": m.show_viewport} for m in obj.modifiers]
    
    if params.get("include_materials", False) and obj.type == 'MESH':
        data["materials"] = [m.name for m in obj.data.materials if m]

    return {"status": "success", "data": data}

def handle_manage_object(params: dict) -> dict:
    """POST /api/object/manage"""
    action = params.get("action")
    name = params.get("name")
    
    if action == "create":
        prim_type = params.get("primitive_type", "CUBE")
        loc = params.get("location", (0, 0, 0))
        rot = params.get("rotation", (0, 0, 0))
        scale = params.get("scale", (1, 1, 1))

        if prim_type == "CUBE": bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot, scale=scale)
        elif prim_type == "SPHERE": bpy.ops.mesh.primitive_uv_sphere_add(location=loc, rotation=rot, scale=scale)
        elif prim_type == "CYLINDER": bpy.ops.mesh.primitive_cylinder_add(location=loc, rotation=rot, scale=scale)
        elif prim_type == "PLANE": bpy.ops.mesh.primitive_plane_add(location=loc, rotation=rot, scale=scale)
        elif prim_type == "CONE": bpy.ops.mesh.primitive_cone_add(location=loc, rotation=rot, scale=scale)
        elif prim_type == "TORUS": bpy.ops.mesh.primitive_torus_add(location=loc, rotation=rot, scale=scale)
        elif prim_type == "MONKEY": bpy.ops.mesh.primitive_monkey_add(location=loc, rotation=rot, scale=scale)
        
        obj = bpy.context.active_object
        if name: obj.name = name
        return {"status": "success", "data": {"name": obj.name}}

    elif action == "delete":
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)
            return {"status": "success", "message": f"Object '{name}' deleted."}
        return {"status": "error", "message": f"Object '{name}' not found."}

    elif action == "transform":
        obj = bpy.data.objects.get(name)
        if not obj: return {"status": "error", "message": f"Object '{name}' not found."}
        if "location" in params: obj.location = params["location"]
        if "rotation" in params: obj.rotation_euler = params["rotation"]
        if "scale" in params: obj.scale = params["scale"]
        return {"status": "success", "message": f"Transformed '{name}'."}

    elif action == "rename":
        obj = bpy.data.objects.get(name)
        if obj:
            obj.name = params["new_name"]
            return {"status": "success", "data": {"name": obj.name}}
        return {"status": "error", "message": f"Object '{name}' not found."}

    elif action == "set_parent":
        child = bpy.data.objects.get(name)
        parent = bpy.data.objects.get(params.get("parent"))
        if child and parent:
            child.parent = parent
            return {"status": "success", "message": f"Parented '{name}' to '{parent.name}'."}
        return {"status": "error", "message": "Child or parent not found."}

    return {"status": "error", "message": f"Unknown action: {action}"}

def handle_manage_collection(params: dict) -> dict:
    """POST /api/collection/manage"""
    action = params.get("action")
    name = params.get("name")
    coll = bpy.data.collections.get(name)

    if action == "create":
        new_coll = bpy.data.collections.new(name)
        parent_name = params.get("parent", "Scene Collection")
        if parent_name == "Scene Collection":
            bpy.context.scene.collection.children.link(new_coll)
        else:
            parent = bpy.data.collections.get(parent_name)
            if parent: parent.children.link(new_coll)
        return {"status": "success", "data": {"name": new_coll.name}}

    elif action == "add_object":
        obj = bpy.data.objects.get(params.get("object"))
        if coll and obj:
            # Unlink from old collections
            for c in obj.users_collection: c.objects.unlink(obj)
            coll.objects.link(obj)
            return {"status": "success", "message": f"Linked '{obj.name}' to '{name}'."}
        return {"status": "error", "message": "Collection or object not found."}

    return {"status": "error", "message": f"Unknown action: {action}"}
