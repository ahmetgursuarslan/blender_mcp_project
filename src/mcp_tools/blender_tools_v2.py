"""
Blender MCP Tool Definitions v2.5
~65 structured tools exposed via the MCP protocol.
Each tool maps to a route in the Blender bridge addon.
"""
import mcp.types as types


def _t(name, desc, props, required=None):
    """Shorthand tool builder."""
    return types.Tool(name=name, description=desc, inputSchema={
        "type": "object", "properties": props, "required": required or []
    })


def get_blender_tools_v2() -> list[types.Tool]:
    """Returns all v2.5 Blender tool definitions."""
    return [
        # ─── Legacy / Core ───
        _t("get_blender_state", "Reads enhanced context: active/selected objects, scene stats, render engine, viewport shading, file path, blender version.", {}, []),
        _t("execute_blender_code", "Injects sandboxed Python into Blender (bpy/math/bmesh/mathutils only). Prefer structured tools when possible.",
           {"code": {"type": "string", "description": "Python script"}}, ["code"]),
        _t("take_blender_screenshot", "Captures current 3D viewport as base64 PNG.", {}, []),

        # ─── Scene & Object ───
        _t("get_scene_hierarchy", "Full scene tree: objects, types, transforms, materials, modifiers, children, collections.",
           {"max_depth": {"type": "integer", "default": 10}, "include_transform": {"type": "boolean", "default": True}}),
        _t("get_object_details", "Full object details: transform, mesh data, modifiers, materials, constraints, vertex groups.",
           {"name": {"type": "string"}, "include_modifiers": {"type": "boolean", "default": True}, "include_materials": {"type": "boolean", "default": True}}, ["name"]),
        _t("manage_object", "Object CRUD: create/delete/duplicate/rename/transform/parent/visibility/select.",
           {"action": {"type": "string", "enum": ["create", "create_empty", "delete", "duplicate", "rename", "transform", "set_parent", "set_visibility", "select"]},
            "name": {"type": "string"}, "new_name": {"type": "string"}, "primitive_type": {"type": "string", "enum": ["CUBE", "SPHERE", "CYLINDER", "PLANE", "CONE", "TORUS", "MONKEY", "CIRCLE", "GRID", "ICO_SPHERE"]},
            "location": {"type": "array", "items": {"type": "number"}}, "rotation": {"type": "array", "items": {"type": "number"}}, "scale": {"type": "array", "items": {"type": "number"}},
            "parent": {"type": "string"}, "display_type": {"type": "string"}, "hide_viewport": {"type": "boolean"}, "hide_render": {"type": "boolean"}}, ["action"]),
        _t("manage_collection", "Collection CRUD: list/create/add_object/remove_object/delete.",
           {"action": {"type": "string", "enum": ["list", "create", "add_object", "remove_object", "delete"]}, "name": {"type": "string"}, "parent": {"type": "string"}, "collection": {"type": "string"}, "object": {"type": "string"}}, ["action"]),

        # ─── Material & Shader ───
        _t("get_materials_list", "All materials with Principled BSDF values.", {}),
        _t("get_material_details", "Full shader node graph: nodes + links.", {"name": {"type": "string"}}, ["name"]),
        _t("manage_material", "Material CRUD. Properties = Principled BSDF inputs.",
           {"action": {"type": "string", "enum": ["create", "modify", "assign", "remove", "duplicate"]}, "name": {"type": "string"}, "new_name": {"type": "string"}, "assign_to": {"type": "string"}, "slot_index": {"type": "integer"},
            "properties": {"type": "object", "description": "base_color, metallic, roughness, emission_color, emission_strength, alpha, transmission_weight, ior"}}, ["action", "name"]),
        _t("manage_shader_nodes", "Shader node graph CRUD: add/remove nodes, connect/disconnect, set values.",
           {"action": {"type": "string", "enum": ["add_node", "remove_node", "connect", "disconnect", "set_value"]}, "material": {"type": "string"}, "node_type": {"type": "string"}, "name": {"type": "string"},
            "location": {"type": "array", "items": {"type": "number"}}, "from_node": {"type": "string"}, "from_socket": {"type": "string"}, "to_node": {"type": "string"}, "to_socket": {"type": "string"},
            "input": {"type": "string"}, "value": {"description": "number, array, or string"}}, ["action", "material"]),

        # ─── Modifier & Constraint ───
        _t("manage_modifier", "Modifier CRUD: add/remove/apply/set_property/move. BEVEL, SUBSURF, MIRROR, BOOLEAN, ARRAY, SOLIDIFY, etc.",
           {"action": {"type": "string", "enum": ["add", "remove", "apply", "set_property", "move_up", "move_down", "list"]}, "object": {"type": "string"}, "name": {"type": "string"}, "modifier_type": {"type": "string"}, "properties": {"type": "object"}}, ["action", "object"]),
        _t("manage_constraint", "Constraint CRUD: TRACK_TO, COPY_LOCATION, DAMPED_TRACK, etc.",
           {"action": {"type": "string", "enum": ["add", "remove", "list"]}, "object": {"type": "string"}, "name": {"type": "string"}, "constraint_type": {"type": "string"}, "properties": {"type": "object"}}, ["action", "object"]),

        # ─── Render & Visual ───
        _t("get_render_settings", "Current render settings: engine, resolution, samples, format, color mgmt.", {}),
        _t("set_render_settings", "Configure render: engine, resolution, samples, format, film transparency.",
           {"engine": {"type": "string", "enum": ["CYCLES", "BLENDER_EEVEE_NEXT"]}, "resolution_x": {"type": "integer"}, "resolution_y": {"type": "integer"}, "film_transparent": {"type": "boolean"},
            "output_format": {"type": "string"}, "fps": {"type": "integer"}, "cycles": {"type": "object"}, "eevee": {"type": "object"}, "color_management": {"type": "object"}}),
        _t("render_image", "Full Cycles/EEVEE render → base64 PNG.",
           {"filepath": {"type": "string"}, "format": {"type": "string", "enum": ["PNG", "JPEG", "OPEN_EXR"]}}),
        _t("manage_camera", "Camera CRUD: create/modify/set_active/look_at. DOF, lens, clip.",
           {"action": {"type": "string", "enum": ["create", "modify", "set_active", "look_at"]}, "name": {"type": "string"}, "location": {"type": "array", "items": {"type": "number"}}, "rotation": {"type": "array", "items": {"type": "number"}},
            "lens": {"type": "number"}, "clip_start": {"type": "number"}, "clip_end": {"type": "number"}, "dof_enabled": {"type": "boolean"}, "aperture_fstop": {"type": "number"}, "target": {"description": "Object or [x,y,z]"}}, ["action"]),
        _t("manage_light", "Light CRUD: POINT/SUN/SPOT/AREA.",
           {"action": {"type": "string", "enum": ["create", "modify", "delete"]}, "name": {"type": "string"}, "light_type": {"type": "string", "enum": ["POINT", "SUN", "SPOT", "AREA"]},
            "location": {"type": "array", "items": {"type": "number"}}, "rotation": {"type": "array", "items": {"type": "number"}}, "energy": {"type": "number"}, "color": {"type": "array", "items": {"type": "number"}},
            "size": {"type": "number"}, "shape": {"type": "string"}, "spot_size": {"type": "number"}, "use_shadow": {"type": "boolean"}}, ["action"]),

        # ─── Animation ───
        _t("get_animation_info", "Animation info: FPS, frame range, actions, fcurves.", {"object": {"type": "string"}}),
        _t("manage_keyframes", "Keyframe CRUD: insert/delete/read/clear_all.",
           {"action": {"type": "string", "enum": ["insert", "delete", "read", "clear_all"]}, "object": {"type": "string"}, "property": {"type": "string"}, "frame": {"type": "integer"}, "value": {"description": "Value"}}, ["action", "object"]),
        _t("manage_timeline", "Timeline: set_range/set_fps/set_frame/play/stop.",
           {"action": {"type": "string", "enum": ["set_range", "set_fps", "set_frame", "play", "stop"]}, "frame_start": {"type": "integer"}, "frame_end": {"type": "integer"}, "fps": {"type": "integer"}, "frame": {"type": "integer"}}, ["action"]),

        # ─── File ───
        _t("manage_file", "File: new/open/save/save_as/info.",
           {"action": {"type": "string", "enum": ["new", "open", "save", "save_as", "info"]}, "filepath": {"type": "string"}, "use_empty": {"type": "boolean"}}, ["action"]),
        _t("export_model", "Export: FBX/OBJ/GLTF/GLB/STL/USD/ABC.",
           {"format": {"type": "string", "enum": ["FBX", "OBJ", "GLTF", "GLB", "STL", "USD", "ABC"]}, "filepath": {"type": "string"}, "selected_only": {"type": "boolean"}, "apply_modifiers": {"type": "boolean"}}, ["format", "filepath"]),
        _t("import_model", "Import 3D file (auto-detects format).", {"filepath": {"type": "string"}}, ["filepath"]),

        # ─── Mesh & Physics ───
        _t("get_mesh_data", "Mesh data: verts/edges/faces counts, UVs, vertex groups, shape keys, bounding box.",
           {"name": {"type": "string"}, "include_vertices": {"type": "boolean", "default": False}}, ["name"]),
        _t("edit_mesh", "BMesh ops: subdivide/extrude/inset/bevel/merge/normals/triangulate/dissolve/smooth.",
           {"action": {"type": "string", "enum": ["subdivide", "extrude_faces", "inset_faces", "bevel_edges", "merge_vertices", "flip_normals", "recalculate_normals", "triangulate", "dissolve_limited", "smooth_vertices"]},
            "object": {"type": "string"}, "faces": {"description": "'all' or indices"}, "edges": {"description": "'all' or indices"},
            "offset": {"type": "array", "items": {"type": "number"}}, "thickness": {"type": "number"}, "depth": {"type": "number"}, "width": {"type": "number"}, "segments": {"type": "integer"},
            "cuts": {"type": "integer"}, "distance": {"type": "number"}, "angle_limit": {"type": "number"}, "factor": {"type": "number"}, "repeat": {"type": "integer"}}, ["action", "object"]),
        _t("manage_physics", "Physics: RIGID_BODY/SOFT_BODY/CLOTH/PARTICLE_SYSTEM.",
           {"action": {"type": "string", "enum": ["add", "remove", "bake"]}, "object": {"type": "string"}, "physics_type": {"type": "string", "enum": ["RIGID_BODY", "SOFT_BODY", "CLOTH", "PARTICLE_SYSTEM"]},
            "rigid_body_type": {"type": "string", "enum": ["ACTIVE", "PASSIVE"]}, "properties": {"type": "object"}}, ["action", "object"]),

        # ═══════════════ v2.5 — Extended ═══════════════

        # ─── Geometry Nodes ───
        _t("manage_geometry_nodes", "GeoNodes modifier: create/read/set_input/get_inputs/apply/delete/set_node_group.",
           {"action": {"type": "string", "enum": ["create", "read", "set_input", "get_inputs", "apply", "delete", "set_node_group"]}, "object": {"type": "string"}, "modifier_name": {"type": "string"},
            "node_group": {"type": "string"}, "inputs": {"type": "object"}}, ["action"]),
        _t("manage_node_group", "Node group CRUD for GeometryNodeTree/ShaderNodeTree/CompositorNodeTree.",
           {"action": {"type": "string", "enum": ["list", "create", "read", "duplicate", "delete"]}, "name": {"type": "string"}, "tree_type": {"type": "string"}, "new_name": {"type": "string"}}, ["action"]),

        # ─── World / Environment ───
        _t("manage_world", "World: solid color, HDRI (rotation), Nishita/Hosek-Wilkie sky, strength, volumetric fog.",
           {"action": {"type": "string", "enum": ["get", "set_color", "set_hdri", "set_sky", "set_strength", "set_volume"]},
            "color": {"type": "array", "items": {"type": "number"}}, "hdri_path": {"type": "string"}, "strength": {"type": "number"},
            "rotation": {"type": "number"}, "density": {"type": "number"},
            "sky_params": {"type": "object", "description": "sky_type, sun_elevation, sun_rotation, air_density, dust_density, ozone_density, altitude"}}, ["action"]),

        # ─── Armature & Rigging ───
        _t("manage_armature", "Full rigging: create/add_bone/remove_bone/list_bones/rename_bone/set_bone_parent/set_pose/reset_pose/set_ik/parent_mesh.",
           {"action": {"type": "string", "enum": ["create", "add_bone", "remove_bone", "list_bones", "rename_bone", "set_bone_parent", "set_pose", "reset_pose", "set_ik", "parent_mesh"]},
            "name": {"type": "string"}, "bone_name": {"type": "string"}, "new_name": {"type": "string"},
            "head": {"type": "array", "items": {"type": "number"}}, "tail": {"type": "array", "items": {"type": "number"}},
            "parent_bone": {"type": "string"}, "connected": {"type": "boolean"}, "roll": {"type": "number"},
            "location": {"type": "array", "items": {"type": "number"}}, "rotation": {"type": "array", "items": {"type": "number"}}, "scale": {"type": "array", "items": {"type": "number"}},
            "ik_target": {"type": "string"}, "chain_length": {"type": "integer"}, "pole_target": {"type": "string"},
            "mesh": {"type": "string"}, "method": {"type": "string", "enum": ["ARMATURE_AUTO", "ARMATURE_NAME", "ARMATURE_ENVELOPE"]}}, ["action"]),
        _t("manage_weight_paint", "Weight painting: auto_weights/assign_vertex_group/normalize/clean/get_weights/list_groups/remove_group.",
           {"action": {"type": "string", "enum": ["auto_weights", "assign_vertex_group", "normalize", "clean", "get_weights", "list_groups", "remove_group"]},
            "object": {"type": "string"}, "armature": {"type": "string"}, "bone": {"type": "string"}, "group": {"type": "string"},
            "vertices": {"type": "array", "items": {"type": "integer"}}, "weight": {"type": "number"}, "threshold": {"type": "number"}}, ["action", "object"]),

        # ─── UV Mapping ───
        _t("manage_uv", "UV: unwrap/smart_project/cube_project/cylinder_project/sphere_project/pack/create_layer/remove_layer/list_layers.",
           {"action": {"type": "string", "enum": ["unwrap", "smart_project", "cube_project", "cylinder_project", "sphere_project", "pack", "create_layer", "remove_layer", "list_layers"]},
            "object": {"type": "string"}, "uv_layer": {"type": "string"}, "params": {"type": "object"}}, ["action"]),

        # ─── Image Management ───
        _t("manage_images", "Image CRUD: load/create/save/pack/unpack/list/assign_to_node/delete.",
           {"action": {"type": "string", "enum": ["load", "create", "save", "pack", "unpack", "list", "assign_to_node", "delete"]},
            "name": {"type": "string"}, "filepath": {"type": "string"}, "width": {"type": "integer"}, "height": {"type": "integer"},
            "color": {"type": "array", "items": {"type": "number"}}, "is_float": {"type": "boolean"},
            "material": {"type": "string"}, "node_name": {"type": "string"}}, ["action"]),

        # ─── Texture Baking ───
        _t("manage_texture_bake", "Bake: DIFFUSE/NORMAL/AO/ROUGHNESS/EMIT/COMBINED/SHADOW.",
           {"action": {"type": "string", "enum": ["setup", "bake"]}, "object": {"type": "string"},
            "bake_type": {"type": "string", "enum": ["DIFFUSE", "NORMAL", "AO", "ROUGHNESS", "EMIT", "COMBINED", "SHADOW"]},
            "resolution": {"type": "integer"}, "margin": {"type": "integer"}, "samples": {"type": "integer"},
            "output_path": {"type": "string"}, "use_selected_to_active": {"type": "boolean"}, "cage_extrusion": {"type": "number"}}, ["action"]),

        # ─── Curves ───
        _t("manage_curve", "Bezier/NURBS/Poly curve CRUD with bevel/taper/fill/twist.",
           {"action": {"type": "string", "enum": ["create", "add_point", "set_properties", "convert_to_mesh"]},
            "name": {"type": "string"}, "curve_type": {"type": "string", "enum": ["BEZIER", "NURBS", "POLY"]},
            "location": {"type": "array", "items": {"type": "number"}}, "points": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}},
            "properties": {"type": "object"}, "taper_object": {"type": "string"}, "bevel_object": {"type": "string"},
            "spline_index": {"type": "integer"}, "point": {"type": "array", "items": {"type": "number"}}, "dimensions": {"type": "string", "enum": ["2D", "3D"]}}, ["action"]),

        # ─── 3D Text ───
        _t("manage_text", "3D text: create/modify/convert_to_mesh. Font, size, extrude, bevel, alignment.",
           {"action": {"type": "string", "enum": ["create", "modify", "convert_to_mesh"]},
            "name": {"type": "string"}, "body": {"type": "string"}, "font_path": {"type": "string"}, "size": {"type": "number"},
            "extrude": {"type": "number"}, "bevel_depth": {"type": "number"}, "align_x": {"type": "string"}, "align_y": {"type": "string"},
            "resolution": {"type": "integer"}, "location": {"type": "array", "items": {"type": "number"}}, "rotation": {"type": "array", "items": {"type": "number"}}}, ["action"]),

        # ─── Grease Pencil ───
        _t("manage_grease_pencil", "2D drawing/annotation: create/add_layer/add_stroke/set_material/list_layers.",
           {"action": {"type": "string", "enum": ["create", "add_layer", "add_stroke", "set_material", "list_layers"]},
            "name": {"type": "string"}, "layer": {"type": "string"}, "frame": {"type": "integer"},
            "stroke_points": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}}, "pressure": {"type": "array", "items": {"type": "number"}},
            "line_width": {"type": "integer"}, "material_index": {"type": "integer"},
            "material_name": {"type": "string"}, "material_properties": {"type": "object"}, "location": {"type": "array", "items": {"type": "number"}}}, ["action"]),

        # ─── Shape Keys ───
        _t("manage_shape_keys", "Shape key CRUD: list/create/delete/set_value/set_key(keyframe).",
           {"action": {"type": "string", "enum": ["list", "create", "delete", "set_value", "set_key"]},
            "object": {"type": "string"}, "name": {"type": "string"}, "value": {"type": "number"}, "from_mix": {"type": "boolean"}, "frame": {"type": "integer"}}, ["action", "object"]),

        # ─── NLA Editor ───
        _t("manage_nla", "Non-linear animation: list_tracks/push_action/create_strip/mute_track/solo_track.",
           {"action": {"type": "string", "enum": ["list_tracks", "push_action", "create_strip", "mute_track", "solo_track"]},
            "object": {"type": "string"}, "track_name": {"type": "string"}, "action_name": {"type": "string"},
            "frame_start": {"type": "integer"}, "blend_type": {"type": "string", "enum": ["REPLACE", "COMBINE", "ADD", "SUBTRACT"]},
            "influence": {"type": "number"}, "repeat": {"type": "number"}, "scale": {"type": "number"}, "mute": {"type": "boolean"}}, ["action", "object"]),

        # ─── Drivers ───
        _t("manage_drivers", "Expression-based drivers: add/remove/list.",
           {"action": {"type": "string", "enum": ["add", "remove", "list"]}, "object": {"type": "string"},
            "data_path": {"type": "string"}, "array_index": {"type": "integer"},
            "driver_type": {"type": "string", "enum": ["SCRIPTED", "AVERAGE", "SUM", "MIN", "MAX"]},
            "expression": {"type": "string"}, "variables": {"type": "array", "items": {"type": "object"}}}, ["action", "object"]),

        # ─── Timeline Markers ───
        _t("manage_markers", "Timeline markers: add/remove/list/move. Camera binding.",
           {"action": {"type": "string", "enum": ["add", "remove", "list", "move"]},
            "name": {"type": "string"}, "frame": {"type": "integer"}, "camera": {"type": "string"}}, ["action"]),

        # ─── Compositor ───
        _t("manage_compositor", "Compositor node graph: enable/disable/add_node/remove_node/connect/disconnect/set_value/list_nodes.",
           {"action": {"type": "string", "enum": ["enable", "disable", "add_node", "remove_node", "connect", "disconnect", "set_value", "list_nodes"]},
            "node_type": {"type": "string"}, "name": {"type": "string"}, "location": {"type": "array", "items": {"type": "number"}},
            "from_node": {"type": "string"}, "from_socket": {"type": "string"}, "to_node": {"type": "string"}, "to_socket": {"type": "string"},
            "input": {"type": "string"}, "value": {"description": "any"}, "properties": {"type": "object"}}, ["action"]),

        # ─── View Layers ───
        _t("manage_view_layer", "View layer: list/create/delete/set_active/get_passes/enable_pass.",
           {"action": {"type": "string", "enum": ["list", "create", "delete", "set_active", "get_passes", "enable_pass"]},
            "name": {"type": "string"}, "passes": {"type": "object"}}, ["action"]),

        # ─── Preferences ───
        _t("manage_preferences", "Blender preferences: undo steps, GPU/compute device.",
           {"action": {"type": "string", "enum": ["get", "set"]}, "properties": {"type": "object"}}, ["action"]),

        # ─── Add-on Management ───
        _t("manage_addons", "Addons: list/enable/disable.",
           {"action": {"type": "string", "enum": ["list", "enable", "disable"]}, "addon_name": {"type": "string"}, "filter_enabled": {"type": "boolean"}}, ["action"]),

        # ─── Batch Operations ───
        _t("batch_operations", "Batch: apply_all_transforms/set_origin/clear_parent/smooth_normals/flat_normals/shade_auto_smooth/purge_orphans/join_objects.",
           {"action": {"type": "string", "enum": ["apply_all_transforms", "set_origin", "clear_parent", "smooth_normals", "flat_normals", "shade_auto_smooth", "purge_orphans", "join_objects"]},
            "objects": {"description": "'all', 'selected', or array of names"}, "origin_type": {"type": "string"}, "auto_smooth_angle": {"type": "number"}}, ["action"]),

        # ─── Scene Settings ───
        _t("manage_scene_settings", "Scene: gravity, unit system/scale, frame step.",
           {"action": {"type": "string", "enum": ["get", "set"]}, "properties": {"type": "object"}}, ["action"]),

        # ─── Library Link/Append ───
        _t("library_link", "Link/append from external .blend files.",
           {"action": {"type": "string", "enum": ["link", "append", "list_contents"]}, "filepath": {"type": "string"},
            "data_type": {"type": "string", "enum": ["Object", "Material", "Collection", "NodeTree", "Action", "World"]},
            "names": {"type": "array", "items": {"type": "string"}}}, ["action"]),

        # ─── Custom Properties ───
        _t("manage_custom_properties", "Custom property metadata on objects.",
           {"action": {"type": "string", "enum": ["set", "get", "remove", "list"]}, "object": {"type": "string"},
            "key": {"type": "string"}, "value": {"description": "Any JSON value"}, "description": {"type": "string"},
            "min": {"type": "number"}, "max": {"type": "number"}, "subtype": {"type": "string"}}, ["action", "object"]),

        # ─── Scene Statistics ───
        _t("get_scene_statistics", "Detailed stats: objects, verts, edges, faces, materials, images, image memory, actions, node groups, orphan data.", {}),
    ]
