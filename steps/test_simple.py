# Minimal test
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
obj = bpy.context.active_object
obj.name = 'TestCube'
print(f'Created {obj.name} at {obj.location}')
print(f'Scene objects: {len(bpy.data.objects)}')
