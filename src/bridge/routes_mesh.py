import bpy
import bmesh
from mathutils import Vector


def handle_get_mesh_data(params: dict) -> dict:
    """Mesh data: verts/edges/faces counts, UVs, vertex groups, shape keys, bounding box."""
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
        "has_shape_keys": mesh.shape_keys is not None,
        "is_smooth": any(p.use_smooth for p in mesh.polygons) if mesh.polygons else False,
    }

    if mesh.shape_keys:
        data["shape_keys"] = [kb.name for kb in mesh.shape_keys.key_blocks]

    # Bounding box
    if obj.bound_box:
        bb = [list(v) for v in obj.bound_box]
        data["bounding_box"] = {
            "min": [min(v[i] for v in bb) for i in range(3)],
            "max": [max(v[i] for v in bb) for i in range(3)],
        }

    if params.get("include_vertices", False):
        max_verts = min(len(mesh.vertices), 5000)
        data["vertices"] = [list(v.co) for v in mesh.vertices[:max_verts]]
        if len(mesh.vertices) > max_verts:
            data["vertices_truncated"] = True

    return {"status": "success", "data": data}


def handle_edit_mesh(params: dict) -> dict:
    """BMesh ops: subdivide/extrude/inset/bevel/merge/normals/triangulate/dissolve/smooth."""
    name = params.get("object")
    obj = bpy.data.objects.get(name)
    if not obj or obj.type != 'MESH':
        return {"status": "error", "message": f"Mesh object '{name}' not found."}

    action = params.get("action")

    # Ensure we're in object mode before bmesh operations
    if bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()

    try:
        if action == "subdivide":
            cuts = params.get("cuts", 1)
            bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)

        elif action == "extrude_faces":
            faces_param = params.get("faces", "all")
            if faces_param == "all":
                faces = bm.faces[:]
            elif isinstance(faces_param, list):
                faces = [bm.faces[i] for i in faces_param if i < len(bm.faces)]
            else:
                faces = bm.faces[:]

            res = bmesh.ops.extrude_face_region(bm, geom=faces)
            verts = [v for v in res['geom'] if isinstance(v, bmesh.types.BMVert)]
            offset = params.get("offset", [0, 0, 0.5])
            bmesh.ops.translate(bm, vec=Vector(offset), verts=verts)

        elif action == "inset_faces":
            thickness = params.get("thickness", 0.1)
            depth = params.get("depth", 0.0)
            faces_param = params.get("faces", "all")
            if faces_param == "all":
                faces = bm.faces[:]
            elif isinstance(faces_param, list):
                faces = [bm.faces[i] for i in faces_param if i < len(bm.faces)]
            else:
                faces = bm.faces[:]
            bmesh.ops.inset_individual(bm, faces=faces, thickness=thickness, depth=depth)

        elif action == "bevel_edges":
            width = params.get("width", 0.1)
            segments = params.get("segments", 1)
            edges_param = params.get("edges", "all")
            if edges_param == "all":
                edges = bm.edges[:]
            elif isinstance(edges_param, list):
                edges = [bm.edges[i] for i in edges_param if i < len(bm.edges)]
            else:
                edges = bm.edges[:]
            bmesh.ops.bevel(bm, geom=edges, offset=width, segments=segments, affect='EDGES')

        elif action == "merge_vertices":
            distance = params.get("distance", 0.001)
            bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=distance)

        elif action == "flip_normals":
            faces_param = params.get("faces", "all")
            if faces_param == "all":
                faces = bm.faces[:]
            else:
                faces = [bm.faces[i] for i in faces_param if i < len(bm.faces)]
            bmesh.ops.reverse_faces(bm, faces=faces)

        elif action == "recalculate_normals":
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

        elif action == "triangulate":
            bmesh.ops.triangulate(bm, faces=bm.faces[:])

        elif action == "dissolve_limited":
            angle_limit = params.get("angle_limit", 0.0873)  # ~5 degrees
            bmesh.ops.dissolve_limit(bm, angle_limit=angle_limit, verts=bm.verts[:], edges=bm.edges[:])

        elif action == "smooth_vertices":
            factor = params.get("factor", 0.5)
            repeat = params.get("repeat", 1)
            for _ in range(repeat):
                bmesh.ops.smooth_vert(bm, verts=bm.verts[:], factor=factor)

        else:
            bm.free()
            return {"status": "error", "message": f"Unknown edit_mesh action: {action}"}

        bm.to_mesh(obj.data)
        obj.data.update()

        return {"status": "success", "message": f"Action '{action}' applied to '{name}'.", "data": {
            "vertices": len(obj.data.vertices),
            "edges": len(obj.data.edges),
            "faces": len(obj.data.polygons),
        }}
    except Exception as e:
        return {"status": "error", "message": f"edit_mesh '{action}' failed: {e}"}
    finally:
        bm.free()


def handle_manage_physics(params: dict) -> dict:
    """Physics: RIGID_BODY/SOFT_BODY/CLOTH/PARTICLE_SYSTEM."""
    name = params.get("object")
    obj = bpy.data.objects.get(name)
    if not obj:
        return {"status": "error", "message": f"Object '{name}' not found."}

    action = params.get("action")
    ptype = params.get("physics_type", "RIGID_BODY")

    if action == "add":
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        if ptype == "RIGID_BODY":
            bpy.ops.rigidbody.object_add()
            if "rigid_body_type" in params:
                obj.rigid_body.type = params["rigid_body_type"]
            props = params.get("properties", {})
            if obj.rigid_body:
                for k, v in props.items():
                    if hasattr(obj.rigid_body, k):
                        setattr(obj.rigid_body, k, v)
        elif ptype == "SOFT_BODY":
            bpy.ops.object.modifier_add(type='SOFT_BODY')
        elif ptype == "CLOTH":
            bpy.ops.object.modifier_add(type='CLOTH')
        elif ptype == "PARTICLE_SYSTEM":
            obj.modifiers.new("Particles", 'PARTICLE_SYSTEM')
        return {"status": "success", "message": f"Added {ptype} to '{name}'."}

    elif action == "remove":
        if ptype == "RIGID_BODY" and obj.rigid_body:
            bpy.context.view_layer.objects.active = obj
            bpy.ops.rigidbody.object_remove()
        else:
            for mod in obj.modifiers:
                if mod.type in ('SOFT_BODY', 'CLOTH', 'PARTICLE_SYSTEM'):
                    obj.modifiers.remove(mod)
                    break
        return {"status": "success", "message": f"Removed {ptype} from '{name}'."}

    elif action == "bake":
        bpy.context.view_layer.objects.active = obj
        try:
            bpy.ops.ptcache.bake_all(bake=True)
            return {"status": "success", "message": "Physics baked."}
        except Exception as e:
            return {"status": "error", "message": f"Bake failed: {e}"}

    return {"status": "error", "message": f"Unknown physics action: {action}"}
