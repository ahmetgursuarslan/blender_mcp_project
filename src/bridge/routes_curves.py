import bpy
import math


def handle_manage_curve(params: dict) -> dict:
    """Bezier/NURBS/Poly curve CRUD with bevel/taper/fill/twist."""
    action = params.get("action")
    name = params.get("name", "Curve")

    if action == "create":
        ctype = params.get("curve_type", "BEZIER")
        loc = tuple(params.get("location", (0, 0, 0)))

        if ctype == "BEZIER":
            bpy.ops.curve.primitive_bezier_curve_add(location=loc)
        elif ctype == "NURBS":
            bpy.ops.curve.primitive_nurbs_curve_add(location=loc)
        elif ctype == "POLY":
            bpy.ops.curve.primitive_bezier_curve_add(location=loc)
            # Convert to poly
            bpy.context.active_object.data.splines[0].type = 'POLY'
        else:
            bpy.ops.curve.primitive_bezier_curve_add(location=loc)

        curve_obj = bpy.context.active_object
        curve_obj.name = name
        curve_obj.data.name = name

        # Apply properties
        props = params.get("properties", {})
        _apply_curve_props(curve_obj, props)

        # Set initial points if provided
        points = params.get("points")
        if points:
            spline = curve_obj.data.splines[0]
            _set_spline_points(spline, points, ctype)

        if "dimensions" in params:
            curve_obj.data.dimensions = params["dimensions"]
        if "bevel_object" in params:
            bevel = bpy.data.objects.get(params["bevel_object"])
            if bevel:
                curve_obj.data.bevel_object = bevel
        if "taper_object" in params:
            taper = bpy.data.objects.get(params["taper_object"])
            if taper:
                curve_obj.data.taper_object = taper

        return {"status": "success", "data": {"name": curve_obj.name}}

    elif action == "add_point":
        curve_obj = bpy.data.objects.get(name)
        if not curve_obj or curve_obj.type != 'CURVE':
            return {"status": "error", "message": f"Curve '{name}' not found."}
        spline_idx = params.get("spline_index", 0)
        if spline_idx >= len(curve_obj.data.splines):
            return {"status": "error", "message": f"Spline index {spline_idx} out of range."}

        spline = curve_obj.data.splines[spline_idx]
        point = params.get("point", [0, 0, 0])

        if spline.type == 'BEZIER':
            spline.bezier_points.add(1)
            bp = spline.bezier_points[-1]
            bp.co = tuple(point[:3])
            if len(point) >= 6:
                bp.handle_left = tuple(point[:3])
                bp.handle_right = tuple(point[3:6])
        elif spline.type in ('NURBS', 'POLY'):
            spline.points.add(1)
            p = spline.points[-1]
            p.co = tuple(point[:3]) + (1.0,)

        return {"status": "success", "message": "Point added."}

    elif action == "set_properties":
        curve_obj = bpy.data.objects.get(name)
        if not curve_obj or curve_obj.type != 'CURVE':
            return {"status": "error", "message": f"Curve '{name}' not found."}
        props = params.get("properties", {})
        _apply_curve_props(curve_obj, props)
        return {"status": "success", "message": f"Curve '{name}' properties updated."}

    elif action == "convert_to_mesh":
        curve_obj = bpy.data.objects.get(name)
        if not curve_obj or curve_obj.type != 'CURVE':
            return {"status": "error", "message": f"Curve '{name}' not found."}
        bpy.context.view_layer.objects.active = curve_obj
        curve_obj.select_set(True)
        bpy.ops.object.convert(target='MESH')
        return {"status": "success", "message": f"Curve '{name}' converted to mesh."}

    return {"status": "error", "message": f"Unknown curve action: {action}"}


def _apply_curve_props(curve_obj, props):
    """Apply curve properties."""
    curve = curve_obj.data
    prop_map = {
        "bevel_depth": "bevel_depth",
        "bevel_resolution": "bevel_resolution",
        "extrude": "extrude",
        "offset": "offset",
        "resolution_u": "resolution_u",
        "fill_mode": "fill_mode",
        "twist_mode": "twist_mode",
        "use_fill_caps": "use_fill_caps",
    }
    for k, v in props.items():
        attr = prop_map.get(k, k)
        if hasattr(curve, attr):
            try:
                setattr(curve, attr, v)
            except Exception:
                pass


def _set_spline_points(spline, points, ctype):
    """Set spline points from array."""
    if ctype == "BEZIER":
        if len(points) > len(spline.bezier_points):
            spline.bezier_points.add(len(points) - len(spline.bezier_points))
        for i, p in enumerate(points):
            if i < len(spline.bezier_points):
                spline.bezier_points[i].co = tuple(p[:3])
    else:
        if len(points) > len(spline.points):
            spline.points.add(len(points) - len(spline.points))
        for i, p in enumerate(points):
            if i < len(spline.points):
                spline.points[i].co = tuple(p[:3]) + (1.0,)


def handle_manage_text(params: dict) -> dict:
    """3D text: create/modify/convert_to_mesh."""
    action = params.get("action")
    name = params.get("name", "Text")

    if action == "create":
        loc = tuple(params.get("location", (0, 0, 0)))
        rot = tuple(params.get("rotation", (0, 0, 0)))
        bpy.ops.object.text_add(location=loc, rotation=rot)
        text_obj = bpy.context.active_object
        text_obj.name = name
        text_obj.data.body = params.get("body", "Text")
        if "size" in params:
            text_obj.data.size = params["size"]
        if "extrude" in params:
            text_obj.data.extrude = params["extrude"]
        if "bevel_depth" in params:
            text_obj.data.bevel_depth = params["bevel_depth"]
        if "resolution" in params:
            text_obj.data.resolution_u = params["resolution"]
        if "align_x" in params:
            text_obj.data.align_x = params["align_x"]
        if "align_y" in params:
            text_obj.data.align_y = params["align_y"]
        if "font_path" in params:
            try:
                font = bpy.data.fonts.load(params["font_path"])
                text_obj.data.font = font
            except Exception:
                pass
        return {"status": "success", "data": {"name": text_obj.name}}

    elif action == "modify":
        text_obj = bpy.data.objects.get(name)
        if not text_obj or text_obj.type != 'FONT':
            return {"status": "error", "message": f"Text object '{name}' not found."}
        if "body" in params:
            text_obj.data.body = params["body"]
        if "size" in params:
            text_obj.data.size = params["size"]
        if "extrude" in params:
            text_obj.data.extrude = params["extrude"]
        if "bevel_depth" in params:
            text_obj.data.bevel_depth = params["bevel_depth"]
        if "resolution" in params:
            text_obj.data.resolution_u = params["resolution"]
        if "align_x" in params:
            text_obj.data.align_x = params["align_x"]
        if "align_y" in params:
            text_obj.data.align_y = params["align_y"]
        if "location" in params:
            text_obj.location = tuple(params["location"])
        if "rotation" in params:
            text_obj.rotation_euler = tuple(params["rotation"])
        return {"status": "success", "message": f"Text '{name}' modified."}

    elif action == "convert_to_mesh":
        text_obj = bpy.data.objects.get(name)
        if not text_obj or text_obj.type != 'FONT':
            return {"status": "error", "message": f"Text object '{name}' not found."}
        bpy.context.view_layer.objects.active = text_obj
        text_obj.select_set(True)
        bpy.ops.object.convert(target='MESH')
        return {"status": "success", "message": f"Text '{name}' converted to mesh."}

    return {"status": "error", "message": f"Unknown text action: {action}"}


def handle_manage_grease_pencil(params: dict) -> dict:
    """Grease pencil: create/add_layer/add_stroke/set_material/list_layers."""
    action = params.get("action")
    name = params.get("name", "GPencil")

    if action == "create":
        loc = tuple(params.get("location", (0, 0, 0)))
        bpy.ops.object.gpencil_add(location=loc, type='EMPTY')
        gp = bpy.context.active_object
        gp.name = name
        return {"status": "success", "data": {"name": gp.name}}

    elif action == "add_layer":
        gp = bpy.data.objects.get(name)
        if not gp or gp.type != 'GPENCIL':
            return {"status": "error", "message": f"Grease Pencil '{name}' not found."}
        layer_name = params.get("layer", "Layer")
        layer = gp.data.layers.new(layer_name)
        return {"status": "success", "data": {"layer": layer.info}}

    elif action == "add_stroke":
        gp = bpy.data.objects.get(name)
        if not gp or gp.type != 'GPENCIL':
            return {"status": "error", "message": f"Grease Pencil '{name}' not found."}

        layer_name = params.get("layer")
        layer = None
        if layer_name:
            for l in gp.data.layers:
                if l.info == layer_name:
                    layer = l
                    break
        if not layer:
            layer = gp.data.layers[0] if gp.data.layers else gp.data.layers.new("Layer")

        frame_num = params.get("frame", bpy.context.scene.frame_current)
        frame = layer.frames.get(frame_num) if hasattr(layer.frames, 'get') else None
        if not frame:
            frame = layer.frames.new(frame_num)

        stroke = frame.strokes.new()
        stroke.line_width = params.get("line_width", 10)
        if "material_index" in params:
            stroke.material_index = params["material_index"]

        points = params.get("stroke_points", [])
        pressure = params.get("pressure", [])
        stroke.points.add(len(points))
        for i, pt in enumerate(points):
            stroke.points[i].co = tuple(pt[:3])
            if i < len(pressure):
                stroke.points[i].pressure = pressure[i]
            else:
                stroke.points[i].pressure = 1.0

        return {"status": "success", "message": f"Stroke added with {len(points)} points."}

    elif action == "set_material":
        gp = bpy.data.objects.get(name)
        if not gp or gp.type != 'GPENCIL':
            return {"status": "error", "message": f"Grease Pencil '{name}' not found."}
        mat_name = params.get("material_name", "GP_Material")
        mat = bpy.data.materials.get(mat_name)
        if not mat:
            mat = bpy.data.materials.new(mat_name)
            bpy.data.materials.create_gpencil_data(mat)
        if mat.name not in [m.name for m in gp.data.materials]:
            gp.data.materials.append(mat)
        props = params.get("material_properties", {})
        if mat.grease_pencil:
            gp_mat = mat.grease_pencil
            if "color" in props:
                gp_mat.color = tuple(props["color"][:4]) if len(props["color"]) >= 4 else tuple(props["color"][:3]) + (1.0,)
            if "fill_color" in props:
                fc = props["fill_color"]
                gp_mat.fill_color = tuple(fc[:4]) if len(fc) >= 4 else tuple(fc[:3]) + (1.0,)
                gp_mat.show_fill = True
        return {"status": "success", "message": f"Material '{mat_name}' set on '{name}'."}

    elif action == "list_layers":
        gp = bpy.data.objects.get(name)
        if not gp or gp.type != 'GPENCIL':
            return {"status": "error", "message": f"Grease Pencil '{name}' not found."}
        layers = []
        for l in gp.data.layers:
            layers.append({
                "name": l.info,
                "frames": len(l.frames),
                "opacity": l.opacity,
                "hide": l.hide,
            })
        return {"status": "success", "data": layers}

    return {"status": "error", "message": f"Unknown grease_pencil action: {action}"}
