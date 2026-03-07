# System Architecture

> **Elite Blender MCP & Execution Bridge v2.5**

---

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         AI IDE (Cursor / Cline)                        │
│                                                                         │
│  User Prompt ──► AI Agent ──► MCP Protocol (stdio) ──► MCP Server v2.5 │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
                                      │ HTTP REST (localhost:5000)
                                      │ Bearer Token Auth
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     Blender 5.0 (Running Instance)                     │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │              Elite MCP Bridge v2 (Addon)                     │      │
│  │                                                               │      │
│  │  HTTP Server (background thread)                             │      │
│  │       │                                                       │      │
│  │       ▼                                                       │      │
│  │  Request Handler ──► Route Registry ──► Route Modules        │      │
│  │       │              (15 modules)        routes_scene.py     │      │
│  │       │                                  routes_material.py  │      │
│  │       ▼                                  routes_mesh.py      │      │
│  │  Execution Queue ──► Main Thread Timer   routes_modifier.py  │      │
│  │       │              (bpy.app.timers)    routes_render.py    │      │
│  │       ▼                                  routes_animation.py │      │
│  │  bpy / bmesh / mathutils                 routes_armature.py  │      │
│  │  (Safe Execution Sandbox)                routes_world.py     │      │
│  │                                          routes_file.py      │      │
│  │  Security Layer:                         routes_uv.py        │      │
│  │  - AST Import Checker                   routes_curves.py    │      │
│  │  - Bearer Token Validation              routes_geometry_nodes│      │
│  │  - Auto Undo Push                       routes_advanced.py   │      │
│  └──────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. MCP Server (`src/mcp_server_v2.py`)

The brain of the system. A Python process that communicates with the AI IDE over **stdio** using the Model Context Protocol.

| Property | Value |
|----------|-------|
| **Transport** | stdio (stdin/stdout) |
| **Protocol** | MCP (Model Context Protocol) |
| **Tools Exposed** | 54 total (51 build + 3 docs) |
| **Dependencies** | `mcp`, `httpx`, `fastembed`, `sqlite-vec`, `python-dotenv` |

**Responsibilities:**
- Registers all 54 tools with the IDE via `@server.list_tools()`
- Routes incoming tool calls to either `BlenderToolsHandlerV2` or `DocsToolsHandler`
- Manages the documentation vector store for semantic search

### 2. Blender Bridge Client (`src/services/blender_bridge_client.py`)

HTTP client that communicates with the Blender addon over localhost.

| Property | Value |
|----------|-------|
| **Protocol** | HTTP POST/GET to `127.0.0.1:{port}` |
| **Auth** | Bearer token from `~/.blender_mcp_lock` |
| **Timeout** | 120s read, 5s connect |
| **Retry** | Exponential backoff, 3 attempts (via `tenacity`) |

**Endpoints:**
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/ping` | GET | Health check |
| `/state` | GET | Scene context |
| `/execute` | POST | Run Python code |
| `/screenshot` | GET | Viewport capture |
| `/api` | POST | Unified v2 tool routing |

### 3. Bridge Addon (`src/bridge/`)

A multi-file Blender addon that runs an HTTP server inside Blender's background thread.

| File | Purpose | Lines |
|------|---------|:-----:|
| `__init__.py` | Addon lifecycle, HTTP server, request handler, execution queue | 209 |
| `security.py` | AST-based import validation | 50 |
| `routes_scene.py` | Scene hierarchy, objects, collections, statistics | 250+ |
| `routes_material.py` | Materials, shader nodes | 180+ |
| `routes_mesh.py` | BMesh operations, edit mode | 120+ |
| `routes_modifier.py` | Modifier CRUD | 90+ |
| `routes_render.py` | Render settings, camera, lights, render execution | 150+ |
| `routes_animation.py` | Keyframes, timeline, NLA, markers | 60+ |
| `routes_file.py` | File I/O, import/export, library link | 110+ |
| `routes_world.py` | World settings, HDRI, sky, fog | 70+ |
| `routes_armature.py` | Armature, bones, IK, weight paint | 70+ |
| `routes_uv.py` | UV unwrap, projection, bake | 60+ |
| `routes_geometry_nodes.py` | GeoNodes modifier, node groups | 70+ |
| `routes_curves.py` | Curves, text, grease pencil | 50+ |
| `routes_advanced.py` | Shape keys, drivers, custom props, compositor, physics | 80+ |

### 4. Tool Definitions (`src/mcp_tools/`)

| File | Purpose |
|------|---------|
| `blender_tools_v2.py` | JSON Schema definitions for all 51 Blender tools |
| `blender_tools_handler_v2.py` | Routes MCP calls → bridge HTTP requests |
| `docs_tools.py` | 3 documentation tools (search, read, index) |

### 5. Services (`src/services/`)

| File | Purpose |
|------|---------|
| `database.py` | SQLite database manager with transaction context manager |
| `vector_store.py` | Embedding generation (fastembed) + vector search (sqlite-vec) |
| `indexer_service.py` | HTML → Markdown parser, document chunker, index builder |
| `blender_bridge_client.py` | HTTP client for bridge communication |

---

## Data Flow

### Tool Execution Flow
```
1. User types prompt in IDE
2. AI decides to call MCP tool (e.g., manage_object)
3. MCP Server receives tool call via stdio
4. BlenderToolsHandlerV2.handle() routes to /api endpoint
5. Bridge Client sends HTTP POST to Blender
6. Bridge Addon receives request on background thread
7. Request is queued in execution_queue
8. Main thread timer dequeues and executes via bpy
9. Result JSON returned to Bridge Client
10. MCP Server formats and returns to AI
```

### Documentation Search Flow
```
1. AI calls search_blender_manual("query")
2. DocsToolsHandler.handle() invoked
3. VectorStore.search() generates query embedding
4. sqlite-vec performs KNN search in SQL
5. Top-K chunks returned with file paths and distances
6. Formatted markdown returned to AI
```

---

## Security Model

| Layer | Protection |
|-------|------------|
| **Transport** | localhost only (127.0.0.1) — no external network access |
| **Authentication** | Bearer token generated per-session, stored in `~/.blender_mcp_lock` |
| **Code Sandbox** | AST checker blocks `os`, `sys`, `subprocess`, `socket`, `eval`, `exec`, `open` |
| **Undo Safety** | Automatic `bpy.ops.ed.undo_push()` before each code execution |
| **Timeout** | 120-second execution limit per code block |

---

## File Tree

```
blender_mcp_project/
├── .gitignore                    # Git ignore rules
├── .env                          # Environment variables (DOCS_DIR, DB_PATH)
├── Gemini.md                     # Elite AI system prompt
├── README.md                     # Project overview
├── LICENSE                       # Modified MIT License
├── pyproject.toml                # Python project metadata (v2.5.0)
│
├── docs/                         # 📚 Documentation
│   ├── index.md                  # Master documentation index
│   ├── memory-index.md           # Daily memory log index
│   ├── README.md
│   ├── architecture.md
│   ├── mcp-tools-reference.md
│   ├── bridge-addon-guide.md
│   ├── setup-guide.md
│   ├── workflows.md
│   └── troubleshooting.md
│
├── memory/                       # 🧠 Daily session logs
│   └── [DATE]-memory.md
│
├── src/
│   ├── mcp_server_v2.py          # MCP Server entry point (v2.5)
│   ├── bridge/                   # Blender Addon (15 modules)
│   │   ├── __init__.py           # HTTP server, execution queue, dynamic port
│   │   ├── security.py           # AST import validation
│   │   └── routes_*.py           # 13 route handlers
│   ├── mcp_tools/                # Tool definitions & handler
│   │   ├── blender_tools_v2.py
│   │   ├── blender_tools_handler_v2.py
│   │   └── docs_tools.py
│   └── services/                 # Core services
│       ├── database.py
│       ├── vector_store.py
│       ├── indexer_service.py
│       └── blender_bridge_client.py
│
├── data/                         # SQLite DB & vector index (gitignored)
├── blender_manual_html/          # Blender 5.0 HTML manual cache (gitignored)
├── outputs/                      # Generated models, renders, exports (gitignored)
│
├── install_bridge.bat            # Addon installer
├── setup_and_index.bat           # Environment setup
├── start_mcp.bat                 # Server launcher
└── install_*_mcp.bat             # IDE-specific MCP injectors
```
