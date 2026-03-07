# Step 1: Reset Scene & Create All Materials + Helpers
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)
for mat in list(bpy.data.materials):
    bpy.data.materials.remove(mat)

def make_mat(name, col, met, rgh, emit=None, strength=10):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = col
    bsdf.inputs['Metallic'].default_value = met
    bsdf.inputs['Roughness'].default_value = rgh
    if emit:
        if 'Emission Color' in bsdf.inputs:
            bsdf.inputs['Emission Color'].default_value = emit
            bsdf.inputs['Emission Strength'].default_value = strength
    return mat

M_BLUE = make_mat('Blue', (0.015, 0.08, 0.45, 1), 0.3, 0.25)
M_YELLOW = make_mat('Yellow', (0.9, 0.65, 0.02, 1), 0.1, 0.3)
M_BLACK = make_mat('Black', (0.02, 0.02, 0.02, 1), 0.8, 0.4)
M_GLASS = make_mat('Glass', (0.002, 0.002, 0.002, 1), 0.5, 0.05)
M_RUBBER = make_mat('Rubber', (0.01, 0.01, 0.01, 1), 0.0, 0.9)
M_PLASTIC = make_mat('Plastic', (0.01, 0.01, 0.01, 1), 0.0, 0.7)
M_WHITE_E = make_mat('WhiteEmit', (0,0,0,1), 0, 0, (1, 0.95, 0.9, 1), 25)
M_YELLOW_E = make_mat('YellowEmit', (0,0,0,1), 0, 0, (1, 0.8, 0.1, 1), 25)
M_RED_E = make_mat('RedEmit', (0,0,0,1), 0, 0, (1, 0, 0, 1), 40)
M_GRILLE = make_mat('Grille', (0.05, 0.05, 0.05, 1), 0.9, 0.5)

def P(name, ptype, loc, scale, rot, mat):
    if ptype == 'CUBE':
        bpy.ops.mesh.primitive_cube_add(location=loc)
    elif ptype == 'CYL':
        bpy.ops.mesh.primitive_cylinder_add(vertices=64, location=loc)
    elif ptype == 'SPH':
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=loc)
    elif ptype == 'PLANE':
        bpy.ops.mesh.primitive_plane_add(size=2, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    o.rotation_euler = rot
    o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = True
    return o

def BV(obj, w=0.008):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_add(type='BEVEL')
    mod = obj.modifiers['Bevel']
    mod.width = w
    mod.segments = 4
    mod.limit_method = 'ANGLE'
    mod.angle_limit = math.radians(30)

def MR(obj):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_add(type='MIRROR')
    obj.modifiers['Mirror'].use_axis[0] = True

def SD(obj, lvl=2):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_add(type='SUBSURF')
    mod = obj.modifiers['Subdivision']
    mod.levels = lvl
    mod.render_levels = lvl

print('Step 1 DONE: Scene cleared, 10 materials + P/BV/MR/SD helpers created.')
print(f'Materials: {len(bpy.data.materials)}')
