import bpy
import os
from datetime import datetime

def summarize_scene():
    """
    Generates a markdown summary of the current Blender scene.
    Intended to be executed via 'execute_blender_code'.
    """
    stats = bpy.context.scene.statistics(bpy.context.view_layer)
    objects = bpy.data.objects
    collections = bpy.data.collections
    
    summary = []
    summary.append(f"# Scene Summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    summary.append(f"\n## Statistics\n- {stats}")
    
    summary.append("\n## Collections & Hierarchy")
    for col in collections:
        summary.append(f"- **{col.name}**")
        for obj in col.objects:
            summary.append(f"  - {obj.name} ({obj.type})")
            
    summary.append("\n## Materials")
    materials = bpy.data.materials
    if materials:
        for mat in materials:
            summary.append(f"- {mat.name}")
    else:
        summary.append("- No materials in scene")

    summary_text = "\n".join(summary)
    
    # In a real MCP context, we might write this to a file or print it
    print("--- SCENE SUMMARY START ---")
    print(summary_text)
    print("--- SCENE SUMMARY END ---")
    
    return summary_text

if __name__ == "__main__":
    summarize_scene()
