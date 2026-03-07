# Workflows

> Standard workflows for 3D modeling, image replication, and asset export using the Elite Blender MCP.

---

## 1. Standard 3D Model Workflow

The universal 10-phase pipeline for creating any 3D model:

```
Phase 0: VERIFY        → get_blender_state
Phase 1: RESET         → manage_file (action: new, use_empty: true)
Phase 2: MATERIALS     → manage_material (create all PBR materials)
Phase 3: BASE SHAPE    → manage_object + execute_blender_code (BMesh)
Phase 4: DETAILS       → manage_object + edit_mesh
Phase 5: MODIFIERS     → manage_modifier (Bevel, SubD, Mirror)
Phase 6: LIGHTING      → manage_light (3-point studio rig)
Phase 7: CAMERA        → manage_camera (hero angle, focal length)
Phase 8: ENVIRONMENT   → manage_world (HDRI or dark studio)
Phase 9: RENDER        → set_render_settings + render_image
Phase 10: VERIFY       → take_blender_screenshot
```

### Tool Priority Rules
1. **Structured tools first** — Use `manage_object`, `manage_material`, etc.
2. **BMesh for topology** — Fall back to `execute_blender_code` for vertex-level work
3. **One logical action per call** — Don't build everything in one code block
4. **Verify after each phase** — `get_blender_state` or `take_blender_screenshot`

---

## 2. Image-to-Blender Replication Pipeline

When the user provides a reference image, follow this 7-step process:

### Step 1: Image Analysis
Analyze the image and fill these tables:

**Dimensional Analysis:**
| Dimension | Blender Units | Ratio |
|-----------|:---:|:---:|
| Total Length | _estimate_ | 1.00 |
| Width | | ~0.40 |
| Height | | ~0.28 |
| Wheelbase | | ~0.58 |
| Wheel Diameter | | ~0.14 |

**Color Extraction:**
| Zone | RGB (0-1) | Metallic | Roughness |
|------|:---:|:---:|:---:|
| Body | | | |
| Chrome | | | |
| Glass | | | |

**Lighting:**
| Light | Direction | Intensity |
|-------|-----------|:---------:|
| Key | | |
| Fill | | |
| Rim | | |

### Step 2: Material Library
Create all materials using `manage_material` with extracted RGB values.

### Step 3: Geometric Decomposition
Break the subject into primitives:
- **Cubes** → Bodies, panels, bumpers
- **Cylinders** → Wheels, pipes
- **Spheres** → Lights, mirrors
- **Planes** → Grilles, windows

### Step 4: Progressive Construction
Build from largest to smallest:
1. Main body shell
2. Secondary volumes (cabin, hood)
3. Attachments (wheels, lights)
4. Fine details (grilles, badges)

### Step 5: Modifier Stack
Apply in this order:
1. Mirror → Solidify → Boolean → Bevel → Subdivision Surface

### Step 6: Scene Matching
Match the image's lighting, camera angle, and background.

### Step 7: Verification
`take_blender_screenshot` → Compare → Iterate → `render_image`

---

## 3. Game-Ready Export Workflow

```
1. Complete high-poly model (standard workflow)
2. manage_modifier: add DECIMATE → target ratio 0.1
3. manage_uv: smart_project → clean UV atlas
4. manage_texture_bake: setup + bake NORMAL from high-poly
5. manage_texture_bake: bake AO
6. export_model: format=GLB, apply_modifiers=true
```

---

## 4. Turntable Animation Workflow

```
1. manage_object: create_empty "TurntableCenter" at origin
2. manage_camera: create "TurntableCamera" at (10, 0, 3)
3. manage_camera: look_at target="TurntableCenter"
4. manage_object: set_parent camera → "TurntableCenter"
5. manage_keyframes: insert object="TurntableCenter"
   frame=1, property="rotation_euler", value=[0, 0, 0]
6. manage_keyframes: insert object="TurntableCenter"
   frame=120, property="rotation_euler", value=[0, 0, 6.283]
7. manage_timeline: set_range 1-120
8. manage_timeline: set_fps 30
9. set_render_settings: output_format=FFMPEG
10. render_image (animation)
```

---

## 5. Multi-Shot Render Workflow

```
1. manage_camera: create "Hero_34" loc=(8.5,-8.5,4.5) lens=85
2. manage_camera: create "Front"  loc=(0,-12,3) lens=100
3. manage_camera: create "Side"   loc=(15,0,3) lens=135
4. manage_camera: create "Low"    loc=(5,-5,1) lens=35

For each camera:
5. manage_camera: set_active name="{camera}"
6. render_image: filepath="outputs/{project}/renders/{shot}.png"
```

---

## 6. Collection Organization Workflow

```
1. manage_collection: create "Body"
2. manage_collection: create "Wheels"
3. manage_collection: create "Lights"
4. manage_collection: create "Interior"
5. manage_collection: create "Studio"

After creating objects:
6. manage_collection: add_object collection="Body" object="Chassis"
7. manage_collection: add_object collection="Wheels" object="Tire_FR"
```

---

## 7. Technical Validation Workflow

Run before final render/export:
```
1. get_scene_statistics → total verts < 5M
2. batch_operations: purge_orphans
3. edit_mesh: recalculate_normals (all objects)
4. get_mesh_data → verify no zero-face meshes
5. manage_uv: list_layers → verify UV exists
6. get_render_settings → resolution ≥ 1920×1080
7. manage_collection: list → verify organization
```
