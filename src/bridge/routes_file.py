import bpy

def handle_manage_file(params: dict) -> dict:
    """POST /api/file/manage"""
    action = params.get("action")
    filepath = params.get("filepath", "")

    if action == "new":
        bpy.ops.wm.read_homefile(use_empty=params.get("use_empty", False))
        return {"status": "success", "message": "New scene created."}
    
    elif action == "open":
        if not filepath: return {"status": "error", "message": "No filepath provided."}
        bpy.ops.wm.open_mainfile(filepath=filepath)
        return {"status": "success", "message": f"Opened '{filepath}'."}
    
    elif action == "save":
        if bpy.data.filepath:
            bpy.ops.wm.save_mainfile()
            return {"status": "success", "message": "File saved."}
        elif filepath:
            bpy.ops.wm.save_as_mainfile(filepath=filepath)
            return {"status": "success", "message": f"Saved as '{filepath}'."}
        return {"status": "error", "message": "File not saved yet. Provid a filepath."}

    elif action == "info":
        return {
            "status": "success",
            "data": {
                "filepath": bpy.data.filepath,
                "is_dirty": bpy.data.is_dirty,
                "version": bpy.app.version_string,
            }
        }

    return {"status": "error", "message": f"Unknown action: {action}"}

def handle_export_model(params: dict) -> dict:
    """POST /api/file/export"""
    fmt = params.get("format", "OBJ")
    path = params.get("filepath")
    if not path: return {"status": "error", "message": "No filepath provided."}

    if fmt == "FBX": bpy.ops.export_scene.fbx(filepath=path, use_selection=params.get("selected_only", False))
    elif fmt == "OBJ": bpy.ops.wm.obj_export(filepath=path, export_selected=params.get("selected_only", False))
    elif fmt == "GLTF": bpy.ops.export_scene.gltf(filepath=path, export_format='GLB' if fmt=='GLB' else 'GLTF_SEPARATE', use_selection=params.get("selected_only", False))
    elif fmt == "STL": bpy.ops.export_mesh.stl(filepath=path, use_selection=params.get("selected_only", False))
    
    return {"status": "success", "message": f"Exported as {fmt} to '{path}'."}

def handle_import_model(params: dict) -> dict:
    """POST /api/file/import"""
    path = params.get("filepath")
    if not path: return {"status": "error", "message": "No filepath provided."}
    
    ext = path.split('.')[-1].upper()
    if ext == "FBX": bpy.ops.import_scene.fbx(filepath=path)
    elif ext == "OBJ": bpy.ops.wm.obj_import(filepath=path)
    elif ext == "GLB" or ext == "GLTF": bpy.ops.import_scene.gltf(filepath=path)
    elif ext == "STL": bpy.ops.import_mesh.stl(filepath=path)
    else: return {"status": "error", "message": f"Unsupported format: {ext}"}

    return {"status": "success", "message": f"Imported '{path}'."}
