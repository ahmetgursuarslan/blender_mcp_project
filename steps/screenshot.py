# Take a viewport screenshot (capture from camera viewpoint)
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080
bpy.context.scene.render.filepath = bpy.path.abspath('//outputs/mcp_live_preview.png')
bpy.ops.render.opengl(write_still=True)
print('Screenshot saved to outputs/mcp_live_preview.png')
