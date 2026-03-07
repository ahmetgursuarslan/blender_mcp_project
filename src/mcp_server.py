"""
Elite Blender MCP Server v3.0
Exposes 54+ structured tools with prescriptive AI guidance for creating
production-quality 3D models, materials, lighting, and animations.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server

from services.database import DatabaseManager
from services.vector_store import VectorStore
from services.indexer_service import IndexerService
from services.blender_bridge_client import BlenderBridgeClient
from mcp_tools.docs_tools import get_docs_tools, DocsToolsHandler

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("mcp_server")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "blender_docs.db"
DOCS_DIR = PROJECT_ROOT / "blender_manual_html"
LOCK_FILE = Path.home() / ".blender_mcp_lock"

# ---------------------------------------------------------------------------
# Services (lazy init)
# ---------------------------------------------------------------------------
db_manager: DatabaseManager = None
vector_store: VectorStore = None
indexer: IndexerService = None
docs_handler: DocsToolsHandler = None
bridge: BlenderBridgeClient = None

server = Server("blender-expert-mcp")


def _init_services():
    global db_manager, vector_store, indexer, docs_handler, bridge
    if db_manager is None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        db_manager = DatabaseManager(str(DB_PATH))
        vector_store = VectorStore(db_manager)
        indexer = IndexerService(db_manager, vector_store, str(DOCS_DIR))
        docs_handler = DocsToolsHandler(db_manager, vector_store, indexer, str(DOCS_DIR))
        bridge = BlenderBridgeClient(LOCK_FILE)


# ═══════════════════════════════════════════════════════════════════════════
# TOOL DEFINITIONS — Elite AI Guidance
# ═══════════════════════════════════════════════════════════════════════════
# These descriptions are READ BY THE AI MODEL. They must be prescriptive,
# detailed, and guide the AI toward creating production-quality output.
# ═══════════════════════════════════════════════════════════════════════════

def _get_blender_tools() -> list[types.Tool]:
    """Returns all Blender bridge tool definitions with elite-level descriptions."""
    return [
        # ───────────────────────────────────────────────────
        # EXECUTE CODE (most powerful tool)
        # ───────────────────────────────────────────────────
        types.Tool(
            name="execute_blender_code",
            description=(
                "Execute arbitrary Python code directly inside Blender's main thread. "
                "This is the MOST POWERFUL tool — use it when no structured tool covers your need, "
                "or when you need complex multi-step operations in a single atomic call.\n\n"
                "## Available globals (pre-imported):\n"
                "bpy, bmesh, mathutils (Vector, Euler, Matrix, Quaternion), math, random, functools, itertools, collections\n\n"
                "## ELITE MODELING GUIDELINES — Follow these for production quality:\n"
                "1. **Use bmesh for complex geometry**: Create bmesh objects, manipulate vertices/edges/faces, "
                "then write to mesh. This gives you sub-object level control.\n"
                "2. **Subdivision workflow**: Start with low-poly base → add supporting edge loops → "
                "apply Subdivision Surface modifier for smooth results.\n"
                "3. **Boolean operations**: Use boolean modifiers for hard-surface modeling (union, difference, intersect).\n"
                "4. **Materials must use Principled BSDF**: Always create node-based materials. "
                "Set Base Color, Metallic (0=dielectric, 1=metal), Roughness (0=mirror, 0.5=satin, 1=matte), "
                "and Specular IOR Level for realism.\n"
                "5. **Bevel edges**: Real objects never have perfectly sharp edges. Add bevel modifiers "
                "or use bmesh bevel on important edges (width=0.002-0.01, segments=2-3).\n"
                "6. **Scale matters**: Use real-world scale. A car is ~4.5m long, a person ~1.8m tall.\n"
                "7. **Use collections**: Organize parts into named collections for complex models.\n"
                "8. **Apply transforms**: After positioning, apply scale/rotation to avoid issues.\n"
                "9. **Smooth shading + Auto Smooth**: Use smooth shading with auto-smooth normals (30-45°) "
                "for a professional look.\n"
                "10. **Parent hierarchies**: Use empty objects as group parents for organized models.\n\n"
                "## CODE PATTERNS:\n"
                "```python\n"
                "# Pattern: Create mesh with bmesh\n"
                "import bmesh\n"
                "mesh = bpy.data.meshes.new('MyMesh')\n"
                "obj = bpy.data.objects.new('MyObj', mesh)\n"
                "bpy.context.scene.collection.objects.link(obj)\n"
                "bm = bmesh.new()\n"
                "# ... build geometry ...\n"
                "bm.to_mesh(mesh)\n"
                "bm.free()\n"
                "```\n"
                "```python\n"
                "# Pattern: Subdivision modeling\n"
                "bpy.ops.mesh.primitive_cube_add()\n"
                "obj = bpy.context.active_object\n"
                "# Add supporting loops, then:\n"
                "mod = obj.modifiers.new('Subsurf', 'SUBSURF')\n"
                "mod.levels = 2\n"
                "mod.render_levels = 3\n"
                "```\n"
                "ALWAYS call bpy.context.view_layer.update() after creating/modifying objects."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": (
                            "Python code to execute in Blender. Available: bpy, bmesh, mathutils, math, random. "
                            "Use print() to return data. Code runs on Blender's main thread synchronously."
                        )
                    }
                },
                "required": ["code"]
            }
        ),

        # ───────────────────────────────────────────────────
        # SCENE / OBJECT TOOLS
        # ───────────────────────────────────────────────────
        types.Tool(
            name="get_blender_state",
            description=(
                "Get comprehensive Blender scene state: all objects with types, locations, materials, "
                "modifiers, vertex/face counts, active object, selected objects, render engine, resolution, "
                "frame range, and collection hierarchy. ALWAYS call this FIRST before modifying anything "
                "to understand what already exists in the scene."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),

        types.Tool(
            name="get_scene_hierarchy",
            description=(
                "Get full scene tree with parent-child relationships, transforms (location/rotation/scale/dimensions), "
                "material assignments, modifier stacks, and collection membership for every object. "
                "Use when you need to understand spatial relationships between objects."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "include_transform": {"type": "boolean", "description": "Include location/rotation/scale (default: true)", "default": True},
                    "max_depth": {"type": "integer", "description": "Max hierarchy depth (default: 10)", "default": 10}
                },
                "required": []
            }
        ),

        types.Tool(
            name="get_object_details",
            description=(
                "Deep inspection of a single object: full transform, modifiers with parameters, "
                "material slots with Principled BSDF values, mesh topology (verts/edges/faces), "
                "UV layers, vertex groups, shape keys, constraints, bounding box, and hierarchy."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Object name to inspect"},
                    "include_modifiers": {"type": "boolean", "default": True},
                    "include_materials": {"type": "boolean", "default": True}
                },
                "required": ["name"]
            }
        ),

        types.Tool(
            name="manage_object",
            description=(
                "Create, delete, duplicate, rename, transform, parent, and manage visibility of objects.\n\n"
                "## Actions:\n"
                "- **create**: Create primitive mesh (CUBE/SPHERE/CYLINDER/PLANE/CONE/TORUS/MONKEY/CIRCLE/GRID/ICO_SPHERE) "
                "with location, rotation, scale. ALWAYS give objects meaningful names.\n"
                "- **create_empty**: Create empty (PLAIN_AXES/ARROWS/SINGLE_ARROW/CIRCLE/CUBE/SPHERE) as group parent.\n"
                "- **delete**: Remove object by name, or '__all__' for everything.\n"
                "- **duplicate**: Copy with new mesh data.\n"
                "- **rename**: Rename object and mesh data.\n"
                "- **transform**: Set location/rotation/scale. Rotation in radians.\n"
                "- **set_parent**: Parent child to parent object.\n"
                "- **set_visibility**: Control viewport/render visibility.\n"
                "- **select**: Select/deselect objects.\n\n"
                "## Best Practices:\n"
                "- Name objects descriptively: 'Car_Body', 'Wheel_FL', not 'Cube.001'\n"
                "- Use empties as root parents for multi-part models\n"
                "- Set transforms to identity after positioning (use batch_operations/apply_all_transforms)"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Operation to perform",
                        "enum": ["create", "create_empty", "delete", "duplicate", "rename", "transform", "set_parent", "set_visibility", "select"]
                    },
                    "name": {"type": "string", "description": "Object name (for create: desired name; for others: target object)"},
                    "primitive_type": {"type": "string", "description": "For create: CUBE/SPHERE/CYLINDER/PLANE/CONE/TORUS/MONKEY/CIRCLE/GRID/ICO_SPHERE"},
                    "location": {"type": "array", "items": {"type": "number"}, "description": "[x, y, z] position"},
                    "rotation": {"type": "array", "items": {"type": "number"}, "description": "[x, y, z] rotation in radians"},
                    "scale": {"type": "array", "items": {"type": "number"}, "description": "[x, y, z] scale factors"},
                    "parent": {"type": "string", "description": "For set_parent: parent object name"},
                    "new_name": {"type": "string", "description": "For rename/duplicate: new name"},
                    "display_type": {"type": "string", "description": "For create_empty: display type"},
                    "hide_viewport": {"type": "boolean", "description": "For set_visibility"},
                    "hide_render": {"type": "boolean", "description": "For set_visibility"}
                },
                "required": ["action"]
            }
        ),

        types.Tool(
            name="manage_collection",
            description=(
                "Organize objects into collections (Blender's folder system).\n"
                "Actions: list, create, add_object, remove_object, delete.\n"
                "Use collections to organize complex models: 'Body', 'Wheels', 'Interior', 'Lights', etc."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["list", "create", "add_object", "remove_object", "delete"]},
                    "name": {"type": "string", "description": "Collection name"},
                    "object": {"type": "string", "description": "Object name (for add_object/remove_object)"},
                    "collection": {"type": "string", "description": "Target collection (alternative to name)"},
                    "parent": {"type": "string", "description": "Parent collection name (for create)"}
                },
                "required": ["action"]
            }
        ),

        # ───────────────────────────────────────────────────
        # MATERIAL TOOLS
        # ───────────────────────────────────────────────────
        types.Tool(
            name="get_materials_list",
            description=(
                "List all materials with their Principled BSDF property values "
                "(base_color, metallic, roughness, alpha, specular, transmission, emission, etc.). "
                "Shows which inputs are linked to texture nodes."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),

        types.Tool(
            name="get_material_details",
            description=(
                "Full shader node graph of a material: every node (type, location, input values), "
                "every link (from_node→to_node socket connections). Use to understand complex material setups."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Material name"}
                },
                "required": ["name"]
            }
        ),

        types.Tool(
            name="manage_material",
            description=(
                "Create, modify, assign, remove, or duplicate PBR materials.\n\n"
                "## Actions:\n"
                "- **create**: New Principled BSDF material with properties.\n"
                "- **modify**: Change existing material properties.\n"
                "- **assign**: Assign material to object (slot_index for multi-material).\n"
                "- **remove**: Delete material from scene.\n"
                "- **duplicate**: Copy material with new name.\n\n"
                "## Property Reference (Principled BSDF, Blender 4.x):\n"
                "- base_color: [R, G, B] 0-1 — surface color\n"
                "- metallic: 0-1 — 0=plastic/wood, 1=pure metal\n"
                "- roughness: 0-1 — 0=mirror, 0.3=glossy, 0.5=satin, 0.8=rough, 1=chalk\n"
                "- alpha: 0-1 — transparency (needs blend mode set)\n"
                "- specular_ior_level: 0-1 — specular intensity\n"
                "- coat_weight: 0-1 — clearcoat layer (car paint, lacquer)\n"
                "- coat_roughness: 0-1 — clearcoat smoothness\n"
                "- transmission_weight: 0-1 — glass/liquid transparency\n"
                "- ior: 1.0-3.0 — glass=1.5, water=1.33, diamond=2.42\n"
                "- emission_color: [R, G, B] — glow color\n"
                "- emission_strength: 0+ — glow intensity\n"
                "- subsurface_weight: 0-1 — skin/wax/marble subsurface scattering\n"
                "- sheen_weight: 0-1 — fabric/velvet sheen\n"
                "- anisotropic: 0-1 — brushed metal effect\n\n"
                "## Material Presets:\n"
                "- **Chrome**: metallic=1, roughness=0.05, base_color=[0.8,0.8,0.8]\n"
                "- **Car Paint**: metallic=0.9, roughness=0.2, coat_weight=1.0, coat_roughness=0.05\n"
                "- **Rubber**: metallic=0, roughness=0.9, base_color=[0.02,0.02,0.02]\n"
                "- **Glass**: transmission_weight=1, roughness=0, ior=1.5\n"
                "- **Plastic**: metallic=0, roughness=0.3, specular_ior_level=0.5\n"
                "- **Brushed Steel**: metallic=1, roughness=0.35, anisotropic=0.8\n"
                "- **Gold**: metallic=1, roughness=0.2, base_color=[1.0, 0.766, 0.336]\n"
                "- **Wood**: metallic=0, roughness=0.7, base_color=[0.4, 0.2, 0.07]"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["create", "modify", "assign", "remove", "duplicate"]},
                    "name": {"type": "string", "description": "Material name"},
                    "properties": {
                        "type": "object",
                        "description": "PBR properties: base_color, metallic, roughness, alpha, emission_color, emission_strength, transmission_weight, ior, coat_weight, coat_roughness, etc."
                    },
                    "assign_to": {"type": "string", "description": "Object name (for assign action)"},
                    "slot_index": {"type": "integer", "description": "Material slot index (for assign, default: 0)"},
                    "new_name": {"type": "string", "description": "For duplicate action"}
                },
                "required": ["action", "name"]
            }
        ),

        types.Tool(
            name="manage_shader_nodes",
            description=(
                "Advanced shader node graph manipulation: add/remove nodes, connect/disconnect sockets, set values.\n\n"
                "## Actions:\n"
                "- **add_node**: Add shader node by bl_idname (e.g., ShaderNodeTexImage, ShaderNodeMixRGB, "
                "ShaderNodeBump, ShaderNodeNormalMap, ShaderNodeTexNoise, ShaderNodeTexVoronoi, "
                "ShaderNodeColorRamp, ShaderNodeMapping, ShaderNodeTexCoord, ShaderNodeMath, "
                "ShaderNodeValToRGB, ShaderNodeSeparateXYZ, ShaderNodeCombineXYZ).\n"
                "- **remove_node**: Remove node by name.\n"
                "- **connect**: Link output socket → input socket.\n"
                "- **disconnect**: Remove link from input socket.\n"
                "- **set_value**: Set node input default value.\n\n"
                "Use this for procedural textures, normal maps, PBR texture setups, etc."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "material": {"type": "string", "description": "Material name"},
                    "action": {"type": "string", "enum": ["add_node", "remove_node", "connect", "disconnect", "set_value"]},
                    "node_type": {"type": "string", "description": "For add_node: Blender node bl_idname"},
                    "name": {"type": "string", "description": "Node name"},
                    "location": {"type": "array", "items": {"type": "number"}, "description": "[x, y] node position"},
                    "from_node": {"type": "string", "description": "For connect: source node name"},
                    "from_socket": {"type": "string", "description": "For connect: source socket name or index"},
                    "to_node": {"type": "string", "description": "For connect: target node name"},
                    "to_socket": {"type": "string", "description": "For connect: target socket name or index"},
                    "input": {"type": "string", "description": "For set_value: input name"},
                    "value": {"description": "For set_value: value to set"}
                },
                "required": ["material", "action"]
            }
        ),

        # ───────────────────────────────────────────────────
        # MODIFIER TOOLS
        # ───────────────────────────────────────────────────
        types.Tool(
            name="manage_modifier",
            description=(
                "Add, remove, apply, configure, and reorder modifiers on objects.\n\n"
                "## Actions: list, add, remove, apply, set_property, move_up, move_down\n\n"
                "## Key Modifiers for Elite Modeling:\n"
                "- **SUBSURF**: Subdivision Surface. levels=2, render_levels=3 for smooth organic shapes.\n"
                "- **MIRROR**: Mirror across axes. use_mirror_x=True + merge threshold for symmetric models.\n"
                "- **BEVEL**: Round edges for realism. width=0.005, segments=3, limit_method='ANGLE'.\n"
                "- **SOLIDIFY**: Add thickness to flat surfaces. thickness=0.02, offset=-1.\n"
                "- **BOOLEAN**: CSG operations (DIFFERENCE/UNION/INTERSECT) for hard-surface modeling.\n"
                "- **ARRAY**: Repeat geometry. count=5, relative_offset_displace=[1,0,0].\n"
                "- **SHRINKWRAP**: Snap to surface. Good for decals/stickers.\n"
                "- **CURVE**: Deform along curve path.\n"
                "- **DECIMATE**: Reduce polygon count. ratio=0.5.\n"
                "- **WEIGHTED_NORMAL**: Better auto-smooth normals.\n"
                "- **DISPLACE**: Height-map displacement.\n\n"
                "## Modifier Order Matters:\n"
                "1. Mirror (if symmetric)\n"
                "2. Boolean operations\n"
                "3. Bevel (edge rounding)\n"
                "4. Subdivision Surface (smoothing)\n"
                "5. Weighted Normal (normal cleanup)"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "object": {"type": "string", "description": "Target object name"},
                    "action": {"type": "string", "enum": ["list", "add", "remove", "apply", "set_property", "move_up", "move_down"]},
                    "modifier_type": {"type": "string", "description": "For add: SUBSURF/MIRROR/BEVEL/BOOLEAN/SOLIDIFY/ARRAY/SHRINKWRAP/CURVE/DECIMATE/DISPLACE/WEIGHTED_NORMAL etc."},
                    "name": {"type": "string", "description": "Modifier name"},
                    "properties": {"type": "object", "description": "Modifier properties to set (e.g., levels, width, segments, use_mirror_x, etc.)"}
                },
                "required": ["object", "action"]
            }
        ),

        types.Tool(
            name="manage_constraint",
            description=(
                "Add, remove, or list object constraints (TRACK_TO, COPY_LOCATION, COPY_ROTATION, "
                "LIMIT_LOCATION, FLOOR, FOLLOW_PATH, etc.)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "object": {"type": "string", "description": "Target object name"},
                    "action": {"type": "string", "enum": ["list", "add", "remove"]},
                    "constraint_type": {"type": "string", "description": "For add: constraint type"},
                    "name": {"type": "string", "description": "Constraint name"},
                    "properties": {"type": "object", "description": "Constraint properties (target, influence, etc.)"}
                },
                "required": ["object", "action"]
            }
        ),

        # ───────────────────────────────────────────────────
        # RENDER / CAMERA / LIGHT TOOLS
        # ───────────────────────────────────────────────────
        types.Tool(
            name="get_render_settings",
            description="Get current render engine, resolution, samples, color management, and format settings.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),

        types.Tool(
            name="set_render_settings",
            description=(
                "Configure render engine, resolution, samples, output format, and color management.\n\n"
                "## Recommended Settings:\n"
                "- **Preview**: engine=BLENDER_EEVEE_NEXT, resolution: 1920x1080\n"
                "- **Final**: engine=CYCLES, samples=256-512, resolution: 1920x1080 or 3840x2160\n"
                "- **Transparent BG**: film_transparent=true\n"
                "- **Color management**: view_transform='Filmic' for realistic, 'Standard' for emissive/UI"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "engine": {"type": "string", "description": "CYCLES, BLENDER_EEVEE_NEXT, or BLENDER_WORKBENCH"},
                    "resolution_x": {"type": "integer"}, "resolution_y": {"type": "integer"},
                    "film_transparent": {"type": "boolean"},
                    "output_format": {"type": "string", "description": "PNG, JPEG, OPEN_EXR, etc."},
                    "samples": {"type": "integer", "description": "Render samples (Cycles)"},
                    "fps": {"type": "integer"},
                    "cycles": {"type": "object", "description": "Cycles settings: samples, preview_samples, use_denoising, device"},
                    "eevee": {"type": "object", "description": "EEVEE settings"},
                    "color_management": {"type": "object", "description": "view_transform, look, exposure, gamma"}
                },
                "required": []
            }
        ),

        types.Tool(
            name="render_image",
            description="Render the scene to an image file and return it as base64 PNG. Use for final output.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Output file path"},
                    "format": {"type": "string", "description": "PNG, JPEG, OPEN_EXR (default: PNG)"}
                },
                "required": []
            }
        ),

        types.Tool(
            name="viewport_screenshot",
            description=(
                "Capture a quick viewport screenshot as base64 PNG. Much faster than full render. "
                "Use to check your work visually after creating/modifying objects."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),

        types.Tool(
            name="manage_camera",
            description=(
                "Create, modify, and control cameras.\n\n"
                "## Actions: create, modify, set_active, look_at\n\n"
                "## Camera Tips:\n"
                "- Standard focal length: lens=50mm (natural), 85mm (portrait), 24mm (wide), 135mm (telephoto)\n"
                "- For product shots: place camera at slight elevation, 35-85mm lens\n"
                "- Enable DOF with aperture_fstop=2.8 for background blur\n"
                "- look_at accepts object name or [x,y,z] coordinate"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["create", "modify", "set_active", "look_at"]},
                    "name": {"type": "string", "description": "Camera name"},
                    "location": {"type": "array", "items": {"type": "number"}},
                    "rotation": {"type": "array", "items": {"type": "number"}},
                    "lens": {"type": "number", "description": "Focal length in mm"},
                    "clip_start": {"type": "number"}, "clip_end": {"type": "number"},
                    "dof_enabled": {"type": "boolean"},
                    "aperture_fstop": {"type": "number", "description": "DOF aperture (lower=more blur)"},
                    "target": {"description": "For look_at: object name (string) or [x,y,z] (array)"}
                },
                "required": ["action"]
            }
        ),

        types.Tool(
            name="manage_light",
            description=(
                "Create, modify, and delete lights.\n\n"
                "## Light Types: POINT, SUN, SPOT, AREA\n\n"
                "## Lighting Presets:\n"
                "- **3-Point Studio**: Key(AREA, energy=500, 45° front-left), Fill(AREA, energy=200, front-right), "
                "Rim(SPOT, energy=300, behind-above)\n"
                "- **Outdoor**: SUN light, energy=5, slight angle\n"
                "- **Product Shot**: 2x AREA lights (soft boxes) + HDRI environment\n"
                "- **Dramatic**: Single strong SPOT with shadows\n\n"
                "## Tips:\n"
                "- AREA lights = soft shadows (best for interiors/products)\n"
                "- SUN = parallel rays (outdoor scenes)\n"
                "- SPOT = focused beam with cone\n"
                "- Energy in Watts: AREA ~200-1000W, POINT ~100-500W, SUN ~1-10"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["create", "modify", "delete"]},
                    "name": {"type": "string"},
                    "light_type": {"type": "string", "description": "POINT, SUN, SPOT, AREA"},
                    "location": {"type": "array", "items": {"type": "number"}},
                    "rotation": {"type": "array", "items": {"type": "number"}},
                    "energy": {"type": "number", "description": "Light power in Watts"},
                    "color": {"type": "array", "items": {"type": "number"}, "description": "[R, G, B] 0-1"},
                    "size": {"type": "number", "description": "Light size (larger=softer shadows)"},
                    "use_shadow": {"type": "boolean"},
                    "spot_size": {"type": "number", "description": "Spot cone angle in radians"},
                    "shape": {"type": "string", "description": "Area light shape: SQUARE, RECTANGLE, DISK, ELLIPSE"}
                },
                "required": ["action"]
            }
        ),

        # ───────────────────────────────────────────────────
        # ANIMATION TOOLS
        # ───────────────────────────────────────────────────
        types.Tool(
            name="get_animation_info",
            description="Get animation data: FPS, frame range, actions, F-Curves, keyframe counts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "object": {"type": "string", "description": "Optional: specific object to inspect"}
                },
                "required": []
            }
        ),

        types.Tool(
            name="manage_keyframes",
            description=(
                "Insert, delete, read, or clear keyframes on objects.\n"
                "Properties: 'location', 'rotation_euler', 'scale', 'modifiers[\"Name\"].property', etc."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["insert", "delete", "read", "clear_all"]},
                    "object": {"type": "string", "description": "Object name"},
                    "property": {"type": "string", "description": "Data path (e.g., 'location', 'rotation_euler')"},
                    "frame": {"type": "integer", "description": "Frame number"},
                    "value": {"description": "Value to set before keying"}
                },
                "required": ["action", "object"]
            }
        ),

        types.Tool(
            name="manage_timeline",
            description="Control timeline: set_range, set_fps, set_frame, play, stop.",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["set_range", "set_fps", "set_frame", "play", "stop"]},
                    "frame_start": {"type": "integer"}, "frame_end": {"type": "integer"},
                    "fps": {"type": "integer"}, "frame": {"type": "integer"}
                },
                "required": ["action"]
            }
        ),

        # ───────────────────────────────────────────────────
        # FILE TOOLS
        # ───────────────────────────────────────────────────
        types.Tool(
            name="manage_file",
            description="File operations: new, open, save, save_as, info.",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["new", "open", "save", "save_as", "info"]},
                    "filepath": {"type": "string"},
                    "use_empty": {"type": "boolean", "description": "For new: start with empty scene"}
                },
                "required": ["action"]
            }
        ),

        types.Tool(
            name="export_model",
            description="Export scene/selection: FBX, OBJ, GLTF, GLB, STL, USD, ABC.",
            inputSchema={
                "type": "object",
                "properties": {
                    "format": {"type": "string", "description": "FBX/OBJ/GLTF/GLB/STL/USD/ABC"},
                    "filepath": {"type": "string", "description": "Output file path"},
                    "selected_only": {"type": "boolean", "default": False},
                    "apply_modifiers": {"type": "boolean", "default": True}
                },
                "required": ["format", "filepath"]
            }
        ),

        types.Tool(
            name="import_model",
            description="Import 3D file (auto-detects format from extension): FBX, OBJ, GLTF/GLB, STL, USD, ABC, SVG.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path to import file"}
                },
                "required": ["filepath"]
            }
        ),

        # ───────────────────────────────────────────────────
        # MESH EDITING TOOLS
        # ───────────────────────────────────────────────────
        types.Tool(
            name="get_mesh_data",
            description=(
                "Get mesh topology: vertex/edge/face counts, UV layers, vertex groups, "
                "shape keys, bounding box. Optionally include vertex positions (max 5000)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Mesh object name"},
                    "include_vertices": {"type": "boolean", "default": False}
                },
                "required": ["name"]
            }
        ),

        types.Tool(
            name="edit_mesh",
            description=(
                "Low-level mesh operations via BMesh:\n"
                "- **subdivide**: Add geometry (cuts=1-4)\n"
                "- **extrude_faces**: Extrude faces with offset vector [x,y,z]\n"
                "- **inset_faces**: Inset faces (thickness, depth)\n"
                "- **bevel_edges**: Round edges (width, segments)\n"
                "- **merge_vertices**: Remove doubles (distance threshold)\n"
                "- **flip_normals** / **recalculate_normals**: Fix shading\n"
                "- **triangulate**: Convert to triangles\n"
                "- **dissolve_limited**: Simplify flat regions\n"
                "- **smooth_vertices**: Relax vertex positions"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "object": {"type": "string", "description": "Mesh object name"},
                    "action": {"type": "string", "enum": ["subdivide", "extrude_faces", "inset_faces", "bevel_edges", "merge_vertices", "flip_normals", "recalculate_normals", "triangulate", "dissolve_limited", "smooth_vertices"]},
                    "cuts": {"type": "integer"}, "offset": {"type": "array", "items": {"type": "number"}},
                    "thickness": {"type": "number"}, "depth": {"type": "number"},
                    "width": {"type": "number"}, "segments": {"type": "integer"},
                    "distance": {"type": "number"}, "angle_limit": {"type": "number"},
                    "factor": {"type": "number"}, "repeat": {"type": "integer"},
                    "faces": {"description": "'all' or array of face indices"},
                    "edges": {"description": "'all' or array of edge indices"}
                },
                "required": ["object", "action"]
            }
        ),

        types.Tool(
            name="manage_physics",
            description=(
                "Add/remove physics: RIGID_BODY, SOFT_BODY, CLOTH, PARTICLE_SYSTEM.\n"
                "Actions: add (with properties), remove, bake."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "object": {"type": "string"}, "action": {"type": "string", "enum": ["add", "remove", "bake"]},
                    "physics_type": {"type": "string", "description": "RIGID_BODY/SOFT_BODY/CLOTH/PARTICLE_SYSTEM"},
                    "rigid_body_type": {"type": "string", "description": "ACTIVE or PASSIVE"},
                    "properties": {"type": "object"}
                },
                "required": ["object", "action"]
            }
        ),

        # ───────────────────────────────────────────────────
        # GEOMETRY NODES
        # ───────────────────────────────────────────────────
        types.Tool(
            name="manage_geometry_nodes",
            description=(
                "Geometry Nodes modifier: create, read graph, set inputs, get inputs, apply, delete, set_node_group.\n"
                "Powerful for procedural geometry generation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["create", "read", "set_input", "get_inputs", "apply", "delete", "set_node_group"]},
                    "object": {"type": "string"}, "modifier_name": {"type": "string"},
                    "node_group": {"type": "string", "description": "For set_node_group"},
                    "inputs": {"type": "object", "description": "For set_input: key-value pairs"}
                },
                "required": ["action", "object"]
            }
        ),

        types.Tool(
            name="manage_node_group",
            description="CRUD for node groups (GeometryNodeTree, ShaderNodeTree, CompositorNodeTree): list, create, read, duplicate, delete.",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["list", "create", "read", "duplicate", "delete"]},
                    "name": {"type": "string"}, "tree_type": {"type": "string", "default": "GeometryNodeTree"},
                    "new_name": {"type": "string"}
                },
                "required": ["action"]
            }
        ),

        # ───────────────────────────────────────────────────
        # WORLD / ENVIRONMENT
        # ───────────────────────────────────────────────────
        types.Tool(
            name="manage_world",
            description=(
                "Control world environment for lighting and background.\n\n"
                "## Actions:\n"
                "- **get**: Current world settings\n"
                "- **set_color**: Solid background color + strength\n"
                "- **set_hdri**: Load HDRI for Image-Based Lighting (most realistic). "
                "Supports rotation for repositioning highlight directions.\n"
                "- **set_sky**: Procedural sky (NISHITA for physically accurate: sun_elevation, sun_rotation, altitude)\n"
                "- **set_strength**: Adjust environment light intensity\n"
                "- **set_volume**: Add volumetric fog (density, color)\n\n"
                "## Tips:\n"
                "- For product shots: dark background (set_color [0.01,0.01,0.01]) + AREA lights\n"
                "- For outdoor: HDRI or Nishita sky\n"
                "- For moody: low strength HDRI + volumetric fog"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["get", "set_color", "set_hdri", "set_sky", "set_strength", "set_volume"]},
                    "color": {"type": "array", "items": {"type": "number"}, "description": "[R, G, B] 0-1"},
                    "strength": {"type": "number", "description": "Environment light intensity"},
                    "hdri_path": {"type": "string"}, "rotation": {"type": "number", "description": "HDRI Z-rotation in radians"},
                    "sky_params": {"type": "object", "description": "sky_type, sun_elevation, sun_rotation, altitude, air_density, dust_density, ozone_density"},
                    "density": {"type": "number", "description": "Fog density"}
                },
                "required": ["action"]
            }
        ),

        # ───────────────────────────────────────────────────
        # ARMATURE / RIGGING
        # ───────────────────────────────────────────────────
        types.Tool(
            name="manage_armature",
            description=(
                "Full rigging toolkit: create armature, add/remove/rename bones, set bone parents, "
                "pose bones, reset pose, add IK constraints, parent mesh to armature.\n\n"
                "Actions: create, add_bone, remove_bone, list_bones, rename_bone, set_bone_parent, "
                "set_pose, reset_pose, set_ik, parent_mesh."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["create", "add_bone", "remove_bone", "list_bones", "rename_bone", "set_bone_parent", "set_pose", "reset_pose", "set_ik", "parent_mesh"]},
                    "name": {"type": "string", "description": "Armature name"},
                    "bone_name": {"type": "string"}, "head": {"type": "array", "items": {"type": "number"}},
                    "tail": {"type": "array", "items": {"type": "number"}},
                    "parent_bone": {"type": "string"}, "connected": {"type": "boolean"},
                    "roll": {"type": "number", "description": "Bone roll in degrees"},
                    "location": {"type": "array", "items": {"type": "number"}},
                    "rotation": {"type": "array", "items": {"type": "number"}},
                    "scale": {"type": "array", "items": {"type": "number"}},
                    "mesh": {"type": "string", "description": "For parent_mesh"},
                    "method": {"type": "string", "description": "ARMATURE_AUTO, ARMATURE_NAME, ARMATURE_ENVELOPE"},
                    "ik_target": {"type": "string"}, "chain_length": {"type": "integer"}, "pole_target": {"type": "string"},
                    "new_name": {"type": "string"}
                },
                "required": ["action", "name"]
            }
        ),

        types.Tool(
            name="manage_weight_paint",
            description=(
                "Vertex weight management: auto_weights, assign_vertex_group, normalize, clean, "
                "get_weights, list_groups, remove_group."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "object": {"type": "string"}, "action": {"type": "string", "enum": ["auto_weights", "assign_vertex_group", "normalize", "clean", "get_weights", "list_groups", "remove_group"]},
                    "armature": {"type": "string"}, "group": {"type": "string"},
                    "vertices": {"type": "array", "items": {"type": "integer"}},
                    "weight": {"type": "number"}, "threshold": {"type": "number"}
                },
                "required": ["object", "action"]
            }
        ),

        # ───────────────────────────────────────────────────
        # UV / TEXTURING
        # ───────────────────────────────────────────────────
        types.Tool(
            name="manage_uv",
            description=(
                "UV mapping: unwrap, smart_project, cube_project, cylinder_project, sphere_project, "
                "pack islands, create/remove/list UV layers."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "object": {"type": "string"}, "action": {"type": "string", "enum": ["unwrap", "smart_project", "cube_project", "cylinder_project", "sphere_project", "pack", "create_layer", "remove_layer", "list_layers"]},
                    "uv_layer": {"type": "string"}, "params": {"type": "object", "description": "method, angle_limit, island_margin, margin"}
                },
                "required": ["object", "action"]
            }
        ),

        types.Tool(
            name="manage_images",
            description="Image management: load, create, save, pack, unpack, list, assign_to_node, delete.",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["load", "create", "save", "pack", "unpack", "list", "assign_to_node", "delete"]},
                    "name": {"type": "string"}, "filepath": {"type": "string"},
                    "width": {"type": "integer"}, "height": {"type": "integer"},
                    "color": {"type": "array", "items": {"type": "number"}}, "is_float": {"type": "boolean"},
                    "material": {"type": "string"}, "node_name": {"type": "string"}
                },
                "required": ["action"]
            }
        ),

        types.Tool(
            name="manage_texture_bake",
            description=(
                "Texture baking (Cycles): setup bake target image on material, then bake.\n"
                "Bake types: DIFFUSE, NORMAL, AO, ROUGHNESS, EMIT, COMBINED, SHADOW.\n"
                "Actions: setup (creates target image), bake (runs bake operation)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["setup", "bake"]},
                    "object": {"type": "string"}, "bake_type": {"type": "string"},
                    "resolution": {"type": "integer", "default": 1024},
                    "samples": {"type": "integer", "default": 32},
                    "margin": {"type": "integer", "default": 16},
                    "output_path": {"type": "string"},
                    "use_selected_to_active": {"type": "boolean"},
                    "cage_extrusion": {"type": "number"}
                },
                "required": ["action", "object"]
            }
        ),

        # ───────────────────────────────────────────────────
        # CURVES / TEXT / GREASE PENCIL
        # ───────────────────────────────────────────────────
        types.Tool(
            name="manage_curve",
            description=(
                "Create and edit Bezier/NURBS/Poly curves with bevel, taper, fill, and twist.\n"
                "Actions: create, add_point, set_properties, convert_to_mesh.\n"
                "Use curves for pipes, wires, railings, trim pieces, and path animations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["create", "add_point", "set_properties", "convert_to_mesh"]},
                    "name": {"type": "string"}, "curve_type": {"type": "string", "description": "BEZIER, NURBS, POLY"},
                    "location": {"type": "array", "items": {"type": "number"}},
                    "points": {"type": "array", "description": "Array of [x,y,z] control points"},
                    "properties": {"type": "object", "description": "bevel_depth, bevel_resolution, extrude, resolution_u, fill_mode, twist_mode, use_fill_caps"},
                    "dimensions": {"type": "string", "description": "2D or 3D"},
                    "spline_index": {"type": "integer"}, "point": {"type": "array", "items": {"type": "number"}},
                    "bevel_object": {"type": "string"}, "taper_object": {"type": "string"}
                },
                "required": ["action"]
            }
        ),

        types.Tool(
            name="manage_text",
            description=(
                "3D text objects: create, modify, convert_to_mesh.\n"
                "Properties: body (text content), size, extrude (depth), bevel_depth, resolution, "
                "align_x (LEFT/CENTER/RIGHT), align_y, font_path."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["create", "modify", "convert_to_mesh"]},
                    "name": {"type": "string"}, "body": {"type": "string", "description": "Text content"},
                    "location": {"type": "array", "items": {"type": "number"}},
                    "rotation": {"type": "array", "items": {"type": "number"}},
                    "size": {"type": "number"}, "extrude": {"type": "number", "description": "Depth"},
                    "bevel_depth": {"type": "number"}, "resolution": {"type": "integer"},
                    "align_x": {"type": "string"}, "align_y": {"type": "string"},
                    "font_path": {"type": "string"}
                },
                "required": ["action"]
            }
        ),

        types.Tool(
            name="manage_grease_pencil",
            description="Grease Pencil: create, add_layer, add_stroke, set_material, list_layers.",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["create", "add_layer", "add_stroke", "set_material", "list_layers"]},
                    "name": {"type": "string"}, "layer": {"type": "string"},
                    "stroke_points": {"type": "array", "description": "Array of [x,y,z] points"},
                    "line_width": {"type": "integer"}, "pressure": {"type": "array", "items": {"type": "number"}},
                    "material_name": {"type": "string"}, "material_properties": {"type": "object", "description": "color, fill_color"},
                    "material_index": {"type": "integer"}, "frame": {"type": "integer"},
                    "location": {"type": "array", "items": {"type": "number"}}
                },
                "required": ["action"]
            }
        ),

        # ───────────────────────────────────────────────────
        # ADVANCED TOOLS
        # ───────────────────────────────────────────────────
        types.Tool(
            name="manage_shape_keys",
            description="Shape key CRUD: list, create, delete, set_value, set_key (keyframe). Used for morph targets/blend shapes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "object": {"type": "string"}, "action": {"type": "string", "enum": ["list", "create", "delete", "set_value", "set_key"]},
                    "name": {"type": "string"}, "value": {"type": "number"}, "frame": {"type": "integer"},
                    "from_mix": {"type": "boolean"}
                },
                "required": ["object", "action"]
            }
        ),

        types.Tool(
            name="manage_nla",
            description="NLA Editor: list_tracks, push_action, mute_track, solo_track. For non-linear animation mixing.",
            inputSchema={
                "type": "object",
                "properties": {
                    "object": {"type": "string"}, "action": {"type": "string", "enum": ["list_tracks", "push_action", "mute_track", "solo_track"]},
                    "action_name": {"type": "string"}, "track_name": {"type": "string"},
                    "frame_start": {"type": "integer"}, "mute": {"type": "boolean"}
                },
                "required": ["object", "action"]
            }
        ),

        types.Tool(
            name="manage_drivers",
            description="Drivers: add, remove, list. For expression-based property animation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "object": {"type": "string"}, "action": {"type": "string", "enum": ["add", "remove", "list"]},
                    "data_path": {"type": "string"}, "array_index": {"type": "integer"},
                    "expression": {"type": "string"}, "variables": {"type": "array"}
                },
                "required": ["object", "action"]
            }
        ),

        types.Tool(
            name="manage_markers",
            description="Timeline markers: add, remove, list, move. Can bind cameras to markers for camera cuts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["add", "remove", "list", "move"]},
                    "name": {"type": "string"}, "frame": {"type": "integer"}, "camera": {"type": "string"}
                },
                "required": ["action"]
            }
        ),

        types.Tool(
            name="manage_compositor",
            description=(
                "Compositor node graph: enable, disable, list_nodes, add_node, remove_node, connect, disconnect, set_value.\n"
                "Use for post-processing: Glare, Color Balance, Denoise, Lens Distortion, Vignette."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["enable", "disable", "list_nodes", "add_node", "remove_node", "connect", "disconnect", "set_value"]},
                    "node_type": {"type": "string"}, "name": {"type": "string"},
                    "location": {"type": "array", "items": {"type": "number"}},
                    "from_node": {"type": "string"}, "from_socket": {"type": "string"},
                    "to_node": {"type": "string"}, "to_socket": {"type": "string"},
                    "input": {"type": "string"}, "value": {}, "properties": {"type": "object"}
                },
                "required": ["action"]
            }
        ),

        types.Tool(
            name="manage_view_layer",
            description="View layers: list, create, delete, set_active, get_passes, enable_pass.",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["list", "create", "delete", "set_active", "get_passes", "enable_pass"]},
                    "name": {"type": "string"}, "passes": {"type": "object"}
                },
                "required": ["action"]
            }
        ),

        types.Tool(
            name="manage_preferences",
            description="Blender preferences: get, set (undo_steps, compute_device_type for GPU rendering).",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["get", "set"]},
                    "properties": {"type": "object"}
                },
                "required": ["action"]
            }
        ),

        types.Tool(
            name="manage_addons",
            description="Blender addons: list, enable, disable.",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["list", "enable", "disable"]},
                    "addon_name": {"type": "string"}, "filter_enabled": {"type": "boolean"}
                },
                "required": ["action"]
            }
        ),

        types.Tool(
            name="batch_operations",
            description=(
                "Bulk operations on multiple objects:\n"
                "- **apply_all_transforms**: Freeze transforms to identity\n"
                "- **set_origin**: ORIGIN_GEOMETRY, ORIGIN_CENTER_OF_MASS, ORIGIN_CURSOR\n"
                "- **clear_parent**: Remove all parent relationships\n"
                "- **smooth_normals**: Apply smooth shading\n"
                "- **flat_normals**: Apply flat shading\n"
                "- **shade_auto_smooth**: Smooth + auto-smooth at angle threshold\n"
                "- **purge_orphans**: Clean unused data blocks\n"
                "- **join_objects**: Merge selected meshes into one"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["apply_all_transforms", "set_origin", "clear_parent", "smooth_normals", "flat_normals", "shade_auto_smooth", "purge_orphans", "join_objects"]},
                    "objects": {"description": "'all', 'selected', or array of object names"},
                    "origin_type": {"type": "string"}, "auto_smooth_angle": {"type": "number", "description": "Degrees"}
                },
                "required": ["action"]
            }
        ),

        types.Tool(
            name="manage_scene_settings",
            description="Scene settings: get/set gravity, unit system, unit scale, frame step.",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["get", "set"]},
                    "properties": {"type": "object", "description": "gravity, use_gravity, unit_system, unit_scale, frame_step"}
                },
                "required": ["action"]
            }
        ),

        types.Tool(
            name="library_link",
            description="Link or append assets from external .blend files. Actions: list_contents, link, append.",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["list_contents", "link", "append"]},
                    "filepath": {"type": "string", "description": "Path to .blend file"},
                    "data_type": {"type": "string", "description": "Object, Material, Collection, etc."},
                    "names": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["action"]
            }
        ),

        types.Tool(
            name="manage_custom_properties",
            description="Custom properties on objects: set, get, remove, list.",
            inputSchema={
                "type": "object",
                "properties": {
                    "object": {"type": "string"}, "action": {"type": "string", "enum": ["set", "get", "remove", "list"]},
                    "key": {"type": "string"}, "value": {}, "description": {"type": "string"},
                    "min": {"type": "number"}, "max": {"type": "number"}
                },
                "required": ["object", "action"]
            }
        ),

        types.Tool(
            name="get_scene_statistics",
            description="Detailed scene statistics: object counts by type, total verts/edges/faces, materials, images, memory usage.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
    ]


# ═══════════════════════════════════════════════════════════════════════════
# MCP PROTOCOL HANDLERS
# ═══════════════════════════════════════════════════════════════════════════

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Return all available tools."""
    _init_services()
    return _get_blender_tools() + get_docs_tools()


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent | types.ImageContent]:
    """Route tool calls to appropriate handlers."""
    _init_services()
    arguments = arguments or {}

    try:
        # ── Documentation tools ──
        if name in ("search_blender_manual", "read_specific_page", "update_index"):
            return await docs_handler.handle(name, arguments)

        # ── Blender state ──
        if name == "get_blender_state":
            result = await bridge.request("/state")
            return [types.TextContent(type="text", text=_format_result(result))]

        # ── Execute code ──
        if name == "execute_blender_code":
            code = arguments.get("code", "")
            result = await bridge.request("/execute", {"code": code})
            return [types.TextContent(type="text", text=_format_result(result))]

        # ── Screenshot ──
        if name == "viewport_screenshot":
            result = await bridge.request("/screenshot")
            if result.get("status") == "success" and "image_base64" in result:
                return [
                    types.ImageContent(type="image", data=result["image_base64"], mimeType="image/png"),
                    types.TextContent(type="text", text="Viewport screenshot captured.")
                ]
            return [types.TextContent(type="text", text=_format_result(result))]

        # ── Render image ──
        if name == "render_image":
            result = await bridge.request("/api", {"tool": name, "params": arguments})
            if result.get("status") == "success" and "image_base64" in result:
                return [
                    types.ImageContent(type="image", data=result["image_base64"], mimeType="image/png"),
                    types.TextContent(type="text", text=f"Render complete. Saved to: {result.get('filepath', 'N/A')}")
                ]
            return [types.TextContent(type="text", text=_format_result(result))]

        # ── All other bridge API tools ──
        bridge_tools = {
            "get_scene_hierarchy", "get_object_details", "manage_object", "manage_collection",
            "get_materials_list", "get_material_details", "manage_material", "manage_shader_nodes",
            "manage_modifier", "manage_constraint",
            "get_render_settings", "set_render_settings", "manage_camera", "manage_light",
            "get_animation_info", "manage_keyframes", "manage_timeline",
            "manage_file", "export_model", "import_model",
            "get_mesh_data", "edit_mesh", "manage_physics",
            "manage_geometry_nodes", "manage_node_group",
            "manage_world",
            "manage_armature", "manage_weight_paint",
            "manage_uv", "manage_images", "manage_texture_bake",
            "manage_curve", "manage_text", "manage_grease_pencil",
            "manage_shape_keys", "manage_nla", "manage_drivers", "manage_markers",
            "manage_compositor", "manage_view_layer",
            "manage_preferences", "manage_addons",
            "batch_operations", "manage_scene_settings", "library_link",
            "manage_custom_properties", "get_scene_statistics",
        }

        if name in bridge_tools:
            result = await bridge.request("/api", {"tool": name, "params": arguments})
            return [types.TextContent(type="text", text=_format_result(result))]

        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Tool '{name}' failed: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error executing '{name}': {str(e)}")]


def _format_result(result: dict) -> str:
    """Format bridge result for AI consumption."""
    import json
    if not result:
        return "No response from Blender bridge. Is Blender running with the MCP Bridge addon?"
    try:
        return json.dumps(result, indent=2, default=str)
    except Exception:
        return str(result)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

async def main():
    logger.info("Starting Elite Blender MCP Server v3.0...")
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(
                notification_options=NotificationOptions(),
                experimental_capabilities={},
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
