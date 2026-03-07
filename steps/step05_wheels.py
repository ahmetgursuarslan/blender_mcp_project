# Step 5: Wheels
M_RUBBER = bpy.data.materials['Rubber']
M_BLACK = bpy.data.materials['Black']
M_YELLOW = bpy.data.materials['Yellow']

def make_wheel(ypos):
    tire = P('Tire', 'CYL', (0.9, ypos, 0.35), (0.32, 0.32, 0.12), (0, math.radians(90), 0), M_RUBBER)
    MR(tire)
    rim = P('Rim', 'CYL', (1.0, ypos, 0.35), (0.22, 0.22, 0.06), (0, math.radians(90), 0), M_BLACK)
    MR(rim)
    hub = P('Hub', 'CYL', (1.02, ypos, 0.35), (0.08, 0.08, 0.03), (0, math.radians(90), 0), M_YELLOW)
    MR(hub)
    for i in range(5):
        ang = math.radians(i * 72)
        ly = ypos + math.sin(ang) * 0.05
        lz = 0.35 + math.cos(ang) * 0.05
        ln = P(f'Lug_{ypos}_{i}', 'CYL', (1.04, ly, lz), (0.012, 0.012, 0.008), (0, math.radians(90), 0), M_BLACK)
        MR(ln)

make_wheel(-1.35)
make_wheel(1.35)
print('Step 5 DONE')
print(f'Objects: {len(bpy.data.objects)}')
