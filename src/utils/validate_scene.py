import bpy

def validate_scene():
    """
    Performs technical validation on the Blender scene.
    Checks for common production issues.
    """
    issues = []
    
    # 1. Check for objects without UV maps
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            if not obj.data.uv_layers:
                issues.append(f"MISSING_UV: Object '{obj.name}' has no UV layers.")
            
            # 2. Check for zero-face/vertex meshes
            if len(obj.data.vertices) == 0:
                issues.append(f"EMPTY_MESH: Object '{obj.name}' has no vertices.")
                
            # 3. Check for naming conventions (Optional, but good practice)
            # Prefix check could be added here if project uses specific prefixes
            
    # 4. Check for materials with missing nodes
    for mat in bpy.data.materials:
        if mat.use_nodes and not mat.node_tree:
            issues.append(f"INVALID_MATERIAL: Material '{mat.name}' has nodes enabled but no node tree.")

    print("--- VALIDATION REPORT START ---")
    if not issues:
        print("ALL_CLEAR: Scene passed all technical checks.")
    else:
        for issue in issues:
            print(issue)
    print("--- VALIDATION REPORT END ---")
    
    return issues

if __name__ == "__main__":
    validate_scene()
