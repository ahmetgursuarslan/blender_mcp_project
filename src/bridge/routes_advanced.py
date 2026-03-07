import bpy
import math


def handle_manage_shape_keys(params: dict) -> dict:
    """Shape key CRUD: list/create/delete/set_value/set_key."""
    obj_name = params.get("object")
    obj = bpy.data.objects.get(obj_name)
    if not obj or obj.type != 'MESH':
        return {"status": "error", "message": f"Mesh '{obj_name}' not found."}

    action = params.get("action")

    if action == "list":
        if not obj.data.shape_keys:
            return {"status": "success", "data": []}
        keys = []
        for kb in obj.data.shape_keys.key_blocks:
            keys.append({"name": kb.name, "value": kb.value, "mute": kb.mute})
        return {"status": "success", "data": keys}

    elif action == "create":
        if not obj.data.shape_keys:
            obj.shape_key_add(name="Basis")
        sk = obj.shape_key_add(name=params.get("name", "Key"), from_mix=params.get("from_mix", False))
        return {"status": "success", "data": {"name": sk.name}}

    elif action == "delete":
        sk_name = params.get("name")
        if obj.data.shape_keys:
            kb = obj.data.shape_keys.key_blocks.get(sk_name)
            if kb:
                obj.shape_key_remove(kb)
                return {"status": "success", "message": f"Shape key '{sk_name}' deleted."}
        return {"status": "error", "message": f"Shape key '{sk_name}' not found."}

    elif action == "set_value":
        sk_name = params.get("name")
        val = params.get("value", 0.0)
        if obj.data.shape_keys:
            kb = obj.data.shape_keys.key_blocks.get(sk_name)
            if kb:
                kb.value = val
                return {"status": "success", "message": f"Shape key '{sk_name}' set to {val}."}
        return {"status": "error", "message": f"Shape key '{sk_name}' not found."}

    elif action == "set_key":
        sk_name = params.get("name")
        frame = params.get("frame", bpy.context.scene.frame_current)
        if obj.data.shape_keys:
            kb = obj.data.shape_keys.key_blocks.get(sk_name)
            if kb:
                kb.keyframe_insert("value", frame=frame)
                return {"status": "success", "message": f"Keyframe set for shape key '{sk_name}' at frame {frame}."}
        return {"status": "error", "message": f"Shape key '{sk_name}' not found."}

    return {"status": "error", "message": f"Unknown shape_keys action: {action}"}


def handle_manage_nla(params: dict) -> dict:
    """NLA: list_tracks/push_action/create_strip/mute_track/solo_track."""
    obj_name = params.get("object")
    obj = bpy.data.objects.get(obj_name)
    if not obj:
        return {"status": "error", "message": f"Object '{obj_name}' not found."}

    action = params.get("action")

    if not obj.animation_data:
        obj.animation_data_create()

    if action == "list_tracks":
        tracks = []
        if obj.animation_data.nla_tracks:
            for t in obj.animation_data.nla_tracks:
                strips = [{"name": s.name, "action": s.action.name if s.action else None,
                           "frame_start": s.frame_start, "frame_end": s.frame_end} for s in t.strips]
                tracks.append({"name": t.name, "mute": t.mute, "is_solo": t.is_solo, "strips": strips})
        return {"status": "success", "data": tracks}

    elif action == "push_action":
        act_name = params.get("action_name")
        act = bpy.data.actions.get(act_name)
        if not act:
            return {"status": "error", "message": f"Action '{act_name}' not found."}
        track = obj.animation_data.nla_tracks.new()
        track.name = params.get("track_name", act_name)
        frame_start = params.get("frame_start", 1)
        strip = track.strips.new(act.name, frame_start, act)
        return {"status": "success", "data": {"track": track.name, "strip": strip.name}}

    elif action == "mute_track":
        track_name = params.get("track_name")
        mute = params.get("mute", True)
        for t in obj.animation_data.nla_tracks:
            if t.name == track_name:
                t.mute = mute
                return {"status": "success", "message": f"Track '{track_name}' mute={mute}."}
        return {"status": "error", "message": f"Track '{track_name}' not found."}

    elif action == "solo_track":
        track_name = params.get("track_name")
        for t in obj.animation_data.nla_tracks:
            if t.name == track_name:
                t.is_solo = True
                return {"status": "success", "message": f"Track '{track_name}' soloed."}
        return {"status": "error", "message": f"Track '{track_name}' not found."}

    return {"status": "error", "message": f"Unknown NLA action: {action}"}


def handle_manage_drivers(params: dict) -> dict:
    """Drivers: add/remove/list."""
    obj_name = params.get("object")
    obj = bpy.data.objects.get(obj_name)
    if not obj:
        return {"status": "error", "message": f"Object '{obj_name}' not found."}

    action = params.get("action")

    if action == "add":
        data_path = params.get("data_path")
        array_index = params.get("array_index", -1)
        expression = params.get("expression", "")

        try:
            if array_index >= 0:
                fc = obj.driver_add(data_path, array_index)
            else:
                fc = obj.driver_add(data_path)

            if isinstance(fc, list):
                for f in fc:
                    if expression:
                        f.driver.type = 'SCRIPTED'
                        f.driver.expression = expression
            else:
                if expression:
                    fc.driver.type = 'SCRIPTED'
                    fc.driver.expression = expression

                # Add variables if provided
                variables = params.get("variables", [])
                for var_def in variables:
                    var = fc.driver.variables.new()
                    var.name = var_def.get("name", "var")
                    var.type = var_def.get("type", "SINGLE_PROP")
                    if var.type == "SINGLE_PROP" and "targets" in var_def:
                        t = var_def["targets"][0]
                        var.targets[0].id = bpy.data.objects.get(t.get("id", ""))
                        var.targets[0].data_path = t.get("data_path", "")

            return {"status": "success", "message": f"Driver added to '{data_path}'."}
        except Exception as e:
            return {"status": "error", "message": f"Driver add failed: {e}"}

    elif action == "remove":
        data_path = params.get("data_path")
        array_index = params.get("array_index", -1)
        try:
            if array_index >= 0:
                obj.driver_remove(data_path, array_index)
            else:
                obj.driver_remove(data_path)
            return {"status": "success", "message": f"Driver removed from '{data_path}'."}
        except Exception as e:
            return {"status": "error", "message": f"Driver remove failed: {e}"}

    elif action == "list":
        drivers = []
        if obj.animation_data and obj.animation_data.drivers:
            for fc in obj.animation_data.drivers:
                d = fc.driver
                drivers.append({
                    "data_path": fc.data_path,
                    "array_index": fc.array_index,
                    "type": d.type,
                    "expression": d.expression,
                    "variables": [{"name": v.name, "type": v.type} for v in d.variables],
                })
        return {"status": "success", "data": drivers}

    return {"status": "error", "message": f"Unknown drivers action: {action}"}


def handle_manage_markers(params: dict) -> dict:
    """Timeline markers: add/remove/list/move."""
    action = params.get("action")
    scene = bpy.context.scene

    if action == "add":
        name = params.get("name", "Marker")
        frame = params.get("frame", scene.frame_current)
        marker = scene.timeline_markers.new(name, frame=frame)
        if "camera" in params:
            cam = bpy.data.objects.get(params["camera"])
            if cam and cam.type == 'CAMERA':
                marker.camera = cam
        return {"status": "success", "data": {"name": marker.name, "frame": marker.frame}}

    elif action == "remove":
        name = params.get("name")
        marker = scene.timeline_markers.get(name)
        if marker:
            scene.timeline_markers.remove(marker)
            return {"status": "success", "message": f"Marker '{name}' removed."}
        return {"status": "error", "message": f"Marker '{name}' not found."}

    elif action == "list":
        markers = [{"name": m.name, "frame": m.frame, "camera": m.camera.name if m.camera else None}
                   for m in scene.timeline_markers]
        return {"status": "success", "data": markers}

    elif action == "move":
        name = params.get("name")
        frame = params.get("frame")
        marker = scene.timeline_markers.get(name)
        if marker and frame is not None:
            marker.frame = frame
            return {"status": "success", "message": f"Marker '{name}' moved to frame {frame}."}
        return {"status": "error", "message": f"Marker '{name}' not found or no frame specified."}

    return {"status": "error", "message": f"Unknown markers action: {action}"}


def handle_manage_compositor(params: dict) -> dict:
    """Compositor: enable/disable/add_node/remove_node/connect/disconnect/set_value/list_nodes."""
    action = params.get("action")
    scene = bpy.context.scene

    if action == "enable":
        scene.use_nodes = True
        return {"status": "success", "message": "Compositor enabled."}

    elif action == "disable":
        scene.use_nodes = False
        return {"status": "success", "message": "Compositor disabled."}

    if not scene.use_nodes or not scene.node_tree:
        return {"status": "error", "message": "Compositor not enabled."}

    tree = scene.node_tree

    if action == "list_nodes":
        nodes = []
        for n in tree.nodes:
            nodes.append({"name": n.name, "type": n.bl_idname, "location": list(n.location)})
        return {"status": "success", "data": nodes}

    elif action == "add_node":
        ntype = params.get("node_type")
        try:
            node = tree.nodes.new(type=ntype)
            if "location" in params:
                node.location = tuple(params["location"])
            if "name" in params:
                node.name = params["name"]
            return {"status": "success", "data": {"name": node.name}}
        except Exception as e:
            return {"status": "error", "message": f"Failed to add node: {e}"}

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
        if fn and tn:
            tree.links.new(fn.outputs[params["from_socket"]], tn.inputs[params["to_socket"]])
            return {"status": "success", "message": "Nodes connected."}
        return {"status": "error", "message": "Node(s) not found."}

    elif action == "disconnect":
        tn = tree.nodes.get(params.get("to_node"))
        if tn:
            to_socket = params.get("to_socket")
            if to_socket in tn.inputs:
                for link in tn.inputs[to_socket].links:
                    tree.links.remove(link)
                return {"status": "success", "message": "Disconnected."}
        return {"status": "error", "message": "Node or socket not found."}

    elif action == "set_value":
        node_name = params.get("name")
        node = tree.nodes.get(node_name)
        if node:
            inp = params.get("input")
            val = params.get("value")
            if inp in node.inputs:
                node.inputs[inp].default_value = val
                return {"status": "success", "message": f"Set '{inp}' on '{node_name}'."}
            # Try properties
            props = params.get("properties", {})
            for k, v in props.items():
                if hasattr(node, k):
                    setattr(node, k, v)
            return {"status": "success", "message": f"Properties set on '{node_name}'."}
        return {"status": "error", "message": f"Node '{node_name}' not found."}

    return {"status": "error", "message": f"Unknown compositor action: {action}"}


def handle_manage_view_layer(params: dict) -> dict:
    """View layers: list/create/delete/set_active/get_passes/enable_pass."""
    action = params.get("action")
    scene = bpy.context.scene

    if action == "list":
        layers = [{"name": vl.name, "use": vl.use} for vl in scene.view_layers]
        return {"status": "success", "data": layers}

    elif action == "create":
        name = params.get("name", "ViewLayer")
        vl = scene.view_layers.new(name)
        return {"status": "success", "data": {"name": vl.name}}

    elif action == "delete":
        name = params.get("name")
        vl = scene.view_layers.get(name)
        if vl and len(scene.view_layers) > 1:
            scene.view_layers.remove(vl)
            return {"status": "success", "message": f"View layer '{name}' deleted."}
        return {"status": "error", "message": "Cannot delete (not found or last layer)."}

    elif action == "set_active":
        name = params.get("name")
        vl = scene.view_layers.get(name)
        if vl:
            bpy.context.window.view_layer = vl
            return {"status": "success", "message": f"Active view layer: '{name}'."}
        return {"status": "error", "message": f"View layer '{name}' not found."}

    elif action == "get_passes":
        vl = bpy.context.view_layer
        passes = {}
        for attr in dir(vl):
            if attr.startswith('use_pass_'):
                passes[attr] = getattr(vl, attr)
        return {"status": "success", "data": passes}

    elif action == "enable_pass":
        passes = params.get("passes", {})
        vl = bpy.context.view_layer
        for k, v in passes.items():
            if hasattr(vl, k):
                setattr(vl, k, v)
        return {"status": "success", "message": "Passes updated."}

    return {"status": "error", "message": f"Unknown view_layer action: {action}"}


def handle_manage_preferences(params: dict) -> dict:
    """Preferences: get/set."""
    action = params.get("action")
    prefs = bpy.context.preferences

    if action == "get":
        data = {
            "undo_steps": prefs.edit.undo_steps,
            "theme": prefs.themes[0].name if prefs.themes else "Default",
        }
        # GPU info
        if hasattr(prefs, 'addons') and 'cycles' in prefs.addons:
            cprefs = prefs.addons['cycles'].preferences
            data["compute_device_type"] = cprefs.compute_device_type
            data["devices"] = [{"name": d.name, "use": d.use} for d in cprefs.devices]
        return {"status": "success", "data": data}

    elif action == "set":
        props = params.get("properties", {})
        if "undo_steps" in props:
            prefs.edit.undo_steps = props["undo_steps"]
        if "compute_device_type" in props:
            if 'cycles' in prefs.addons:
                cprefs = prefs.addons['cycles'].preferences
                cprefs.compute_device_type = props["compute_device_type"]
                cprefs.get_devices()
                for d in cprefs.devices:
                    d.use = True
        return {"status": "success", "message": "Preferences updated."}

    return {"status": "error", "message": f"Unknown preferences action: {action}"}


def handle_manage_addons(params: dict) -> dict:
    """Addons: list/enable/disable."""
    action = params.get("action")

    if action == "list":
        filter_enabled = params.get("filter_enabled")
        addons = []
        for mod_name in bpy.context.preferences.addons.keys():
            addons.append({"name": mod_name, "enabled": True})
        if filter_enabled is True:
            return {"status": "success", "data": addons}
        # For all known, just list enabled
        return {"status": "success", "data": addons}

    elif action == "enable":
        addon_name = params.get("addon_name")
        try:
            bpy.ops.preferences.addon_enable(module=addon_name)
            return {"status": "success", "message": f"Addon '{addon_name}' enabled."}
        except Exception as e:
            return {"status": "error", "message": f"Enable failed: {e}"}

    elif action == "disable":
        addon_name = params.get("addon_name")
        try:
            bpy.ops.preferences.addon_disable(module=addon_name)
            return {"status": "success", "message": f"Addon '{addon_name}' disabled."}
        except Exception as e:
            return {"status": "error", "message": f"Disable failed: {e}"}

    return {"status": "error", "message": f"Unknown addons action: {action}"}


def handle_batch_operations(params: dict) -> dict:
    """Batch: apply_all_transforms/set_origin/clear_parent/smooth_normals/flat_normals/shade_auto_smooth/purge_orphans/join_objects."""
    action = params.get("action")
    objects_param = params.get("objects", "selected")

    def _get_objects():
        if objects_param == "all":
            return list(bpy.data.objects)
        elif objects_param == "selected":
            return list(bpy.context.selected_objects)
        elif isinstance(objects_param, list):
            return [bpy.data.objects.get(n) for n in objects_param if bpy.data.objects.get(n)]
        return list(bpy.context.selected_objects)

    if action == "apply_all_transforms":
        objs = _get_objects()
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objs:
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        return {"status": "success", "message": f"Transforms applied to {len(objs)} objects."}

    elif action == "set_origin":
        origin_type = params.get("origin_type", "ORIGIN_GEOMETRY")
        objs = _get_objects()
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objs:
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
        bpy.ops.object.origin_set(type=origin_type)
        return {"status": "success", "message": f"Origin set for {len(objs)} objects."}

    elif action == "clear_parent":
        objs = _get_objects()
        for obj in objs:
            obj.parent = None
        return {"status": "success", "message": f"Parent cleared for {len(objs)} objects."}

    elif action == "smooth_normals":
        objs = _get_objects()
        for obj in objs:
            if obj.type == 'MESH':
                for poly in obj.data.polygons:
                    poly.use_smooth = True
                obj.data.update()
        return {"status": "success", "message": "Smooth shading applied."}

    elif action == "flat_normals":
        objs = _get_objects()
        for obj in objs:
            if obj.type == 'MESH':
                for poly in obj.data.polygons:
                    poly.use_smooth = False
                obj.data.update()
        return {"status": "success", "message": "Flat shading applied."}

    elif action == "shade_auto_smooth":
        auto_angle = params.get("auto_smooth_angle", 30.0)
        objs = _get_objects()
        for obj in objs:
            if obj.type == 'MESH':
                for poly in obj.data.polygons:
                    poly.use_smooth = True
                obj.data.update()
                # In Blender 4.x, auto smooth is via modifier or mesh property
                if hasattr(obj.data, 'use_auto_smooth'):
                    obj.data.use_auto_smooth = True
                    obj.data.auto_smooth_angle = math.radians(auto_angle)
        return {"status": "success", "message": "Auto smooth applied."}

    elif action == "purge_orphans":
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
        return {"status": "success", "message": "Orphan data purged."}

    elif action == "join_objects":
        objs = _get_objects()
        if len(objs) < 2:
            return {"status": "error", "message": "Need at least 2 objects to join."}
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objs:
            if obj.type == 'MESH':
                obj.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.object.join()
        return {"status": "success", "message": f"Objects joined into '{bpy.context.active_object.name}'."}

    return {"status": "error", "message": f"Unknown batch action: {action}"}


def handle_manage_scene_settings(params: dict) -> dict:
    """Scene: gravity, unit system/scale, frame step."""
    action = params.get("action")
    scene = bpy.context.scene

    if action == "get":
        data = {
            "gravity": list(scene.gravity),
            "use_gravity": scene.use_gravity,
            "unit_system": scene.unit_settings.system,
            "unit_scale": scene.unit_settings.scale_length,
            "frame_step": scene.frame_step,
        }
        return {"status": "success", "data": data}

    elif action == "set":
        props = params.get("properties", {})
        if "gravity" in props:
            scene.gravity = tuple(props["gravity"])
        if "use_gravity" in props:
            scene.use_gravity = props["use_gravity"]
        if "unit_system" in props:
            scene.unit_settings.system = props["unit_system"]
        if "unit_scale" in props:
            scene.unit_settings.scale_length = props["unit_scale"]
        if "frame_step" in props:
            scene.frame_step = props["frame_step"]
        return {"status": "success", "message": "Scene settings updated."}

    return {"status": "error", "message": f"Unknown scene_settings action: {action}"}


def handle_library_link(params: dict) -> dict:
    """Link/append from external .blend files."""
    action = params.get("action")
    filepath = params.get("filepath")

    if action == "list_contents":
        if not filepath:
            return {"status": "error", "message": "No filepath provided."}
        import os
        contents = {}
        try:
            with bpy.data.libraries.load(filepath) as (data_from, _):
                for attr in ['objects', 'materials', 'collections', 'node_groups', 'actions', 'worlds']:
                    items = getattr(data_from, attr, [])
                    if items:
                        contents[attr] = list(items)
        except Exception as e:
            return {"status": "error", "message": f"Failed to read library: {e}"}
        return {"status": "success", "data": contents}

    elif action in ("link", "append"):
        if not filepath:
            return {"status": "error", "message": "No filepath provided."}
        data_type = params.get("data_type", "Object")
        names = params.get("names", [])
        is_link = (action == "link")

        directory = f"{filepath}/{data_type}/"
        imported = []
        for name in names:
            try:
                bpy.ops.wm.append(
                    filepath=f"{directory}{name}",
                    directory=directory,
                    filename=name,
                    link=is_link,
                )
                imported.append(name)
            except Exception as e:
                pass

        return {"status": "success", "message": f"{'Linked' if is_link else 'Appended'} {len(imported)} items.", "data": imported}

    return {"status": "error", "message": f"Unknown library action: {action}"}


def handle_manage_custom_properties(params: dict) -> dict:
    """Custom property CRUD on objects."""
    obj_name = params.get("object")
    obj = bpy.data.objects.get(obj_name)
    if not obj:
        return {"status": "error", "message": f"Object '{obj_name}' not found."}

    action = params.get("action")

    if action == "set":
        key = params.get("key")
        val = params.get("value")
        obj[key] = val
        # Set metadata if provided
        if "_RNA_UI" not in obj:
            obj["_RNA_UI"] = {}
        ui = {}
        if "description" in params:
            ui["description"] = params["description"]
        if "min" in params:
            ui["min"] = params["min"]
        if "max" in params:
            ui["max"] = params["max"]
        if "subtype" in params:
            ui["subtype"] = params["subtype"]
        if ui:
            obj["_RNA_UI"][key] = ui
        return {"status": "success", "message": f"Property '{key}' set on '{obj_name}'."}

    elif action == "get":
        key = params.get("key")
        if key in obj:
            return {"status": "success", "data": {"key": key, "value": obj[key]}}
        return {"status": "error", "message": f"Property '{key}' not found."}

    elif action == "remove":
        key = params.get("key")
        if key in obj:
            del obj[key]
            return {"status": "success", "message": f"Property '{key}' removed."}
        return {"status": "error", "message": f"Property '{key}' not found."}

    elif action == "list":
        props = {}
        for key in obj.keys():
            if key.startswith("_"):
                continue
            props[key] = obj[key]
        return {"status": "success", "data": props}

    return {"status": "error", "message": f"Unknown custom_properties action: {action}"}


def handle_get_scene_statistics(params: dict) -> dict:
    """Detailed scene statistics."""
    stats = {
        "objects": {
            "total": len(bpy.data.objects),
            "mesh": sum(1 for o in bpy.data.objects if o.type == 'MESH'),
            "light": sum(1 for o in bpy.data.objects if o.type == 'LIGHT'),
            "camera": sum(1 for o in bpy.data.objects if o.type == 'CAMERA'),
            "curve": sum(1 for o in bpy.data.objects if o.type == 'CURVE'),
            "armature": sum(1 for o in bpy.data.objects if o.type == 'ARMATURE'),
            "empty": sum(1 for o in bpy.data.objects if o.type == 'EMPTY'),
        },
        "mesh_totals": {
            "vertices": sum(len(o.data.vertices) for o in bpy.data.objects if o.type == 'MESH' and o.data),
            "edges": sum(len(o.data.edges) for o in bpy.data.objects if o.type == 'MESH' and o.data),
            "faces": sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH' and o.data),
        },
        "materials": len(bpy.data.materials),
        "images": len(bpy.data.images),
        "actions": len(bpy.data.actions),
        "node_groups": len(bpy.data.node_groups),
        "collections": len(bpy.data.collections),
        "scenes": len(bpy.data.scenes),
    }

    # Memory estimate
    img_memory = 0
    for img in bpy.data.images:
        if img.size[0] > 0 and img.size[1] > 0:
            channels = 4  # RGBA
            bytes_per = 4 if img.is_float else 1
            img_memory += img.size[0] * img.size[1] * channels * bytes_per
    stats["image_memory_mb"] = round(img_memory / (1024 * 1024), 2)

    return {"status": "success", "data": stats}
