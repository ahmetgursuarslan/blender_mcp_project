import bpy


def handle_manage_uv(params: dict) -> dict:
    """UV: unwrap/smart_project/cube_project/cylinder_project/sphere_project/pack/create_layer/remove_layer/list_layers."""
    obj_name = params.get("object")
    obj = bpy.data.objects.get(obj_name)
    if not obj or obj.type != 'MESH':
        return {"status": "error", "message": f"Mesh object '{obj_name}' not found."}

    action = params.get("action")
    bpy.context.view_layer.objects.active = obj
    uv_params = params.get("params", {})

    if action in ("unwrap", "smart_project", "cube_project", "cylinder_project", "sphere_project"):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        try:
            if action == "unwrap":
                method = uv_params.get("method", "ANGLE_BASED")
                bpy.ops.uv.unwrap(method=method)
            elif action == "smart_project":
                angle = uv_params.get("angle_limit", 66.0)
                island_margin = uv_params.get("island_margin", 0.0)
                bpy.ops.uv.smart_project(angle_limit=angle, island_margin=island_margin)
            elif action == "cube_project":
                bpy.ops.uv.cube_project()
            elif action == "cylinder_project":
                bpy.ops.uv.cylinder_project()
            elif action == "sphere_project":
                bpy.ops.uv.sphere_project()
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')
        return {"status": "success", "message": f"UV '{action}' completed on '{obj_name}'."}

    elif action == "pack":
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        try:
            margin = uv_params.get("margin", 0.001)
            bpy.ops.uv.pack_islands(margin=margin)
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')
        return {"status": "success", "message": "UV islands packed."}

    elif action == "create_layer":
        layer_name = params.get("uv_layer", "UVMap")
        obj.data.uv_layers.new(name=layer_name)
        return {"status": "success", "message": f"UV layer '{layer_name}' created."}

    elif action == "remove_layer":
        layer_name = params.get("uv_layer")
        uv_layer = obj.data.uv_layers.get(layer_name)
        if uv_layer:
            obj.data.uv_layers.remove(uv_layer)
            return {"status": "success", "message": f"UV layer '{layer_name}' removed."}
        return {"status": "error", "message": f"UV layer '{layer_name}' not found."}

    elif action == "list_layers":
        layers = [{"name": l.name, "active": l.active} for l in obj.data.uv_layers]
        return {"status": "success", "data": layers}

    return {"status": "error", "message": f"Unknown UV action: {action}"}


def handle_manage_images(params: dict) -> dict:
    """Image CRUD: load/create/save/pack/unpack/list/assign_to_node/delete."""
    action = params.get("action")

    if action == "load":
        path = params.get("filepath")
        if not path:
            return {"status": "error", "message": "No filepath provided."}
        try:
            img = bpy.data.images.load(path)
            return {"status": "success", "data": {"name": img.name, "size": list(img.size)}}
        except Exception as e:
            return {"status": "error", "message": f"Load failed: {e}"}

    elif action == "create":
        name = params.get("name", "Image")
        width = params.get("width", 1024)
        height = params.get("height", 1024)
        color = params.get("color", [0, 0, 0, 1])
        is_float = params.get("is_float", False)
        img = bpy.data.images.new(name, width, height, is_data=is_float)
        # Fill with color
        if color:
            pixels = list(color[:4]) * (width * height)
            img.pixels = pixels
        return {"status": "success", "data": {"name": img.name, "size": [width, height]}}

    elif action == "save":
        name = params.get("name")
        path = params.get("filepath")
        img = bpy.data.images.get(name)
        if not img:
            return {"status": "error", "message": f"Image '{name}' not found."}
        if path:
            img.filepath_raw = path
        img.save()
        return {"status": "success", "message": f"Image '{name}' saved."}

    elif action == "pack":
        name = params.get("name")
        img = bpy.data.images.get(name)
        if img:
            img.pack()
            return {"status": "success", "message": f"Image '{name}' packed."}
        return {"status": "error", "message": f"Image '{name}' not found."}

    elif action == "unpack":
        name = params.get("name")
        img = bpy.data.images.get(name)
        if img:
            img.unpack()
            return {"status": "success", "message": f"Image '{name}' unpacked."}
        return {"status": "error", "message": f"Image '{name}' not found."}

    elif action == "list":
        images = []
        for img in bpy.data.images:
            images.append({
                "name": img.name,
                "size": list(img.size),
                "filepath": img.filepath,
                "is_packed": img.packed_file is not None,
                "type": img.type,
            })
        return {"status": "success", "data": images}

    elif action == "assign_to_node":
        img_name = params.get("name")
        mat_name = params.get("material")
        node_name = params.get("node_name")
        img = bpy.data.images.get(img_name)
        mat = bpy.data.materials.get(mat_name)
        if not img or not mat or not mat.use_nodes:
            return {"status": "error", "message": "Image, material, or node tree not found."}
        node = mat.node_tree.nodes.get(node_name)
        if node and hasattr(node, 'image'):
            node.image = img
            return {"status": "success", "message": f"Image '{img_name}' assigned to node '{node_name}'."}
        return {"status": "error", "message": f"Node '{node_name}' not found or doesn't support images."}

    elif action == "delete":
        name = params.get("name")
        img = bpy.data.images.get(name)
        if img:
            bpy.data.images.remove(img)
            return {"status": "success", "message": f"Image '{name}' deleted."}
        return {"status": "error", "message": f"Image '{name}' not found."}

    return {"status": "error", "message": f"Unknown images action: {action}"}


def handle_manage_texture_bake(params: dict) -> dict:
    """Bake: DIFFUSE/NORMAL/AO/ROUGHNESS/EMIT/COMBINED/SHADOW."""
    action = params.get("action")
    obj_name = params.get("object")

    if action == "setup":
        obj = bpy.data.objects.get(obj_name)
        if not obj:
            return {"status": "error", "message": f"Object '{obj_name}' not found."}

        resolution = params.get("resolution", 1024)
        bake_type = params.get("bake_type", "DIFFUSE")

        # Create image for baking
        img_name = f"{obj_name}_{bake_type.lower()}_bake"
        img = bpy.data.images.new(img_name, resolution, resolution)

        # Ensure object has a material with an Image Texture node selected
        if not obj.data.materials:
            mat = bpy.data.materials.new(f"{obj_name}_BakeMat")
            mat.use_nodes = True
            obj.data.materials.append(mat)

        mat = obj.data.materials[0]
        if mat.use_nodes:
            tex_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
            tex_node.image = img
            tex_node.name = "BakeTarget"
            # Make sure this node is selected/active
            for n in mat.node_tree.nodes:
                n.select = False
            tex_node.select = True
            mat.node_tree.nodes.active = tex_node

        return {"status": "success", "data": {"image": img_name, "resolution": resolution}}

    elif action == "bake":
        obj = bpy.data.objects.get(obj_name)
        if not obj:
            return {"status": "error", "message": f"Object '{obj_name}' not found."}

        bake_type = params.get("bake_type", "DIFFUSE")
        samples = params.get("samples", 32)
        margin = params.get("margin", 16)
        output_path = params.get("output_path")

        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.scene.cycles.samples = samples
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)

        try:
            if params.get("use_selected_to_active", False):
                bpy.ops.object.bake(type=bake_type, margin=margin, use_selected_to_active=True,
                                     cage_extrusion=params.get("cage_extrusion", 0.1))
            else:
                bpy.ops.object.bake(type=bake_type, margin=margin)

            if output_path:
                # Save the baked image
                for node in obj.data.materials[0].node_tree.nodes:
                    if node.name == "BakeTarget" and node.image:
                        node.image.filepath_raw = output_path
                        node.image.save()
                        break

            return {"status": "success", "message": f"Baked {bake_type} for '{obj_name}'."}
        except Exception as e:
            return {"status": "error", "message": f"Bake failed: {e}"}

    return {"status": "error", "message": f"Unknown texture_bake action: {action}"}
