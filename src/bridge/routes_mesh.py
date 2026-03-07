import bpy
import bmesh

def handle_get_mesh_data(params: dict) -> dict:
    """GET /api/mesh/data"""
    name = params.get("name")
    obj = bpy.data.objects.get(name)
    if not obj or obj.type != 'MESH':
        return {"status": "error", "message": f"Mesh object '{name}' not found."}

    mesh = obj.data
    data = {
        "vertices_count": len(mesh.vertices),
        "edges_count": len(mesh.edges),
        "faces_count": len(mesh.polygons),
        "uv_layers": [l.name for l in mesh.uv_layers],
        "vertex_groups": [g.name for g in obj.vertex_groups],
    }
    
    if params.get("include_vertices", False):
        data["vertices"] = [list(v.co) for v in mesh.vertices]

    return {"status": "success", "data": data}

def handle_edit_mesh(params: dict) -> dict:
    """POST /api/mesh/edit"""
    name = params.get("object")
    obj = bpy.data.objects.get(name)
    if not obj or obj.type != 'MESH':
        return {"status": "error", "message": f"Mesh object '{name}' not found."}

    action = params.get("action")
    bm = bmesh.new()
    bm.from_mesh(obj.data)

    try:
        if action == "subdivide":
            cuts = params.get("cuts", 1)
            bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=cuts, use_grid_fill=True)
        
        elif action == "extrude_faces":
            faces = bm.faces
            # selective extrusion logic if needed, here we do all for simplicity
            res = bmesh.ops.extrude_face_region(bm, geom=faces)
            verts = [v for v in res['geom'] if isinstance(v, bmesh.types.BMVert)]
            offset = params.get("offset", (0, 0, 0))
            bmesh.ops.translate(bm, vec=offset, verts=verts)

        elif action == "inset_faces":
            thickness = params.get("thickness", 0.1)
            bmesh.ops.inset_individual_faces(bm, faces=bm.faces, thickness=thickness)

        bm.to_mesh(obj.data)
        obj.data.update()
        return {"status": "success", "message": f"Action '{action}' applied."}
    finally:
        bm.free()

def handle_manage_physics(params: dict) -> dict:
    """POST /api/physics/manage"""
    name = params.get("object")
    obj = bpy.data.objects.get(name)
    if not obj: return {"status": "error", "message": f"Object '{name}' not found."}

    action = params.get("action")
    ptype = params.get("physics_type", "RIGID_BODY")

    if action == "add":
        bpy.context.view_layer.objects.active = obj
        if ptype == "RIGID_BODY":
            bpy.ops.rigidbody.object_add()
            if "rigid_body_type" in params: obj.rigid_body.type = params["rigid_body_type"]
        elif ptype == "CLOTH": bpy.ops.object.modifier_add(type='CLOTH')
        elif ptype == "PARTICLE_SYSTEM": obj.modifiers.new("Particles", 'PARTICLE_SYSTEM')
        return {"status": "success", "message": f"Added {ptype} to '{name}'."}

    return {"status": "error", "message": f"Unknown action: {action}"}
