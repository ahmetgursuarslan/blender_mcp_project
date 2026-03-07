# Step 4: Fenders, Side Vents, Exhaust
M_BLUE = bpy.data.materials['Blue']
M_BLACK = bpy.data.materials['Black']

fl = P('FenderFL', 'CUBE', (0.85, -1.35, 0.55), (0.1, 0.3, 0.15), (0,0,0), M_BLUE)
MR(fl); SD(fl, 2); BV(fl)
rl = P('FenderRL', 'CUBE', (0.85, 1.35, 0.55), (0.1, 0.3, 0.15), (0,0,0), M_BLUE)
MR(rl); SD(rl, 2); BV(rl)
sv = P('SideVentL', 'CUBE', (0.82, -0.5, 0.55), (0.005, 0.15, 0.04), (0,0,0), M_BLACK)
MR(sv)
sv2 = P('SideVent2L', 'CUBE', (0.82, -0.5, 0.48), (0.005, 0.15, 0.04), (0,0,0), M_BLACK)
MR(sv2)
ex = P('ExhaustL', 'CYL', (0.85, -0.1, 0.35), (0.04, 0.04, 0.15), (0, math.radians(90), 0), M_BLACK)
MR(ex)
print('Step 4 DONE')
print(f'Objects: {len(bpy.data.objects)}')
