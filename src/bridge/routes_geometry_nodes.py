import bpy

def handle_manage_geometry_nodes(params: dict) -> dict:
    """POST /api/geometry_nodes/manage"""
    name = params.get("object")
    obj = bpy.data.objects.get(name)
    if not obj: return {"status": "error", "message": f"Object '{name}' not found."}

    action = params.get("action")
    
    if action == "create":
        mod = obj.modifiers.new(name="GeometryNodes", type='NODES')
        if not mod.node_group:
            tree = bpy.data.node_groups.new("Geometry Nodes", 'GeometryNodeTree')
            mod.node_group = tree
            tree.nodes.new('NodeGroupInput')
            tree.nodes.new('NodeGroupOutput')
        return {"status": "success", "data": {"modifier": mod.name}}

    elif action == "set_input":
        mod = obj.modifiers.get(params.get("modifier_name", "GeometryNodes"))
        if mod and mod.type == 'NODES':
            inputs = params.get("inputs", {})
            for key, val in inputs.items():
                if key in mod: mod[key] = val
            return {"status": "success", "message": "Inputs updated."}

    return {"status": "error", "message": f"Unknown action: {action}"}

def handle_manage_node_group(params: dict) -> dict:
    """POST /api/node_group/manage"""
    action = params.get("action")
    ntype = params.get("tree_type", "GeometryNodeTree")
    name = params.get("name")

    if action == "list":
        groups = [g.name for g in bpy.data.node_groups if g.bl_idname == ntype]
        return {"status": "success", "data": groups}

    elif action == "create":
        tree = bpy.data.node_groups.new(name, ntype)
        return {"status": "success", "data": {"name": tree.name}}

    return {"status": "error", "message": f"Unknown action: {action}"}
