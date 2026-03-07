import bpy

def handle_manage_world(params: dict) -> dict:
    """POST /api/world/manage"""
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    
    action = params.get("action")
    
    if action == "set_color":
        color = params.get("color", [0.05, 0.05, 0.05])
        if world.use_nodes:
            bg = world.node_tree.nodes.get("Background")
            if bg: bg.inputs[0].default_value = tuple(color) + (1.0,)
        else:
            world.color = color[:3]
        return {"status": "success", "message": "World color set."}

    elif action == "set_hdri":
        path = params.get("hdri_path")
        if not path: return {"status": "error", "message": "No HDRI path."}
        
        world.use_nodes = True
        tree = world.node_tree
        tree.nodes.clear()
        
        node_env = tree.nodes.new('ShaderNodeTexEnvironment')
        try:
            node_env.image = bpy.data.images.load(path)
        except Exception as e:
            return {"status": "error", "message": f"Failed to load HDRI: {e}"}
            
        node_bg = tree.nodes.new('ShaderNodeBackground')
        node_out = tree.nodes.new('ShaderNodeOutputWorld')
        
        tree.links.new(node_env.outputs[0], node_bg.inputs[0])
        tree.links.new(node_bg.outputs[0], node_out.inputs[0])
        
        if "strength" in params: node_bg.inputs[1].default_value = params["strength"]
        
        return {"status": "success", "message": f"HDRI loaded."}

    return {"status": "error", "message": f"Unknown action: {action}"}
