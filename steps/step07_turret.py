# Step 7: Turret
M_YELLOW = bpy.data.materials['Yellow']
M_BLACK = bpy.data.materials['Black']

tb = P('TurretBase', 'CYL', (0, 0.0, 1.1), (0.35, 0.35, 0.05), (0,0,0), M_YELLOW)
SD(tb, 1)
thead = P('TurretHead', 'CUBE', (0, -0.1, 1.3), (0.25, 0.3, 0.15), (0,0,0), M_YELLOW)
SD(thead, 2); BV(thead)
P('CannonBase', 'CYL', (0, -0.4, 1.3), (0.1, 0.1, 0.15), (math.radians(90), 0, 0), M_YELLOW)
P('CannonBarrel', 'CYL', (0, -0.9, 1.3), (0.06, 0.06, 0.5), (math.radians(90), 0, 0), M_YELLOW)
for i in range(4):
    y = -0.55 - i * 0.15
    P(f'Ring_{i}', 'CYL', (0, y, 1.3), (0.065, 0.065, 0.015), (math.radians(90), 0, 0), M_BLACK)
P('Muzzle', 'CYL', (0, -1.4, 1.3), (0.08, 0.08, 0.08), (math.radians(90), 0, 0), M_YELLOW)
P('MuzzleHole', 'CYL', (0, -1.45, 1.3), (0.05, 0.05, 0.06), (math.radians(90), 0, 0), M_BLACK)
tf = P('TurretFin', 'CUBE', (0, 0.3, 1.35), (0.02, 0.12, 0.15), (math.radians(-20), 0, 0), M_YELLOW)
SD(tf, 1)

print('Step 7 DONE')
print(f'Objects: {len(bpy.data.objects)}')
