# 🚀 Elite Blender MCP & Execution Bridge v2.5

![Blender MCP Logo](https://img.shields.io/badge/Blender-5.0.1-orange.svg) 
![MCP Protocol](https://img.shields.io/badge/Model_Context_Protocol-Enabled-blue.svg)
![License](https://img.shields.io/badge/License-Modified_MIT-red.svg)

An advanced, fully local **Model Context Protocol (MCP) Server** and embedded **Execution Bridge** that transforms any AI Agent into a completely autonomous 3D Technical Artist natively inside Blender.

Version 2.5 expands the system to provide **~65 structured tools**, offering near-complete API coverage over Blender's subsystems including Geometry Nodes, Rigging, Environments, Nodes, Animation, Compositor, Physics, UVs, and Extensibility—all executed safely via local bridge communication.

---

## 🧠 Core Architecture

The system is composed of two highly optimized, interdependent modules:

### 1. The Expert Knowledge Base (MCP Server V2)
A scalable, modular MCP server operating locally over `stdio`. It exposes tools dynamically to the AI IDE.
- **Vast Tool Set:** Provides ~65 distinct tools across all Blender subsystems directly to the AI.
- **RAG Documentation System:** Features a built-in zero-dependency search engine indexing the Blender 5.0 HTML manual with local FAISS vector search, helping the AI understand modern API changes instantly.
- **RESTful Routing:** Translates MCP tool calls into standard JSON payloads routed dynamically to specific endpoints on the Blender bridge.

### 2. The Elite Execution Bridge (Modular Blender Add-on)
A multi-file, secure REST API server running *inside* Blender's background thread.
- **Modular Route Handlers:** Requests are mapped to dedicated routes (`routes_geometry_nodes`, `routes_armature`, `routes_materials`, etc.) preventing monolithic server bottlenecks.
- **Main-Thread Queueing:** Bypasses Blender's strict thread constraints. The HTTP server queues operations which are safely dequeued and executed on the main thread via `bpy.app.timers`.
- **Fail-Safe Undo Hooks:** Modifying operations automatically trigger an Undo Push (`bpy.ops.ed.undo_push`). If a tool fails or the AI causes an exception, the scene reverts automatically.
- **AST Security:** Blocks lethal OS-level Python imports (`subprocess`, `os`) via an Abstract Syntax Tree verification layer for raw code execution.

---

## 🛠️ MCP Tools Exposed to AI

The v2.5 server exposes an enormous toolkit to the AI Agent. Some highlights include:

*   **Geometry Nodes:** `manage_geometry_nodes` (Full CRUD, smart input node parameter assignment)
*   **Rigging & Weights:** `manage_armature` (Bone CRUD, IK, posing), `manage_weight_paint` (Auto-weights, vertex groups)
*   **World & Env:** `manage_world` (HDRI logic, Nishita Sky, Volumetric fog)
*   **Materials & Shaders:** `manage_material`, `manage_shader_nodes` (Full modular shading network creation)
*   **UV & Bake:** `manage_uv` (Unwrap, project, pack), `manage_texture_bake` (Auto node setup + cyclic baking)
*   **NURBS/Text/GPencil:** `manage_curve`, `manage_text`, `manage_grease_pencil`
*   **Advanced Animation:** `manage_shape_keys`, `manage_nla`, `manage_drivers`, `manage_markers`
*   **Compositing:** `manage_compositor` (Post-processing nodes)
*   **Operations & Utility:** `batch_operations`, `library_link`, `manage_addons`, `manage_preferences`
*   **Core Systems:** `manage_object`, `manage_mesh`, `manage_modifier`, `manage_physics`, `render_image`, `get_blender_state`, `execute_blender_code`

---

## ⚙️ Installation & Deployment

### Phase A: Setup the Python Environment
1. Clone this repository to your local machine.
2. *(Optional)* If using the RAG documentation tools, download the official Blender 5.0 HTML Manual and extract all `.html` files into the `./blender_manual_html` folder.
3. Run the Windows automated setup script to build the venv and install dependencies:
   ```cmd
   > setup_and_index.bat
   ```

### Phase B: Setup the Blender Add-on
1. Run the installation script to copy the new v2.5 multi-file Add-on into your `%APPDATA%`:
   ```cmd
   > install_bridge.bat
   ```
2. Open Blender 5.0.
3. Navigate to **Edit** > **Preferences** > **Add-ons**.
4. Search for `"Elite MCP Bridge v2"` and enable it.
   *(Upon activation, the Add-on creates a background HTTP server and locks to port 5000+ securely).*

### Phase C: IDE Injection
Inject the MCP Server into your preferred IDE's configuration automatically (supports Cursor, RooCode / Cline):
```cmd
> install_gemini_mcp.bat
```
*(Or use `install_codex_mcp.bat` / `install_qwen_mcp.bat` / manual `mcp_server_v2.py` injection).*

---

## 📁 Project Structure

```text
blender_mcp_project/
├── .env                    # Environment variables
├── data/                   # Database & FAISS Vector Index
├── src/                    # Python Source Code
│   ├── mcp_server_v2.py    # The Brain (LLM Entry Point handling 65+ tools)
│   ├── bridge/             # The Blender Add-on Module
│   │   ├── __init__.py     # bl_info and Lifecycle Manager
│   │   ├── security.py     # AST code validator
│   │   ├── routes_*.py     # Modular Handlers (Mesh, Materials, Armature, GeoNodes...) 
│   ├── mcp_tools/          # Tool definitions for MCP 
│   │   ├── blender_tools_v2.py # Defines all inputSchemas
│   │   ├── blender_tools_handler_v2.py # Bridge execution client
│   └── indexer.py          # Documentation Indexer
├── install_bridge.bat      # Helper script for installing the Add-on
├── setup_and_index.bat     # Installs dependencies
└── start_mcp.bat           # IDE bootstrap command 
```

---

## 🤖 Example Agentic Workflow

In your configured IDE, ask your AI:

> *"Search the Blender manual for Geometry Nodes logic. Create a procedural building generator using `manage_geometry_nodes`. Setup an HDRI using `manage_world`, rig a basic camera path with `manage_curve`, and use `take_blender_screenshot` so I can see the final result."*

The AI will now use specific, sandboxed, and highly-reliable structured tools instead of raw script execution, providing a vastly more stable architecture.

---

## ⚖️ License & Terms of Use

This project is released under a **Modified MIT License** with strict Commercial Use restrictions.

By using this software, you agree to the conditions outlined in the `LICENSE` file.
- ✅ **Free for Personal Use:** Hobbyists, students, and individual developers.
- ✅ **Free for Open Source:** Integrating into 100% free, open-source projects.
- ❌ **Commercial Use Prohibited:** You may NOT use this software, its architecture, or its source code to generate revenue, within a for-profit studio pipeline, or as part of a paid product/SaaS platform without purchasing a Commercial License from the author.
