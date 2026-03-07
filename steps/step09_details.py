# Step 9: Spoiler, Mirrors, Antenna
M_BLUE = bpy.data.materials['Blue']
M_YELLOW = bpy.data.materials['Yellow']
M_BLACK = bpy.data.materials['Black']
M_GLASS = bpy.data.materials['Glass']
M_PLASTIC = bpy.data.materials['Plastic']

sw = P('SpoilerWing', 'CUBE', (0, 2.3, 0.9), (0.8, 0.1, 0.02), (math.radians(10), 0, 0), M_BLUE)
SD(sw, 2); BV(sw)
P('SpoilerStripe', 'CUBE', (0, 2.3, 0.91), (0.15, 0.1, 0.025), (math.radians(10), 0, 0), M_YELLOW)
sf = P('SpoilerFin', 'CUBE', (0.75, 2.3, 0.85), (0.02, 0.1, 0.1), (math.radians(10), 0, 0), M_BLUE)
MR(sf)
strt = P('SpoilerStrut', 'CYL', (0.5, 2.15, 0.72), (0.015, 0.015, 0.1), (math.radians(15), 0, 0), M_BLACK)
MR(strt)

mm = P('MirrorMount', 'CYL', (0.65, -0.7, 0.74), (0.01, 0.01, 0.04), (0, math.radians(90), 0), M_PLASTIC)
MR(mm)
mc = P('MirrorCase', 'SPH', (0.75, -0.7, 0.74), (0.05, 0.04, 0.03), (0,0,0), M_BLUE)
MR(mc)
mg = P('MirrorGlass', 'SPH', (0.75, -0.72, 0.74), (0.04, 0.03, 0.02), (0,0,0), M_GLASS)
MR(mg)
P('Antenna', 'CYL', (0.3, 1.6, 1.1), (0.003, 0.003, 0.2), (0,0,0), M_BLACK)

print('Step 9 DONE')
print(f'Objects: {len(bpy.data.objects)}')
