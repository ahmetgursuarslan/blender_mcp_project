import bpy
import math


def handle_scene_hierarchy(params: dict) -> dict:
    """Full scene tree with transforms, materials, modifiers, collections."""
    include_transform = params.get("include_transform", True)
    max_depth = params.get("max_depth", 10)

    def _build_obj_entry(obj, inc_t):
        entry = {
            "name": obj.name,
            "type": obj.type,
            "visible": obj.visible_get(),
            "collections": [c.name for c in obj.users_collection],
        }
        if inc_t:
            entry["location"] = list(obj.location)
            entry["rotation"] = [round(math.degrees(r), 2) for r in obj.rotation_euler]
            entry["scale"] = [round(s, 4) for s in obj.scale]
            entry["dimensions"] = [round(d, 4) for d in obj.dimensions]
        if obj.type == 'MESH' and obj.data:
            entry["vertices"] = len(obj.data.vertices)
            entry["faces"] = len(obj.data.polygons)
        if obj.data and hasattr(obj.data, 'materials'):
            entry["materials"] = [m.name for m in obj.data.materials if m]
        entry["modifiers"] = [{"name": m.name, "type": m.type} for m in obj.modifiers]
        return entry

    def get_children(obj, depth):
        if depth >= max_depth:
            return []
        children = []
        for child in obj.children:
            entry = _build_obj_entry(child, include_transform)
            entry["children"] = get_children(child, depth + 1)
            children.append(entry)
        return children

    root_objects = [o for o in bpy.context.scene.objects if not o.parent]
    hierarchy = []
    for obj in root_objects:
        entry = _build_obj_entry(obj, include_transform)
        entry["children"] = get_children(obj, 1)
        hierarchy.append(entry)

    collections = []
    for col in bpy.data.collections:
        collections.append({
            "name": col.name,
            "objects": [o.name for o in col.objects],
            "children": [c.name for c in col.children],
        })

    return {"status": "success", "data": {"hierarchy": hierarchy, "collections": collections}}


def handle_get_object_details(params: dict) -> dict:
    """Full object details."""
    name = params.get("name")
    obj = bpy.data.objects.get(name)
    if not obj:
        return {"status": "error", "message": f"Object '{name}' not found."}

    data = {
        "name": obj.name,
        "type": obj.type,
        "location": list(obj.location),
        "rotation_euler": [round(math.degrees(r), 2) for r in obj.rotation_euler],
        "rotation_mode": obj.rotation_mode,
        "scale": list(obj.scale),
        "dimensions": list(obj.dimensions),
        "origin": list(obj.matrix_world.translation),
        "visible": obj.visible_get(),
        "hide_viewport": obj.hide_viewport,
        "hide_render": obj.hide_render,
        "parent": obj.parent.name if obj.parent else None,
        "children": [c.name for c in obj.children],
        "collections": [c.name for c in obj.users_collection],
    }

    if obj.bound_box:
        bb = [list(v) for v in obj.bound_box]
        data["bounding_box"] = {
            "min": [min(v[i] for v in bb) for i in range(3)],
            "max": [max(v[i] for v in bb) for i in range(3)],
        }

    if params.get("include_modifiers", True):
        mods = []
        for m in obj.modifiers:
            mod_data = {"name": m.name, "type": m.type, "show_viewport": m.show_viewport, "show_render": m.show_render}
            for prop in ['levels', 'render_levels', 'width', 'segments', 'offset', 'count',
                         'thickness', 'angle_limit', 'iterations']:
                if hasattr(m, prop):
                    val = getattr(m, prop)
                    mod_data[prop] = list(val) if hasattr(val, '__iter__') else val
            mods.append(mod_data)
        data["modifiers"] = mods

    if params.get("include_materials", True) and obj.type == 'MESH' and obj.data:
        mats = []
        for idx, slot in enumerate(obj.material_slots):
            if slot.material:
                mat_info = {"slot": idx, "name": slot.material.name}
                if slot.material.use_nodes:
                    bsdf = slot.material.node_tree.nodes.get("Principled BSDF")
                    if bsdf:
                        for inp_name in ["Base Color", "Metallic", "Roughness", "Alpha"]:
                            if inp_name in bsdf.inputs and not bsdf.inputs[inp_name].is_linked:
                                val = bsdf.inputs[inp_name].default_value
                                mat_info[inp_name.lower().replace(" ", "_")] = list(val) if hasattr(val, '__iter__') else round(val, 4)
                mats.append(mat_info)
        data["materials"] = mats

    if obj.type == 'MESH' and obj.data:
        mesh = obj.data
        data["mesh_info"] = {
            "vertices": len(mesh.vertices),
            "edges": len(mesh.edges),
            "faces": len(mesh.polygons),
            "uv_layers": [l.name for l in mesh.uv_layers],
            "vertex_groups": [g.name for g in obj.vertex_groups],
            "has_shape_keys": mesh.shape_keys is not None,
        }

    data["constraints"] = [{"name": c.name, "type": c.type, "enabled": not c.mute} for c in obj.constraints]
    return {"status": "success", "data": data}


def handle_manage_object(params: dict) -> dict:
    """Object CRUD with all actions."""
    action = params.get("action")
    name = params.get("name")

    if action == "create":
        prim_type = params.get("primitive_type", "CUBE")
        loc = tuple(params.get("location", (0, 0, 0)))
        rot = tuple(params.get("rotation", (0, 0, 0)))
        scale = tuple(params.get("scale", (1, 1, 1)))

        prim_map = {
            "CUBE": bpy.ops.mesh.primitive_cube_add,
            "SPHERE": bpy.ops.mesh.primitive_uv_sphere_add,
            "CYLINDER": bpy.ops.mesh.primitive_cylinder_add,
            "PLANE": bpy.ops.mesh.primitive_plane_add,
            "CONE": bpy.ops.mesh.primitive_cone_add,
            "TORUS": bpy.ops.mesh.primitive_torus_add,
            "MONKEY": bpy.ops.mesh.primitive_monkey_add,
            "CIRCLE": bpy.ops.mesh.primitive_circle_add,
            "GRID": bpy.ops.mesh.primitive_grid_add,
            "ICO_SPHERE": bpy.ops.mesh.primitive_ico_sphere_add,
        }
        fn = prim_map.get(prim_type)
        if not fn:
            return {"status": "error", "message": f"Unknown primitive type: {prim_type}. Valid: {list(prim_map.keys())}"}
        fn(location=loc, rotation=rot, scale=scale)
        obj = bpy.context.active_object
        if name:
            obj.name = name
            if obj.data:
                obj.data.name = name
        return {"status": "success", "data": {"name": obj.name, "type": obj.type}}

    elif action == "create_empty":
        display_type = params.get("display_type", "PLAIN_AXES")
        loc = tuple(params.get("location", (0, 0, 0)))
        bpy.ops.object.empty_add(type=display_type, location=loc)
        obj = bpy.context.active_object
        if name:
            obj.name = name
        if "scale" in params:
            obj.scale = tuple(params["scale"])
        return {"status": "success", "data": {"name": obj.name}}

    elif action == "delete":
        if name == "__all__":
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.delete()
            return {"status": "success", "message": "All objects deleted."}
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)
            return {"status": "success", "message": f"Object '{name}' deleted."}
        return {"status": "error", "message": f"Object '{name}' not found."}

    elif action == "duplicate":
        obj = bpy.data.objects.get(name)
        if not obj:
            return {"status": "error", "message": f"Object '{name}' not found."}
        new_obj = obj.copy()
        if obj.data:
            new_obj.data = obj.data.copy()
        new_name = params.get("new_name", f"{name}.copy")
        new_obj.name = new_name
        for col in obj.users_collection:
            col.objects.link(new_obj)
        if "location" in params:
            new_obj.location = tuple(params["location"])
        return {"status": "success", "data": {"name": new_obj.name}}

    elif action == "rename":
        obj = bpy.data.objects.get(name)
        if obj:
            new_name = params.get("new_name", name)
            obj.name = new_name
            if obj.data:
                obj.data.name = new_name
            return {"status": "success", "data": {"name": obj.name}}
        return {"status": "error", "message": f"Object '{name}' not found."}

    elif action == "transform":
        obj = bpy.data.objects.get(name)
        if not obj:
            return {"status": "error", "message": f"Object '{name}' not found."}
        if "location" in params:
            obj.location = tuple(params["location"])
        if "rotation" in params:
            obj.rotation_euler = tuple(params["rotation"])
        if "scale" in params:
            obj.scale = tuple(params["scale"])
        return {"status": "success", "message": f"Transformed '{name}'.", "data": {
            "location": list(obj.location), "rotation": list(obj.rotation_euler), "scale": list(obj.scale)}}

    elif action == "set_parent":
        child = bpy.data.objects.get(name)
        parent_name = params.get("parent")
        if not child:
            return {"status": "error", "message": f"Object '{name}' not found."}
        if parent_name:
            parent = bpy.data.objects.get(parent_name)
            if not parent:
                return {"status": "error", "message": f"Parent '{parent_name}' not found."}
            child.parent = parent
            child.matrix_parent_inverse = parent.matrix_world.inverted()
        else:
            child.parent = None
        return {"status": "success", "message": f"Parent set for '{name}'."}

    elif action == "set_visibility":
        obj = bpy.data.objects.get(name)
        if not obj:
            return {"status": "error", "message": f"Object '{name}' not found."}
        if "hide_viewport" in params:
            obj.hide_viewport = params["hide_viewport"]
        if "hide_render" in params:
            obj.hide_render = params["hide_render"]
        return {"status": "success", "message": f"Visibility updated for '{name}'."}

    elif action == "select":
        if name == "__all__":
            bpy.ops.object.select_all(action='SELECT')
        elif name == "__none__":
            bpy.ops.object.select_all(action='DESELECT')
        else:
            obj = bpy.data.objects.get(name)
            if not obj:
                return {"status": "error", "message": f"Object '{name}' not found."}
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
        return {"status": "success", "message": "Selection updated."}

    return {"status": "error", "message": f"Unknown action: {action}"}


def handle_manage_collection(params: dict) -> dict:
    """Collection CRUD: list/create/add_object/remove_object/delete."""
    action = params.get("action")
    name = params.get("name")

    if action == "list":
        cols = []
        for col in bpy.data.collections:
            cols.append({
                "name": col.name,
                "objects": [o.name for o in col.objects],
                "children": [c.name for c in col.children],
                "hide_viewport": col.hide_viewport,
            })
        return {"status": "success", "data": cols}

    elif action == "create":
        new_coll = bpy.data.collections.new(name or "Collection")
        parent_name = params.get("parent", "Scene Collection")
        if parent_name == "Scene Collection":
            bpy.context.scene.collection.children.link(new_coll)
        else:
            parent = bpy.data.collections.get(parent_name)
            if parent:
                parent.children.link(new_coll)
            else:
                bpy.context.scene.collection.children.link(new_coll)
        return {"status": "success", "data": {"name": new_coll.name}}

    elif action == "add_object":
        obj_name = params.get("object")
        col_name = params.get("collection", name)
        coll = bpy.data.collections.get(col_name)
        obj = bpy.data.objects.get(obj_name)
        if not coll:
            return {"status": "error", "message": f"Collection '{col_name}' not found."}
        if not obj:
            return {"status": "error", "message": f"Object '{obj_name}' not found."}
        if obj.name not in coll.objects:
            coll.objects.link(obj)
        return {"status": "success", "message": f"Linked '{obj.name}' to '{col_name}'."}

    elif action == "remove_object":
        obj_name = params.get("object")
        col_name = params.get("collection", name)
        coll = bpy.data.collections.get(col_name)
        obj = bpy.data.objects.get(obj_name)
        if coll and obj and obj.name in coll.objects:
            coll.objects.unlink(obj)
            return {"status": "success", "message": f"Unlinked '{obj.name}' from '{col_name}'."}
        return {"status": "error", "message": "Collection or object not found."}

    elif action == "delete":
        coll = bpy.data.collections.get(name)
        if coll:
            bpy.data.collections.remove(coll)
            return {"status": "success", "message": f"Collection '{name}' deleted."}
        return {"status": "error", "message": f"Collection '{name}' not found."}

    return {"status": "error", "message": f"Unknown action: {action}"}
