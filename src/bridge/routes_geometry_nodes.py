import bpy


def handle_manage_geometry_nodes(params: dict) -> dict:
    """GeoNodes modifier: create/read/set_input/get_inputs/apply/delete/set_node_group."""
    action = params.get("action")
    obj_name = params.get("object")

    if action == "create":
        obj = bpy.data.objects.get(obj_name)
        if not obj:
            return {"status": "error", "message": f"Object '{obj_name}' not found."}
        mod_name = params.get("modifier_name", "GeometryNodes")
        mod = obj.modifiers.new(name=mod_name, type='NODES')
        if not mod.node_group:
            tree = bpy.data.node_groups.new(mod_name, 'GeometryNodeTree')
            # Create proper I/O
            inp = tree.nodes.new('NodeGroupInput')
            inp.location = (-300, 0)
            out = tree.nodes.new('NodeGroupOutput')
            out.location = (300, 0)
            # Add geometry socket
            tree.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
            tree.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
            tree.links.new(inp.outputs[0], out.inputs[0])
            mod.node_group = tree
        return {"status": "success", "data": {"modifier": mod.name, "node_group": mod.node_group.name if mod.node_group else None}}

    elif action == "read":
        obj = bpy.data.objects.get(obj_name)
        if not obj:
            return {"status": "error", "message": f"Object '{obj_name}' not found."}
        mod = obj.modifiers.get(params.get("modifier_name", "GeometryNodes"))
        if not mod or mod.type != 'NODES' or not mod.node_group:
            return {"status": "error", "message": "GeoNodes modifier not found."}
        tree = mod.node_group
        nodes = []
        for n in tree.nodes:
            nodes.append({"name": n.name, "type": n.bl_idname, "location": list(n.location)})
        links = []
        for l in tree.links:
            links.append({
                "from_node": l.from_node.name, "from_socket": l.from_socket.name,
                "to_node": l.to_node.name, "to_socket": l.to_socket.name,
            })
        return {"status": "success", "data": {"nodes": nodes, "links": links}}

    elif action == "set_input":
        obj = bpy.data.objects.get(obj_name)
        if not obj:
            return {"status": "error", "message": f"Object '{obj_name}' not found."}
        mod = obj.modifiers.get(params.get("modifier_name", "GeometryNodes"))
        if not mod or mod.type != 'NODES':
            return {"status": "error", "message": "GeoNodes modifier not found."}
        inputs = params.get("inputs", {})
        for key, val in inputs.items():
            try:
                if key in mod:
                    mod[key] = val
            except Exception:
                pass
        return {"status": "success", "message": "GeoNode inputs updated."}

    elif action == "get_inputs":
        obj = bpy.data.objects.get(obj_name)
        if not obj:
            return {"status": "error", "message": f"Object '{obj_name}' not found."}
        mod = obj.modifiers.get(params.get("modifier_name", "GeometryNodes"))
        if not mod or mod.type != 'NODES' or not mod.node_group:
            return {"status": "error", "message": "GeoNodes modifier not found."}
        inputs = {}
        for item in mod.node_group.interface.items_tree:
            if item.in_out == 'INPUT' and item.item_type == 'SOCKET':
                try:
                    identifier = item.identifier
                    if identifier in mod:
                        val = mod[identifier]
                        inputs[item.name] = val if not hasattr(val, '__iter__') else list(val)
                except:
                    inputs[item.name] = "<unavailable>"
        return {"status": "success", "data": inputs}

    elif action == "apply":
        obj = bpy.data.objects.get(obj_name)
        if not obj:
            return {"status": "error", "message": f"Object '{obj_name}' not found."}
        mod_name = params.get("modifier_name", "GeometryNodes")
        mod = obj.modifiers.get(mod_name)
        if mod:
            bpy.context.view_layer.objects.active = obj
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
                return {"status": "success", "message": f"GeoNodes '{mod_name}' applied."}
            except Exception as e:
                return {"status": "error", "message": f"Apply failed: {e}"}
        return {"status": "error", "message": f"Modifier '{mod_name}' not found."}

    elif action == "delete":
        obj = bpy.data.objects.get(obj_name)
        if not obj:
            return {"status": "error", "message": f"Object '{obj_name}' not found."}
        mod_name = params.get("modifier_name", "GeometryNodes")
        mod = obj.modifiers.get(mod_name)
        if mod:
            obj.modifiers.remove(mod)
            return {"status": "success", "message": f"GeoNodes '{mod_name}' deleted."}
        return {"status": "error", "message": f"Modifier '{mod_name}' not found."}

    elif action == "set_node_group":
        obj = bpy.data.objects.get(obj_name)
        if not obj:
            return {"status": "error", "message": f"Object '{obj_name}' not found."}
        mod = obj.modifiers.get(params.get("modifier_name", "GeometryNodes"))
        if not mod or mod.type != 'NODES':
            return {"status": "error", "message": "GeoNodes modifier not found."}
        group_name = params.get("node_group")
        group = bpy.data.node_groups.get(group_name)
        if group:
            mod.node_group = group
            return {"status": "success", "message": f"Node group set to '{group_name}'."}
        return {"status": "error", "message": f"Node group '{group_name}' not found."}

    return {"status": "error", "message": f"Unknown geometry_nodes action: {action}"}


def handle_manage_node_group(params: dict) -> dict:
    """Node group CRUD for GeometryNodeTree/ShaderNodeTree/CompositorNodeTree."""
    action = params.get("action")
    ntype = params.get("tree_type", "GeometryNodeTree")
    name = params.get("name")

    if action == "list":
        groups = []
        for g in bpy.data.node_groups:
            if ntype == "" or g.bl_idname == ntype:
                groups.append({"name": g.name, "type": g.bl_idname, "nodes": len(g.nodes)})
        return {"status": "success", "data": groups}

    elif action == "create":
        tree = bpy.data.node_groups.new(name or "NodeGroup", ntype)
        return {"status": "success", "data": {"name": tree.name, "type": tree.bl_idname}}

    elif action == "read":
        tree = bpy.data.node_groups.get(name)
        if not tree:
            return {"status": "error", "message": f"Node group '{name}' not found."}
        nodes = [{"name": n.name, "type": n.bl_idname, "location": list(n.location)} for n in tree.nodes]
        links = [{"from": l.from_node.name, "from_socket": l.from_socket.name,
                   "to": l.to_node.name, "to_socket": l.to_socket.name} for l in tree.links]
        return {"status": "success", "data": {"nodes": nodes, "links": links}}

    elif action == "duplicate":
        tree = bpy.data.node_groups.get(name)
        if tree:
            new_tree = tree.copy()
            new_name = params.get("new_name", f"{name}.copy")
            new_tree.name = new_name
            return {"status": "success", "data": {"name": new_tree.name}}
        return {"status": "error", "message": f"Node group '{name}' not found."}

    elif action == "delete":
        tree = bpy.data.node_groups.get(name)
        if tree:
            bpy.data.node_groups.remove(tree)
            return {"status": "success", "message": f"Node group '{name}' deleted."}
        return {"status": "error", "message": f"Node group '{name}' not found."}

    return {"status": "error", "message": f"Unknown node_group action: {action}"}
