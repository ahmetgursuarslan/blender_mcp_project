---
description: Standardized steps for final high-quality renders
---
1. Set render engine to Cycles: `set_render_settings` with `engine="CYCLES"`.
2. Configure high-quality samples: `set_render_settings` with `cycles={"samples": 1024, "use_denoising": True}`.
3. Set resolution to 1920x1080 or higher: `set_render_settings` with `resolution_x=1920, resolution_y=1080`.
4. Enable film transparency if needed: `set_render_settings` with `film_transparent=True`.
5. Run the render: `render_image` with `filepath="outputs/renders/final_render.png"`.
6. Post-process if needed using `manage_compositor`.
