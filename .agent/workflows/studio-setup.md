---
description: Automated creation of professional lighting and camera rigs
---
// turbo-all
1. Verify the bridge is alive with `get_blender_state`.
2. Reset the scene if needed using `manage_file` with `action="new", use_empty=true`.
3. Create a Key light using `manage_light` at `(5, -5, 5)` with `energy=1000, color=[1, 1, 1]`.
4. Create a Fill light using `manage_light` at `(-5, -5, 3)` with `energy=500, color=[0.8, 0.9, 1]`.
5. Create a Rim light using `manage_light` at `(0, 5, 5)` with `energy=800, color=[1, 0.9, 0.8]`.
6. Set up a Hero camera at `(8, -8, 5)` using `manage_camera` with `lens=85`.
7. Point the camera at the origin using `manage_camera` with `action="look_at", target=[0, 0, 1]`.
8. Set the active camera using `manage_camera` with `action="set_active"`.
9. Set the world background to a dark studio look using `manage_world` with `action="set_color", color=[0.05, 0.05, 0.05]`.
10. Take a screenshot to verify the setup: `take_blender_screenshot`.
