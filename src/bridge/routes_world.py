import bpy
import math


def handle_manage_world(params: dict) -> dict:
    """World: solid color, HDRI, sky, strength, volumetric fog."""
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world

    action = params.get("action")

    if action == "get":
        data = {"name": world.name, "use_nodes": world.use_nodes}
        if world.use_nodes and world.node_tree:
            bg = world.node_tree.nodes.get("Background")
            if bg:
                data["color"] = list(bg.inputs[0].default_value)
                data["strength"] = bg.inputs[1].default_value
            # Check for environment texture
            for node in world.node_tree.nodes:
                if node.type == 'TEX_ENVIRONMENT' and node.image:
                    data["hdri"] = node.image.filepath
                elif node.type == 'TEX_SKY':
                    data["sky_type"] = node.sky_type
        return {"status": "success", "data": data}

    elif action == "set_color":
        color = params.get("color", [0.05, 0.05, 0.05])
        world.use_nodes = True
        tree = world.node_tree
        # Find or create background node
        bg = tree.nodes.get("Background")
        if not bg:
            tree.nodes.clear()
            bg = tree.nodes.new('ShaderNodeBackground')
            out = tree.nodes.new('ShaderNodeOutputWorld')
            tree.links.new(bg.outputs[0], out.inputs[0])
        if len(color) == 3:
            color = list(color) + [1.0]
        bg.inputs[0].default_value = tuple(color)
        if "strength" in params:
            bg.inputs[1].default_value = params["strength"]
        return {"status": "success", "message": "World color set."}

    elif action == "set_hdri":
        path = params.get("hdri_path")
        if not path:
            return {"status": "error", "message": "No HDRI path."}

        world.use_nodes = True
        tree = world.node_tree
        tree.nodes.clear()

        # Create nodes: Coord → Mapping → Environment → Background → Output
        node_coord = tree.nodes.new('ShaderNodeTexCoord')
        node_coord.location = (-700, 0)
        node_mapping = tree.nodes.new('ShaderNodeMapping')
        node_mapping.location = (-500, 0)
        node_env = tree.nodes.new('ShaderNodeTexEnvironment')
        node_env.location = (-200, 0)
        node_bg = tree.nodes.new('ShaderNodeBackground')
        node_bg.location = (100, 0)
        node_out = tree.nodes.new('ShaderNodeOutputWorld')
        node_out.location = (300, 0)

        # Links
        tree.links.new(node_coord.outputs['Generated'], node_mapping.inputs['Vector'])
        tree.links.new(node_mapping.outputs['Vector'], node_env.inputs['Vector'])
        tree.links.new(node_env.outputs['Color'], node_bg.inputs['Color'])
        tree.links.new(node_bg.outputs['Background'], node_out.inputs['Surface'])

        try:
            node_env.image = bpy.data.images.load(path)
        except Exception as e:
            return {"status": "error", "message": f"Failed to load HDRI: {e}"}

        if "strength" in params:
            node_bg.inputs[1].default_value = params["strength"]
        if "rotation" in params:
            node_mapping.inputs['Rotation'].default_value[2] = params["rotation"]

        return {"status": "success", "message": "HDRI loaded with mapping."}

    elif action == "set_sky":
        world.use_nodes = True
        tree = world.node_tree
        tree.nodes.clear()

        sky_params = params.get("sky_params", {})
        sky_type = sky_params.get("sky_type", "NISHITA")

        node_sky = tree.nodes.new('ShaderNodeTexSky')
        node_sky.location = (-200, 0)
        node_sky.sky_type = sky_type

        if sky_type == "NISHITA":
            if "sun_elevation" in sky_params:
                node_sky.sun_elevation = math.radians(sky_params["sun_elevation"])
            if "sun_rotation" in sky_params:
                node_sky.sun_rotation = math.radians(sky_params["sun_rotation"])
            if "altitude" in sky_params:
                node_sky.altitude = sky_params["altitude"]
            if "air_density" in sky_params:
                node_sky.air_density = sky_params["air_density"]
            if "dust_density" in sky_params:
                node_sky.dust_density = sky_params["dust_density"]
            if "ozone_density" in sky_params:
                node_sky.ozone_density = sky_params["ozone_density"]

        node_bg = tree.nodes.new('ShaderNodeBackground')
        node_bg.location = (100, 0)
        node_out = tree.nodes.new('ShaderNodeOutputWorld')
        node_out.location = (300, 0)

        tree.links.new(node_sky.outputs[0], node_bg.inputs[0])
        tree.links.new(node_bg.outputs[0], node_out.inputs[0])

        if "strength" in params:
            node_bg.inputs[1].default_value = params["strength"]

        return {"status": "success", "message": f"Sky set to {sky_type}."}

    elif action == "set_strength":
        world.use_nodes = True
        bg = world.node_tree.nodes.get("Background")
        if bg:
            bg.inputs[1].default_value = params.get("strength", 1.0)
            return {"status": "success", "message": "World strength updated."}
        return {"status": "error", "message": "No Background node found."}

    elif action == "set_volume":
        world.use_nodes = True
        tree = world.node_tree
        density = params.get("density", 0.01)

        # Find output node
        out = None
        for n in tree.nodes:
            if n.type == 'OUTPUT_WORLD':
                out = n
                break
        if not out:
            out = tree.nodes.new('ShaderNodeOutputWorld')

        # Create volume scatter
        vol = tree.nodes.new('ShaderNodeVolumePrincipled')
        vol.location = (out.location.x - 200, out.location.y - 200)
        vol.inputs['Density'].default_value = density
        if "color" in params:
            c = params["color"]
            vol.inputs['Color'].default_value = tuple(c[:3]) + (1.0,) if len(c) == 3 else tuple(c)

        tree.links.new(vol.outputs['Volume'], out.inputs['Volume'])
        return {"status": "success", "message": "Volumetric fog added."}

    return {"status": "error", "message": f"Unknown world action: {action}"}
