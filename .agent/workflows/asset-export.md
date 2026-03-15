---
description: Standardized steps for exporting to GLB/FBX with textures
---
1. Run the validation utility to ensure the scene is clean: `execute_blender_code` with `src/utils/validate_scene.py` logic.
2. Select all relevant objects for export.
3. Apply all transforms to avoid scaling issues in other software: `batch_operations` with `action="apply_all_transforms"`.
4. Ensure all objects have UV layers: `manage_uv` with `action="smart_project"` if missing.
5. Export the model using `export_model`.
   - For GLB/GLTF: `format="GLB", filepath="outputs/export.glb", apply_modifiers=true`.
   - For FBX: `format="FBX", filepath="outputs/export.fbx", apply_modifiers=true`.
6. Log the export in project history.
