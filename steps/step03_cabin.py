# Step 3: Cabin + Glass
# Re-fetch materials by name (undo invalidates Python refs)
M_BLUE = bpy.data.materials['Blue']
M_GLASS = bpy.data.materials['Glass']

cabin = P('Cabin', 'CUBE', (0, 0.3, 0.88), (0.65, 0.8, 0.12), (0,0,0), M_BLUE)
SD(cabin, 2)
BV(cabin)

P('Windshield', 'CUBE', (0, -0.55, 0.88), (0.58, 0.02, 0.18), (math.radians(55), 0, 0), M_GLASS)
P('RearGlass', 'CUBE', (0, 1.15, 0.88), (0.58, 0.02, 0.18), (math.radians(-50), 0, 0), M_GLASS)
sg = P('SideGlassL', 'CUBE', (0.66, 0.3, 0.88), (0.01, 0.5, 0.1), (0,0,0), M_GLASS)
MR(sg)
P('Roof', 'CUBE', (0, 0.3, 1.02), (0.6, 0.6, 0.02), (0,0,0), M_BLUE)

print('Step 3 DONE: Cabin + glass panels.')
print(f'Objects: {len(bpy.data.objects)}')
