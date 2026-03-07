# MCP Tools Reference

> Complete API reference for all **54 tools** exposed by the Blender Expert MCP Server v2.5.

---

## Tool Categories

| # | Category | Count | Tools |
|:-:|----------|:-----:|-------|
| 1 | Scene & Objects | 5 | `get_blender_state`, `get_scene_hierarchy`, `get_scene_statistics`, `get_object_details`, `manage_object`, `manage_collection` |
| 2 | Mesh & Editing | 3 | `get_mesh_data`, `edit_mesh`, `batch_operations` |
| 3 | Materials & Shaders | 4 | `get_materials_list`, `get_material_details`, `manage_material`, `manage_shader_nodes` |
| 4 | Modifiers & Constraints | 2 | `manage_modifier`, `manage_constraint` |
| 5 | Render, Camera & Lights | 5 | `get_render_settings`, `set_render_settings`, `render_image`, `manage_camera`, `manage_light` |
| 6 | Animation & Timeline | 5 | `get_animation_info`, `manage_keyframes`, `manage_timeline`, `manage_nla`, `manage_markers` |
| 7 | File & I/O | 4 | `manage_file`, `export_model`, `import_model`, `library_link` |
| 8 | World & Environment | 1 | `manage_world` |
| 9 | Geometry Nodes | 2 | `manage_geometry_nodes`, `manage_node_group` |
| 10 | Armature & Rigging | 2 | `manage_armature`, `manage_weight_paint` |
| 11 | UV & Textures | 3 | `manage_uv`, `manage_images`, `manage_texture_bake` |
| 12 | Curves, Text & Grease Pencil | 3 | `manage_curve`, `manage_text`, `manage_grease_pencil` |
| 13 | Advanced Animation | 3 | `manage_shape_keys`, `manage_drivers`, `manage_custom_properties` |
| 14 | Compositor & View Layers | 2 | `manage_compositor`, `manage_view_layer` |
| 15 | System & Preferences | 3 | `manage_preferences`, `manage_addons`, `manage_scene_settings` |
| 16 | Physics | 1 | `manage_physics` |
| 17 | Legacy / Low-Level | 3 | `get_blender_state`, `execute_blender_code`, `take_blender_screenshot` |
| 18 | Documentation | 3 | `search_blender_manual`, `read_specific_page`, `update_index` |

---

## 1. Scene & Objects

### `get_blender_state`
Read the current scene context. **Call this first to verify the bridge is alive.**

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| _(none)_ | — | — | No parameters |

**Returns:** `active_object`, `selected_objects`, `scene_polycount`, `current_frame`, `render_engine`, `viewport_shading`, `file_path`, `blender_version`

---

### `get_scene_hierarchy`
Full scene tree with objects, types, transforms, materials, modifiers, children, collections.

| Parameter | Type | Required | Default | Description |
|-----------|------|:--------:|:-------:|-------------|
| `include_transform` | bool | No | `true` | Include location/rotation/scale |
| `max_depth` | int | No | `10` | Maximum hierarchy depth |

---

### `get_scene_statistics`
Detailed stats: total objects, vertices, edges, faces, materials, images, memory, actions, orphan data.

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| _(none)_ | — | — | No parameters |

---

### `get_object_details`
Full object details: transform, mesh data, modifiers, materials, constraints, vertex groups.

| Parameter | Type | Required | Default | Description |
|-----------|------|:--------:|:-------:|-------------|
| `name` | string | **Yes** | — | Object name |
| `include_modifiers` | bool | No | `true` | Include modifier list |
| `include_materials` | bool | No | `true` | Include material slots |

---

### `manage_object`
Object CRUD: create, delete, duplicate, rename, transform, parent, visibility, select.

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `action` | enum | **Yes** | `create`, `create_empty`, `delete`, `duplicate`, `rename`, `transform`, `set_parent`, `set_visibility`, `select` |
| `primitive_type` | enum | For `create` | `CUBE`, `SPHERE`, `CYLINDER`, `PLANE`, `CONE`, `TORUS`, `MONKEY`, `CIRCLE`, `GRID`, `ICO_SPHERE` |
| `name` | string | Varies | Object name |
| `new_name` | string | For `rename` | New name |
| `location` | [x,y,z] | No | World position |
| `rotation` | [x,y,z] | No | Euler rotation (radians) |
| `scale` | [x,y,z] | No | Scale factor |
| `parent` | string | For `set_parent` | Parent object name |
| `hide_viewport` | bool | For `set_visibility` | Hide in viewport |
| `hide_render` | bool | For `set_visibility` | Hide in render |

---

### `manage_collection`
Collection CRUD: list, create, add/remove objects, delete.

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `action` | enum | **Yes** | `list`, `create`, `add_object`, `remove_object`, `delete` |
| `name` | string | Varies | Collection name |
| `collection` | string | Varies | Target collection |
| `object` | string | Varies | Object to add/remove |
| `parent` | string | No | Parent collection |

---

## 2. Mesh & Editing

### `get_mesh_data`
Mesh data: vertex/edge/face counts, UVs, vertex groups, shape keys, bounding box.

| Parameter | Type | Required | Default | Description |
|-----------|------|:--------:|:-------:|-------------|
| `name` | string | **Yes** | — | Mesh object name |
| `include_vertices` | bool | No | `false` | Include vertex coordinates |

---

### `edit_mesh`
BMesh operations: subdivide, extrude, inset, bevel, merge, normals, triangulate, dissolve, smooth.

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `action` | enum | **Yes** | `subdivide`, `extrude_faces`, `inset_faces`, `bevel_edges`, `merge_vertices`, `flip_normals`, `recalculate_normals`, `triangulate`, `dissolve_limited`, `smooth_vertices` |
| `object` | string | **Yes** | Target mesh object |
| `faces` | array/string | No | Face indices or `'all'` |
| `edges` | array/string | No | Edge indices or `'all'` |
| `cuts` | int | No | Subdivision cuts |
| `segments` | int | No | Bevel segments |
| `thickness` | float | No | Inset thickness |
| `depth` | float | No | Extrude depth |
| `width` | float | No | Bevel width |
| `offset` | [x,y,z] | No | Extrude offset |
| `distance` | float | No | Merge distance |
| `factor` | float | No | Smooth factor |
| `angle_limit` | float | No | Dissolve angle limit |
| `repeat` | int | No | Smooth iterations |

---

### `batch_operations`
Bulk operations across multiple objects.

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `action` | enum | **Yes** | `apply_all_transforms`, `set_origin`, `clear_parent`, `smooth_normals`, `flat_normals`, `shade_auto_smooth`, `purge_orphans`, `join_objects` |
| `objects` | array/string | No | `'all'`, `'selected'`, or array of names |
| `origin_type` | string | No | Origin type for `set_origin` |
| `auto_smooth_angle` | float | No | Angle for auto smooth |

---

## 3. Materials & Shaders

### `get_materials_list`
All materials with their Principled BSDF values. No parameters.

### `get_material_details`
Full shader node graph: nodes + links for a specific material.

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `name` | string | **Yes** | Material name |

### `manage_material`
Material CRUD. Properties map directly to Principled BSDF inputs.

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `action` | enum | **Yes** | `create`, `modify`, `assign`, `remove`, `duplicate` |
| `name` | string | **Yes** | Material name |
| `assign_to` | string | For `assign` | Target object name |
| `new_name` | string | For `duplicate` | New material name |
| `slot_index` | int | No | Material slot index |
| `properties` | object | No | See below |

**Properties Object:**
| Property | Type | Range | Description |
|----------|------|:-----:|-------------|
| `base_color` | [R,G,B,A] | 0-1 | Surface color |
| `metallic` | float | 0-1 | Metallic factor |
| `roughness` | float | 0-1 | Surface roughness |
| `emission_color` | [R,G,B,A] | 0-1 | Emission color |
| `emission_strength` | float | 0+ | Emission intensity |
| `alpha` | float | 0-1 | Opacity |
| `transmission_weight` | float | 0-1 | Glass transparency |
| `ior` | float | 1-3 | Index of refraction |

### `manage_shader_nodes`
Shader node graph CRUD.

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `action` | enum | **Yes** | `add_node`, `remove_node`, `connect`, `disconnect`, `set_value` |
| `material` | string | **Yes** | Material name |
| `node_type` | string | For `add_node` | Blender node type (e.g., `ShaderNodeTexNoise`) |
| `name` | string | Varies | Node name |
| `from_node` | string | For `connect` | Source node name |
| `from_socket` | string | For `connect` | Source socket name |
| `to_node` | string | For `connect` | Target node name |
| `to_socket` | string | For `connect` | Target socket name |
| `input` | string | For `set_value` | Input name |
| `value` | any | For `set_value` | Input value |
| `location` | [x,y] | No | Node position |

---

## 4. Modifiers & Constraints

### `manage_modifier`

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `action` | enum | **Yes** | `add`, `remove`, `apply`, `set_property`, `move_up`, `move_down`, `list` |
| `object` | string | **Yes** | Target object |
| `modifier_type` | string | For `add` | `BEVEL`, `SUBSURF`, `MIRROR`, `BOOLEAN`, `ARRAY`, `SOLIDIFY`, `SHRINKWRAP`, `DECIMATE`, `WIREFRAME` |
| `name` | string | Varies | Modifier name |
| `properties` | object | For `set_property` | Modifier-specific properties |

### `manage_constraint`

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `action` | enum | **Yes** | `add`, `remove`, `list` |
| `object` | string | **Yes** | Target object |
| `constraint_type` | string | For `add` | `TRACK_TO`, `COPY_LOCATION`, `DAMPED_TRACK`, etc. |
| `name` | string | Varies | Constraint name |
| `properties` | object | No | Constraint properties |

---

## 5. Render, Camera & Lights

### `get_render_settings`
Current render settings. No parameters.

### `set_render_settings`

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `engine` | enum | No | `CYCLES`, `BLENDER_EEVEE_NEXT` |
| `resolution_x` | int | No | Render width (px) |
| `resolution_y` | int | No | Render height (px) |
| `output_format` | string | No | `PNG`, `JPEG`, `OPEN_EXR`, `FFMPEG` |
| `film_transparent` | bool | No | Transparent background |
| `fps` | int | No | Frames per second |
| `cycles` | object | No | `{ samples, use_denoising, denoiser, max_bounces }` |
| `eevee` | object | No | `{ samples, use_bloom }` |
| `color_management` | object | No | `{ view_transform, look }` |

### `render_image`

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `filepath` | string | No | Save path (omit for base64 return) |
| `format` | enum | No | `PNG`, `JPEG`, `OPEN_EXR` |

### `manage_camera`

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `action` | enum | **Yes** | `create`, `modify`, `set_active`, `look_at` |
| `name` | string | No | Camera name |
| `location` | [x,y,z] | No | Position |
| `rotation` | [x,y,z] | No | Euler rotation |
| `lens` | float | No | Focal length (mm) |
| `clip_start` | float | No | Near clip |
| `clip_end` | float | No | Far clip |
| `dof_enabled` | bool | No | Depth of field |
| `aperture_fstop` | float | No | F-stop for DOF |
| `target` | string/array | For `look_at` | Object name or [x,y,z] |

### `manage_light`

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `action` | enum | **Yes** | `create`, `modify`, `delete` |
| `light_type` | enum | For `create` | `POINT`, `SUN`, `SPOT`, `AREA` |
| `name` | string | Varies | Light name |
| `location` | [x,y,z] | No | Position |
| `rotation` | [x,y,z] | No | Orientation |
| `energy` | float | No | Intensity (watts) |
| `color` | [R,G,B] | No | Light color |
| `size` | float | No | Area light size |
| `spot_size` | float | No | Spot cone angle |
| `shape` | string | No | Area light shape |
| `use_shadow` | bool | No | Cast shadows |

---

## 6. Animation & Timeline

### `get_animation_info`
| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `object` | string | No | Specific object (omit for scene-level) |

### `manage_keyframes`
| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `action` | enum | **Yes** | `insert`, `delete`, `read`, `clear_all` |
| `object` | string | **Yes** | Target object |
| `property` | string | For `insert` | Property path (e.g., `location`, `rotation_euler`) |
| `frame` | int | For `insert`/`delete` | Frame number |
| `value` | any | For `insert` | Property value |

### `manage_timeline`
| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `action` | enum | **Yes** | `set_range`, `set_fps`, `set_frame`, `play`, `stop` |
| `frame` | int | For `set_frame` | Target frame |
| `frame_start` | int | For `set_range` | Start frame |
| `frame_end` | int | For `set_range` | End frame |
| `fps` | int | For `set_fps` | Frames per second |

### `manage_nla`
| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `action` | enum | **Yes** | `list_tracks`, `push_action`, `create_strip`, `mute_track`, `solo_track` |
| `object` | string | **Yes** | Target object |
| `action_name` | string | Varies | Action name |
| `track_name` | string | Varies | NLA track name |
| `frame_start` | int | No | Strip start frame |
| `blend_type` | enum | No | `REPLACE`, `COMBINE`, `ADD`, `SUBTRACT` |
| `influence` | float | No | Strip influence (0-1) |
| `repeat` | float | No | Strip repeat count |
| `scale` | float | No | Strip time scale |

### `manage_markers`
| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `action` | enum | **Yes** | `add`, `remove`, `list`, `move` |
| `name` | string | Varies | Marker name |
| `frame` | int | Varies | Frame number |
| `camera` | string | No | Camera to bind |

---

## 7. File & I/O

### `manage_file`
| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `action` | enum | **Yes** | `new`, `open`, `save`, `save_as`, `info` |
| `filepath` | string | For `open`/`save_as` | File path |
| `use_empty` | bool | For `new` | Start with empty scene |

### `export_model`
| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `format` | enum | **Yes** | `FBX`, `OBJ`, `GLTF`, `GLB`, `STL`, `USD`, `ABC` |
| `filepath` | string | **Yes** | Output file path |
| `selected_only` | bool | No | Export only selected objects |
| `apply_modifiers` | bool | No | Apply modifiers before export |

### `import_model`
| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `filepath` | string | **Yes** | File to import (auto-detects format) |

### `library_link`
| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `action` | enum | **Yes** | `link`, `append`, `list_contents` |
| `filepath` | string | Varies | .blend file path |
| `data_type` | enum | Varies | `Object`, `Material`, `Collection`, `NodeTree`, `Action`, `World` |
| `names` | array | For `link`/`append` | Names to link/append |

---

## 8. World & Environment

### `manage_world`
| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `action` | enum | **Yes** | `get`, `set_color`, `set_hdri`, `set_sky`, `set_strength`, `set_volume` |
| `color` | [R,G,B] | For `set_color` | World background color |
| `hdri_path` | string | For `set_hdri` | Path to HDR image |
| `rotation` | float | For `set_hdri` | HDRI rotation (degrees) |
| `strength` | float | For `set_strength` | Environment intensity |
| `density` | float | For `set_volume` | Volumetric fog density |
| `sky_params` | object | For `set_sky` | `{ sky_type, sun_elevation, sun_rotation, air_density, dust_density, ozone_density, altitude }` |

---

## 9–16. Remaining Tools (Quick Reference)

### `manage_geometry_nodes`
Actions: `create`, `read`, `set_input`, `get_inputs`, `apply`, `delete`, `set_node_group`

### `manage_node_group`
Actions: `list`, `create`, `read`, `duplicate`, `delete`. Tree types: `GeometryNodeTree`, `ShaderNodeTree`, `CompositorNodeTree`

### `manage_armature`
Actions: `create`, `add_bone`, `remove_bone`, `list_bones`, `rename_bone`, `set_bone_parent`, `set_pose`, `reset_pose`, `set_ik`, `parent_mesh`

### `manage_weight_paint`
Actions: `auto_weights`, `assign_vertex_group`, `normalize`, `clean`, `get_weights`, `list_groups`, `remove_group`

### `manage_uv`
Actions: `unwrap`, `smart_project`, `cube_project`, `cylinder_project`, `sphere_project`, `pack`, `create_layer`, `remove_layer`, `list_layers`

### `manage_images`
Actions: `load`, `create`, `save`, `pack`, `unpack`, `list`, `assign_to_node`, `delete`

### `manage_texture_bake`
Actions: `setup`, `bake`. Types: `DIFFUSE`, `NORMAL`, `AO`, `ROUGHNESS`, `EMIT`, `COMBINED`, `SHADOW`

### `manage_curve`
Actions: `create`, `add_point`, `set_properties`, `convert_to_mesh`. Types: `BEZIER`, `NURBS`, `POLY`

### `manage_text`
Actions: `create`, `modify`, `convert_to_mesh`

### `manage_grease_pencil`
Actions: `create`, `add_layer`, `add_stroke`, `set_material`, `list_layers`

### `manage_shape_keys`
Actions: `list`, `create`, `delete`, `set_value`, `set_key`

### `manage_drivers`
Actions: `add`, `remove`, `list`. Types: `SCRIPTED`, `AVERAGE`, `SUM`, `MIN`, `MAX`

### `manage_custom_properties`
Actions: `set`, `get`, `remove`, `list`

### `manage_compositor`
Actions: `enable`, `disable`, `add_node`, `remove_node`, `connect`, `disconnect`, `set_value`, `list_nodes`

### `manage_view_layer`
Actions: `list`, `create`, `delete`, `set_active`, `get_passes`, `enable_pass`

### `manage_preferences`
Actions: `get`, `set`

### `manage_addons`
Actions: `list`, `enable`, `disable`

### `manage_scene_settings`
Actions: `get`, `set`

### `manage_physics`
Actions: `add`, `remove`, `bake`. Types: `RIGID_BODY`, `SOFT_BODY`, `CLOTH`, `PARTICLE_SYSTEM`

---

## 17. Documentation Tools

### `search_blender_manual`
Semantic search across the indexed Blender documentation.

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `query` | string | **Yes** | Natural language search query |

### `read_specific_page`
Read a specific HTML page from the docs cache as Markdown.

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `relative_path` | string | **Yes** | Path relative to docs dir (e.g., `render/cycles/baking.html`) |

### `update_index`
Re-scan the DOCS folder and update the SQLite vector store. No parameters.

---

## 18. Legacy Tools

### `execute_blender_code`
Inject sandboxed Python into Blender. **Prefer structured tools when possible.**

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `code` | string | **Yes** | Python script (bpy/math/bmesh/mathutils only) |

**Sandbox:** Only `bpy`, `math`, `bmesh`, `mathutils` allowed. 120-second timeout.

### `take_blender_screenshot`
Capture the current 3D viewport as a base64 PNG. No parameters.
