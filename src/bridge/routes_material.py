import bpy

def handle_get_materials_list(params: dict) -> dict:
    """GET /api/materials/list"""
    materials = []
    for mat in bpy.data.materials:
        mat_info = {"name": mat.name, "use_nodes": mat.use_nodes}
        if mat.use_nodes and mat.node_tree:
            # Try to get Principled BSDF values
            node = mat.node_tree.nodes.get("Principled BSDF")
            if node:
                for inp in node.inputs:
                    if inp.is_linked: continue
                    val = inp.default_value
                    mat_info[inp.name.lower().replace(" ", "_")] = list(val) if hasattr(val, "__iter__") else val
        materials.append(mat_info)
    return {"status": "success", "data": materials}

def handle_get_material_details(params: dict) -> dict:
    """GET /api/material/details"""
    name = params.get("name")
    mat = bpy.data.materials.get(name)
    if not mat: return {"status": "error", "message": f"Material '{name}' not found."}

    data = {"name": mat.name, "nodes": [], "links": []}
    if mat.use_nodes and mat.node_tree:
        for node in mat.node_tree.nodes:
            data["nodes"].append({"name": node.name, "type": node.type, "location": list(node.location)})
        for link in mat.node_tree.links:
            data["links"].append({
                "from_node": link.from_node.name,
                "from_socket": link.from_socket.name,
                "to_node": link.to_node.name,
                "to_socket": link.to_socket.name
            })
    return {"status": "success", "data": data}

def handle_manage_material(params: dict) -> dict:
    """POST /api/material/manage"""
    action = params.get("action")
    name = params.get("name")

    if action == "create":
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        return {"status": "success", "data": {"name": mat.name}}

    elif action == "assign":
        obj = bpy.data.objects.get(params.get("assign_to"))
        mat = bpy.data.materials.get(name)
        if obj and mat:
            if not obj.data.materials: obj.data.materials.append(mat)
            else: obj.data.materials[params.get("slot_index", 0)] = mat
            return {"status": "success", "message": f"Assigned '{name}' to '{obj.name}'."}
        return {"status": "error", "message": "Object or material not found."}

    elif action == "modify":
        mat = bpy.data.materials.get(name)
        if mat and mat.use_nodes:
            node = mat.node_tree.nodes.get("Principled BSDF")
            if node:
                props = params.get("properties", {})
                for key, val in props.items():
                    # Map key to socket name
                    socket_map = {"base_color": "Base Color", "metallic": "Metallic", "roughness": "Roughness", "alpha": "Alpha"}
                    sname = socket_map.get(key, key.replace("_", " ").title())
                    if sname in node.inputs:
                        inp = node.inputs[sname]
                        inp.default_value = tuple(val) if isinstance(val, (list, tuple)) else val
                return {"status": "success", "message": f"Modified material '{name}'."}
        return {"status": "error", "message": "Material not found or no nodes."}

    return {"status": "error", "message": f"Unknown action: {action}"}

def handle_manage_shader_nodes(params: dict) -> dict:
    """POST /api/shader_nodes/manage"""
    name = params.get("material")
    mat = bpy.data.materials.get(name)
    if not mat or not mat.use_nodes:
        return {"status": "error", "message": f"Material '{name}' not found or uses no nodes."}

    action = params.get("action")
    tree = mat.node_tree

    if action == "add_node":
        ntype = params.get("node_type")
        node = tree.nodes.new(type=ntype)
        if "location" in params: node.location = params["location"]
        if "name" in params: node.name = params["name"]
        return {"status": "success", "data": {"name": node.name}}

    elif action == "connect":
        fn = tree.nodes.get(params.get("from_node"))
        tn = tree.nodes.get(params.get("to_node"))
        if fn and tn:
            tree.links.new(fn.outputs[params["from_socket"]], tn.inputs[params["to_socket"]])
            return {"status": "success", "message": "Linked nodes."}
        return {"status": "error", "message": "Node(s) not found."}

    return {"status": "error", "message": f"Unknown action: {action}"}
