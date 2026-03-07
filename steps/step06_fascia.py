# Step 6: Front Fascia
M_BLUE = bpy.data.materials['Blue']
M_BLACK = bpy.data.materials['Black']
M_GRILLE = bpy.data.materials['Grille']
M_PLASTIC = bpy.data.materials['Plastic']
M_WHITE_E = bpy.data.materials['WhiteEmit']
M_YELLOW_E = bpy.data.materials['YellowEmit']
M_RED_E = bpy.data.materials['RedEmit']

sp = P('Splitter', 'CUBE', (0, -2.4, 0.12), (0.85, 0.15, 0.03), (0.05, 0, 0), M_BLUE)
BV(sp)
P('SplitterFin', 'CUBE', (0, -2.3, 0.25), (0.6, 0.1, 0.15), (0, 0, 0), M_BLACK)
bmp = P('Bumper', 'CUBE', (0, -2.2, 0.35), (0.75, 0.1, 0.08), (0, 0, 0), M_BLUE)
BV(bmp)
grille = P('Grille', 'PLANE', (0, -2.2, 0.6), (0.72, 0.05, 0.08), (math.radians(90), 0, 0), M_GRILLE)
bpy.context.view_layer.objects.active = grille
bpy.ops.object.modifier_add(type='WIREFRAME')
grille.modifiers['Wireframe'].thickness = 0.012
P('GrilleBG', 'CUBE', (0, -2.15, 0.6), (0.75, 0.01, 0.1), (0, 0, 0), M_BLACK)

def ml(name, loc, sz, mat):
    h = P(f'{name}_H', 'CYL', (loc[0], loc[1]+0.02, loc[2]), (sz+0.01, sz+0.01, 0.03), (math.radians(90),0,0), M_PLASTIC)
    MR(h)
    l = P(f'{name}_L', 'SPH', loc, (sz, sz, 0.02), (0,0,0), mat)
    MR(l)

ml('HLO', (0.5, -2.25, 0.6), 0.04, M_WHITE_E)
ml('HLI', (0.3, -2.25, 0.6), 0.04, M_WHITE_E)
ml('FL', (0.55, -2.35, 0.2), 0.03, M_YELLOW_E)
rl = P('TailLight', 'CUBE', (0.55, 2.3, 0.6), (0.15, 0.02, 0.05), (0,0,0), M_RED_E)
MR(rl)

print('Step 6 DONE')
print(f'Objects: {len(bpy.data.objects)}')
