import bpy


def handle_manage_file(params: dict) -> dict:
    """File: new/open/save/save_as/info."""
    action = params.get("action")
    filepath = params.get("filepath", "")

    if action == "new":
        bpy.ops.wm.read_homefile(use_empty=params.get("use_empty", False))
        return {"status": "success", "message": "New scene created."}

    elif action == "open":
        if not filepath:
            return {"status": "error", "message": "No filepath provided."}
        try:
            bpy.ops.wm.open_mainfile(filepath=filepath)
            return {"status": "success", "message": f"Opened '{filepath}'."}
        except Exception as e:
            return {"status": "error", "message": f"Open failed: {e}"}

    elif action == "save":
        if bpy.data.filepath:
            bpy.ops.wm.save_mainfile()
            return {"status": "success", "message": f"File saved to '{bpy.data.filepath}'."}
        elif filepath:
            bpy.ops.wm.save_as_mainfile(filepath=filepath)
            return {"status": "success", "message": f"Saved as '{filepath}'."}
        return {"status": "error", "message": "File not saved yet. Provide a filepath."}

    elif action == "save_as":
        if not filepath:
            return {"status": "error", "message": "No filepath provided for save_as."}
        bpy.ops.wm.save_as_mainfile(filepath=filepath)
        return {"status": "success", "message": f"Saved as '{filepath}'."}

    elif action == "info":
        return {
            "status": "success",
            "data": {
                "filepath": bpy.data.filepath,
                "is_dirty": bpy.data.is_dirty,
                "version": bpy.app.version_string,
                "scene_name": bpy.context.scene.name,
            }
        }

    return {"status": "error", "message": f"Unknown file action: {action}"}


def handle_export_model(params: dict) -> dict:
    """Export: FBX/OBJ/GLTF/GLB/STL/USD/ABC."""
    fmt = params.get("format", "OBJ")
    path = params.get("filepath")
    if not path:
        return {"status": "error", "message": "No filepath provided."}

    selected = params.get("selected_only", False)
    apply_mods = params.get("apply_modifiers", True)

    try:
        if fmt == "FBX":
            bpy.ops.export_scene.fbx(filepath=path, use_selection=selected, use_mesh_modifiers=apply_mods)
        elif fmt == "OBJ":
            bpy.ops.wm.obj_export(filepath=path, export_selected_objects=selected, apply_modifiers=apply_mods)
        elif fmt in ("GLTF", "GLB"):
            export_fmt = 'GLB' if fmt == 'GLB' else 'GLTF_SEPARATE'
            bpy.ops.export_scene.gltf(filepath=path, export_format=export_fmt, use_selection=selected)
        elif fmt == "STL":
            bpy.ops.export_mesh.stl(filepath=path, use_selection=selected)
        elif fmt == "USD":
            bpy.ops.wm.usd_export(filepath=path, selected_objects_only=selected)
        elif fmt == "ABC":
            bpy.ops.wm.alembic_export(filepath=path, selected=selected)
        else:
            return {"status": "error", "message": f"Unsupported format: {fmt}"}
        return {"status": "success", "message": f"Exported as {fmt} to '{path}'."}
    except Exception as e:
        return {"status": "error", "message": f"Export failed: {e}"}


def handle_import_model(params: dict) -> dict:
    """Import 3D file (auto-detects format)."""
    path = params.get("filepath")
    if not path:
        return {"status": "error", "message": "No filepath provided."}

    ext = path.split('.')[-1].upper()
    try:
        if ext == "FBX":
            bpy.ops.import_scene.fbx(filepath=path)
        elif ext == "OBJ":
            bpy.ops.wm.obj_import(filepath=path)
        elif ext in ("GLB", "GLTF"):
            bpy.ops.import_scene.gltf(filepath=path)
        elif ext == "STL":
            bpy.ops.import_mesh.stl(filepath=path)
        elif ext in ("USD", "USDA", "USDC", "USDZ"):
            bpy.ops.wm.usd_import(filepath=path)
        elif ext == "ABC":
            bpy.ops.wm.alembic_import(filepath=path)
        elif ext == "SVG":
            bpy.ops.import_curve.svg(filepath=path)
        else:
            return {"status": "error", "message": f"Unsupported format: {ext}"}
        return {"status": "success", "message": f"Imported '{path}'."}
    except Exception as e:
        return {"status": "error", "message": f"Import failed: {e}"}
