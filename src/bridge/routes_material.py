import bpy


# Complete socket name mapping for Principled BSDF (Blender 4.x)
BSDF_SOCKET_MAP = {
    # Core
    "base_color": "Base Color",
    "metallic": "Metallic",
    "roughness": "Roughness",
    "alpha": "Alpha",
    # Spec/Coat
    "specular_ior_level": "Specular IOR Level",
    "specular_tint": "Specular Tint",
    "coat_weight": "Coat Weight",
    "coat_roughness": "Coat Roughness",
    "coat_ior": "Coat IOR",
    "coat_tint": "Coat Tint",
    "coat_normal": "Coat Normal",
    # Transmission / SSS
    "transmission_weight": "Transmission Weight",
    "ior": "IOR",
    "subsurface_weight": "Subsurface Weight",
    "subsurface_radius": "Subsurface Radius",
    "subsurface_scale": "Subsurface Scale",
    "subsurface_ior": "Subsurface IOR",
    "subsurface_anisotropy": "Subsurface Anisotropy",
    # Sheen / Emission
    "sheen_weight": "Sheen Weight",
    "sheen_roughness": "Sheen Roughness",
    "sheen_tint": "Sheen Tint",
    "emission_color": "Emission Color",
    "emission_strength": "Emission Strength",
    # Anisotropic
    "anisotropic": "Anisotropic",
    "anisotropic_rotation": "Anisotropic Rotation",
    # Normal / Tangent
    "normal": "Normal",
    "tangent": "Tangent",
}


def handle_get_materials_list(params: dict) -> dict:
    """All materials with Principled BSDF values."""
    materials = []
    for mat in bpy.data.materials:
        mat_info = {"name": mat.name, "use_nodes": mat.use_nodes, "users": mat.users}
        if mat.use_nodes and mat.node_tree:
            node = mat.node_tree.nodes.get("Principled BSDF")
            if node:
                for inp in node.inputs:
                    if inp.is_linked:
                        mat_info[inp.name.lower().replace(" ", "_")] = "<linked>"
                        continue
                    try:
                        val = inp.default_value
                        mat_info[inp.name.lower().replace(" ", "_")] = list(val) if hasattr(val, "__iter__") else round(val, 4) if isinstance(val, float) else val
                    except:
                        pass
        materials.append(mat_info)
    return {"status": "success", "data": materials}


def handle_get_material_details(params: dict) -> dict:
    """Full shader node graph: nodes + links."""
    name = params.get("name")
    mat = bpy.data.materials.get(name)
    if not mat:
        return {"status": "error", "message": f"Material '{name}' not found."}

    data = {"name": mat.name, "use_nodes": mat.use_nodes, "nodes": [], "links": []}
    if mat.use_nodes and mat.node_tree:
        for node in mat.node_tree.nodes:
            node_info = {
                "name": node.name,
                "type": node.type,
                "bl_idname": node.bl_idname,
                "location": [round(node.location.x), round(node.location.y)],
                "inputs": {},
                "outputs": [o.name for o in node.outputs],
            }
            for inp in node.inputs:
                try:
                    if inp.is_linked:
                        node_info["inputs"][inp.name] = "<linked>"
                    else:
                        val = inp.default_value
                        node_info["inputs"][inp.name] = list(val) if hasattr(val, "__iter__") else val
                except:
                    node_info["inputs"][inp.name] = "<unavailable>"
            data["nodes"].append(node_info)

        for link in mat.node_tree.links:
            data["links"].append({
                "from_node": link.from_node.name,
                "from_socket": link.from_socket.name,
                "to_node": link.to_node.name,
                "to_socket": link.to_socket.name,
            })
    return {"status": "success", "data": data}


def handle_manage_material(params: dict) -> dict:
    """Material CRUD with full Principled BSDF property support."""
    action = params.get("action")
    name = params.get("name")

    if action == "create":
        mat = bpy.data.materials.new(name=name or "Material")
        mat.use_nodes = True
        # Apply initial properties if given
        props = params.get("properties", {})
        if props:
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                _apply_bsdf_props(bsdf, props)
        return {"status": "success", "data": {"name": mat.name}}

    elif action == "modify":
        mat = bpy.data.materials.get(name)
        if not mat:
            return {"status": "error", "message": f"Material '{name}' not found."}
        if not mat.use_nodes:
            mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if not bsdf:
            return {"status": "error", "message": f"No Principled BSDF node in '{name}'."}
        props = params.get("properties", {})
        _apply_bsdf_props(bsdf, props)
        return {"status": "success", "message": f"Modified material '{name}'."}

    elif action == "assign":
        assign_to = params.get("assign_to")
        obj = bpy.data.objects.get(assign_to)
        mat = bpy.data.materials.get(name)
        if not obj:
            return {"status": "error", "message": f"Object '{assign_to}' not found."}
        if not mat:
            return {"status": "error", "message": f"Material '{name}' not found."}
        if not hasattr(obj.data, 'materials'):
            return {"status": "error", "message": f"Object '{assign_to}' does not support materials."}
        slot_idx = params.get("slot_index", 0)
        if not obj.data.materials:
            obj.data.materials.append(mat)
        elif slot_idx < len(obj.data.materials):
            obj.data.materials[slot_idx] = mat
        else:
            obj.data.materials.append(mat)
        return {"status": "success", "message": f"Assigned '{name}' to '{obj.name}' slot {slot_idx}."}

    elif action == "remove":
        mat = bpy.data.materials.get(name)
        if mat:
            bpy.data.materials.remove(mat)
            return {"status": "success", "message": f"Material '{name}' removed."}
        return {"status": "error", "message": f"Material '{name}' not found."}

    elif action == "duplicate":
        mat = bpy.data.materials.get(name)
        if mat:
            new_mat = mat.copy()
            new_name = params.get("new_name", f"{name}.copy")
            new_mat.name = new_name
            return {"status": "success", "data": {"name": new_mat.name}}
        return {"status": "error", "message": f"Material '{name}' not found."}

    return {"status": "error", "message": f"Unknown material action: {action}"}


def _apply_bsdf_props(bsdf, props):
    """Apply properties to a Principled BSDF node."""
    for key, val in props.items():
        socket_name = BSDF_SOCKET_MAP.get(key)
        if not socket_name:
            # Try title-case conversion as fallback
            socket_name = key.replace("_", " ").title()
        if socket_name in bsdf.inputs:
            inp = bsdf.inputs[socket_name]
            if not inp.is_linked:
                try:
                    if isinstance(val, (list, tuple)):
                        # Ensure correct length for color inputs (RGBA)
                        if len(val) == 3 and hasattr(inp.default_value, '__len__') and len(inp.default_value) == 4:
                            inp.default_value = tuple(val) + (1.0,)
                        else:
                            inp.default_value = tuple(val)
                    else:
                        inp.default_value = val
                except Exception:
                    pass


def handle_manage_shader_nodes(params: dict) -> dict:
    """Shader node graph CRUD: add/remove/connect/disconnect/set_value."""
    mat_name = params.get("material")
    mat = bpy.data.materials.get(mat_name)
    if not mat or not mat.use_nodes:
        return {"status": "error", "message": f"Material '{mat_name}' not found or no nodes."}

    action = params.get("action")
    tree = mat.node_tree

    if action == "add_node":
        ntype = params.get("node_type")
        if not ntype:
            return {"status": "error", "message": "node_type is required."}
        try:
            node = tree.nodes.new(type=ntype)
        except Exception as e:
            return {"status": "error", "message": f"Failed to create node type '{ntype}': {e}"}
        if "location" in params:
            node.location = tuple(params["location"])
        if "name" in params:
            node.name = params["name"]
            node.label = params["name"]
        return {"status": "success", "data": {"name": node.name, "type": node.bl_idname}}

    elif action == "remove_node":
        node_name = params.get("name")
        node = tree.nodes.get(node_name)
        if node:
            tree.nodes.remove(node)
            return {"status": "success", "message": f"Node '{node_name}' removed."}
        return {"status": "error", "message": f"Node '{node_name}' not found."}

    elif action == "connect":
        fn = tree.nodes.get(params.get("from_node"))
        tn = tree.nodes.get(params.get("to_node"))
        if not fn:
            return {"status": "error", "message": f"Source node '{params.get('from_node')}' not found."}
        if not tn:
            return {"status": "error", "message": f"Target node '{params.get('to_node')}' not found."}

        from_socket = params.get("from_socket")
        to_socket = params.get("to_socket")

        # Try by name first, then by index
        out = fn.outputs.get(from_socket) if isinstance(from_socket, str) else fn.outputs[from_socket]
        inp = tn.inputs.get(to_socket) if isinstance(to_socket, str) else tn.inputs[to_socket]

        if not out:
            return {"status": "error", "message": f"Output socket '{from_socket}' not found on '{fn.name}'."}
        if not inp:
            return {"status": "error", "message": f"Input socket '{to_socket}' not found on '{tn.name}'."}

        tree.links.new(out, inp)
        return {"status": "success", "message": f"Connected {fn.name}.{from_socket} → {tn.name}.{to_socket}"}

    elif action == "disconnect":
        tn = tree.nodes.get(params.get("to_node"))
        to_socket = params.get("to_socket")
        if tn and to_socket:
            inp = tn.inputs.get(to_socket)
            if inp:
                for link in inp.links:
                    tree.links.remove(link)
                return {"status": "success", "message": f"Disconnected '{to_socket}' on '{tn.name}'."}
        return {"status": "error", "message": "Node or socket not found."}

    elif action == "set_value":
        node_name = params.get("name")
        node = tree.nodes.get(node_name)
        if not node:
            return {"status": "error", "message": f"Node '{node_name}' not found."}
        inp_name = params.get("input")
        val = params.get("value")
        if inp_name in node.inputs:
            inp = node.inputs[inp_name]
            if isinstance(val, (list, tuple)):
                inp.default_value = tuple(val)
            else:
                inp.default_value = val
            return {"status": "success", "message": f"Set '{inp_name}' on '{node_name}'."}
        return {"status": "error", "message": f"Input '{inp_name}' not found on '{node_name}'."}

    return {"status": "error", "message": f"Unknown shader_nodes action: {action}"}
