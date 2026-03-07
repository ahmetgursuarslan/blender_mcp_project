# Step 8: Missiles & Machine Guns
M_BLACK = bpy.data.materials['Black']
M_RED_E = bpy.data.materials['RedEmit']
M_PLASTIC = bpy.data.materials['Plastic']

P('MissileMount', 'CUBE', (0.35, -0.1, 1.25), (0.05, 0.05, 0.05), (0,0,0), M_BLACK)
P('MissTop', 'CYL', (0.4, -0.15, 1.35), (0.07, 0.07, 0.2), (math.radians(90), 0, 0), M_BLACK)
P('MissBot', 'CYL', (0.4, -0.15, 1.18), (0.07, 0.07, 0.2), (math.radians(90), 0, 0), M_BLACK)
P('MGTop', 'SPH', (0.4, -0.35, 1.35), (0.055, 0.055, 0.03), (0,0,0), M_RED_E)
P('MGBot', 'SPH', (0.4, -0.35, 1.18), (0.055, 0.055, 0.03), (0,0,0), M_RED_E)

def mk_gun(loc):
    gm = P('GunM', 'CUBE', (loc[0], loc[1]+0.1, loc[2]), (0.03, 0.04, 0.03), (0,0,0), M_PLASTIC)
    MR(gm)
    gb = P('GunB', 'CYL', (loc[0], loc[1], loc[2]), (0.008, 0.008, 0.15), (math.radians(90),0,0), M_BLACK)
    MR(gb)

mk_gun((0.25, -1.3, 0.68))
mk_gun((0.7, -2.4, 0.25))
print('Step 8 DONE')
print(f'Objects: {len(bpy.data.objects)}')
