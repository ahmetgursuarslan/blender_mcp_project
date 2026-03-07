# Step 2: Car Body, Hood, Trunk, Stripes, Chassis
body = P('Body', 'CUBE', (0, 0.3, 0.5), (0.75, 1.2, 0.25), (0,0,0), M_BLUE)
SD(body, 2)
BV(body)

hood = P('Hood', 'CUBE', (0, -1.6, 0.45), (0.75, 0.7, 0.2), (-0.05, 0, 0), M_BLUE)
SD(hood, 2)
BV(hood)

trunk = P('Trunk', 'CUBE', (0, 1.9, 0.55), (0.75, 0.4, 0.2), (0.05, 0, 0), M_BLUE)
SD(trunk, 2)
BV(trunk)

P('Chassis', 'CUBE', (0, 0.3, 0.2), (0.8, 1.4, 0.05), (0,0,0), M_BLACK)

# Stripes
P('StripeTop', 'CUBE', (0, 0.3, 0.52), (0.15, 1.2, 0.255), (0,0,0), M_YELLOW)
P('StripeHood', 'CUBE', (0, -1.6, 0.47), (0.15, 0.7, 0.205), (-0.05, 0, 0), M_YELLOW)
P('StripeTrunk', 'CUBE', (0, 1.9, 0.57), (0.15, 0.4, 0.205), (0.05, 0, 0), M_YELLOW)

# Side stripes
ss = P('SideStripeL', 'CUBE', (0.76, 0.2, 0.5), (0.005, 0.8, 0.02), (0,0,0), M_YELLOW)
MR(ss)

# Lower skirt
sk = P('SkirtL', 'CUBE', (0.78, 0.3, 0.25), (0.04, 1.0, 0.05), (0,0,0), M_BLACK)
MR(sk)

print('Step 2 DONE: Body, hood, trunk, stripes, chassis built.')
print(f'Objects: {len(bpy.data.objects)}')
