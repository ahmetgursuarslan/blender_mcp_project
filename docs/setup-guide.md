# Setup Guide

> Complete installation and configuration guide for the Elite Blender MCP system.

---

## Prerequisites

| Component | Version | Purpose |
|-----------|---------|---------|
| **Windows** | 10/11 | Operating system |
| **Python** | 3.11+ | MCP server runtime |
| **Blender** | 5.0+ | 3D modeling engine |
| **MCP IDE** | Cursor / RooCode / Cline | AI assistant interface |

---

## Phase A: Python Environment

### 1. Clone the Repository
```cmd
git clone <repo-url>
cd blender_mcp_project
```

### 2. Setup Virtual Environment & Dependencies
```cmd
> setup_and_index.bat
```
This script:
- Creates a Python virtual environment in `./venv`
- Installs all dependencies from `pyproject.toml`
- (Optional) Indexes the Blender HTML manual for documentation search

### Manual Setup (if bat fails)
```cmd
python -m venv venv
venv\Scripts\activate
pip install -e .
```

### Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| `mcp` | latest | Model Context Protocol SDK |
| `httpx` | latest | Async HTTP client for bridge communication |
| `tenacity` | latest | Retry logic with exponential backoff |
| `fastembed` | latest | CPU-only ONNX embedding model |
| `sqlite-vec` | latest | Vector search inside SQLite |
| `python-dotenv` | latest | Environment variable loading |
| `numpy` | latest | Array operations for embeddings |

---

## Phase B: Blender Addon

### 1. Install the Addon
```cmd
> install_bridge.bat
```
Target directory:
```
%APPDATA%\Blender Foundation\Blender\5.0\scripts\addons\elite_mcp_bridge_v2\
```

### 2. Enable in Blender
1. Open Blender 5.0
2. **Edit > Preferences > Add-ons**
3. Search: `"Elite MCP Bridge v2"`
4. Enable the checkbox
5. Verify: Open **Window > Toggle System Console** — you should see:
   ```
   Elite MCP Bridge v2 started on port 5000
   ```

### 3. Verify Connection
A lock file should appear at:
```
C:\Users\{username}\.blender_mcp_lock
```
Contents: `{"port": 5000, "token": "..."}`

---

## Phase C: IDE Integration

### Cursor / RooCode
```cmd
> install_gemini_mcp.bat
```
This injects the MCP server configuration into your IDE's settings.

### Manual Configuration
Add to your IDE's MCP configuration:
```json
{
  "mcpServers": {
    "blender-expert-mcp": {
      "command": "C:\\Users\\{username}\\antigravity-repo\\blender_mcp_project\\venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\{username}\\antigravity-repo\\blender_mcp_project\\src\\mcp_server_v2.py"],
      "env": {}
    }
  }
}
```

---

## Environment Variables (`.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `DOCS_DIR` | `./docs_source` | Path to Blender HTML manual |
| `DB_PATH` | `./data/blender_meta.db` | SQLite database path |

---

## Documentation Search Setup (Optional)

To enable the `search_blender_manual` tool:

1. Download the Blender 5.0 HTML manual
2. Extract all `.html` files into `./blender_manual_html/`
3. Run the indexer:
   ```cmd
   > setup_and_index.bat
   ```
   Or use the MCP tool: `update_index`

---

## Verification Checklist

- [ ] `venv/` directory exists with installed packages
- [ ] Blender addon is visible in Add-ons preferences
- [ ] System console shows "Elite MCP Bridge v2 started on port 5000"
- [ ] `~/.blender_mcp_lock` file exists
- [ ] IDE shows `blender-expert-mcp` in MCP servers list
- [ ] `get_blender_state` tool returns valid scene data
