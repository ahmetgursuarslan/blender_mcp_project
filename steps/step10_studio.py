# Step 10: Studio Setup — Lighting, Camera, Background
# Background plane
bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, 0))
bg = bpy.context.active_object
bg.name = 'StudioFloor'
mat_bg = bpy.data.materials.new('StudioBG')
mat_bg.use_nodes = True
bsdf = mat_bg.node_tree.nodes['Principled BSDF']
bsdf.inputs['Base Color'].default_value = (0.05, 0.05, 0.05, 1.0)
bsdf.inputs['Roughness'].default_value = 0.15
bg.data.materials.append(mat_bg)
for p in bg.data.polygons:
    p.use_smooth = True

# Key light
bpy.ops.object.light_add(type='AREA', location=(10, -10, 10))
key = bpy.context.active_object
key.name = 'KeyLight'
key.data.energy = 50000
key.data.size = 20
key.rotation_euler = (math.radians(45), 0, math.radians(45))

# Fill light
bpy.ops.object.light_add(type='AREA', location=(-12, -5, 6))
fill = bpy.context.active_object
fill.name = 'FillLight'
fill.data.energy = 15000
fill.data.size = 15
fill.rotation_euler = (math.radians(60), 0, math.radians(-45))

# Rim light
bpy.ops.object.light_add(type='AREA', location=(0, 15, 8))
rim = bpy.context.active_object
rim.name = 'RimLight'
rim.data.energy = 40000
rim.data.size = 15
rim.rotation_euler = (math.radians(45), math.radians(180), 0)

# Camera
bpy.ops.object.camera_add(location=(14, -18, 9))
cam = bpy.context.active_object
cam.name = 'HeroCamera'
cam.rotation_euler = (math.radians(63), 0, math.radians(38))
cam.data.lens = 120
bpy.context.scene.camera = cam

# Render settings
bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.cycles.samples = 128
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080

print('Step 10 DONE: Studio lighting + camera + render settings.')
print(f'Total objects: {len(bpy.data.objects)}')
total_v = sum(len(o.data.vertices) for o in bpy.data.objects if o.type == 'MESH')
print(f'Total raw vertices: {total_v}')
