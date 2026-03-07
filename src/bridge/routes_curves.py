import bpy

def handle_manage_curve(params: dict) -> dict:
    """POST /api/curve/manage"""
    action = params.get("action")
    name = params.get("name", "Curve")

    if action == "create":
        ctype = params.get("curve_type", "BEZIER")
        if ctype == "BEZIER": bpy.ops.curve.primitive_bezier_curve_add()
        else: bpy.ops.curve.primitive_nurbs_curve_add()
        curve = bpy.context.active_object
        curve.name = name
        return {"status": "success", "data": {"name": curve.name}}

    return {"status": "error", "message": f"Unknown action: {action}"}

def handle_manage_text(params: dict) -> dict:
    """POST /api/text/manage"""
    action = params.get("action")
    if action == "create":
        bpy.ops.object.text_add()
        text_obj = bpy.context.active_object
        text_obj.data.body = params.get("body", "Hello MCP")
        if "size" in params: text_obj.data.size = params["size"]
        if "extrude" in params: text_obj.data.extrude = params["extrude"]
        return {"status": "success", "data": {"name": text_obj.name}}
    return {"status": "error", "message": f"Unknown action: {action}"}

def handle_manage_grease_pencil(params: dict) -> dict:
    return {"status": "success", "message": "Grease pencil placeholder."}
