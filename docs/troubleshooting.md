# Troubleshooting Guide

> Common issues, error recovery, and debugging procedures for the Elite Blender MCP system.

---

## Quick Diagnostic

When something goes wrong, run these checks in order:

```
1. Is Blender running? → Check taskbar
2. Is the addon enabled? → Edit > Preferences > Add-ons > "Elite MCP Bridge v2"
3. Is the bridge alive? → get_blender_state (should return scene data)
4. Is the lock file fresh? → Check ~/.blender_mcp_lock timestamp
5. Is the MCP server running? → Check IDE terminal for errors
```

---

## Error Reference

### Bridge Connection Errors

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `Bridge exhausted retry thresholds` | Blender frozen, addon crashed, or not enabled | 1. Check Blender System Console for errors. 2. Disable and re-enable the addon. 3. Restart Blender. |
| `Server disconnected without response` | Bridge HTTP server crashed mid-request | 1. Restart Blender. 2. Re-enable addon. 3. Delete `~/.blender_mcp_lock` and restart. |
| `Elite MCP Bridge is completely disconnected` | Lock file missing or Blender not running | 1. Open Blender. 2. Enable addon. 3. Verify `~/.blender_mcp_lock` exists. |
| `Bridge Server rejected payload. Status 403` | Token mismatch between MCP server and addon | 1. Restart Blender (generates new token). 2. MCP server auto-reads new token on next call. |

### Code Execution Errors

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `AST checker rejected` | Code contains blocked imports (`os`, `sys`, etc.) | Use only `bpy`, `math`, `bmesh`, `mathutils`. |
| `StructRNA of type Material has been removed` | Reference invalidated by undo checkpoint | Re-fetch all Blender data by name: `bpy.data.materials['Name']` |
| `Timeout (120s exceeded)` | Code execution took too long | Split into multiple smaller `execute_blender_code` calls. |
| `No module named 'bridge'` | Addon files not in correct directory | Re-run `install_bridge.bat`. Verify files in `%APPDATA%/...addons/elite_mcp_bridge_v2/`. |

### MCP Server Errors

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `FATAL SERVER ERROR: name 'contextlib' is not defined` | Missing import in `vector_store.py` | Add `import contextlib` to `src/services/vector_store.py` |
| `Indexer Matrix error` | Documentation database not built | Run `setup_and_index.bat` or call `update_index` tool |
| `Unknown tool: {name}` | Tool name not registered in server | Check `blender_tools_v2.py` for correct tool names |

### Blender-Side Errors

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `Multiple add-ons with the same name found` | Duplicate addon installations | Remove from `addons_core/`, keep only in `addons/` |
| `Port already in use` | Previous Blender session left port locked | Close all Blender instances. Delete `~/.blender_mcp_lock`. |
| `bpy.ops in wrong context` | Operator called from wrong mode/context | Set correct context before calling: `bpy.context.view_layer.objects.active = obj` |

---

## Debug Procedures

### 1. Enable Blender System Console
**Windows:** Window > Toggle System Console
Shows all `print()` output from addon and code execution.

### 2. Check Lock File
```cmd
type %USERPROFILE%\.blender_mcp_lock
```
Expected output:
```json
{"port": 5000, "token": "abc123..."}
```

### 3. Manual Bridge Ping
```cmd
curl http://127.0.0.1:5000/ping -H "Authorization: Bearer {token}"
```
Expected: `{"status": "success", "message": "pong"}`

### 4. Check MCP Server Logs
The MCP server outputs to stderr. Check your IDE's MCP terminal output for:
- `INFO - Starting Blender MCP v2.5 Server on STDIO Transport.`
- `INFO - Blender tools: 51 | Doc tools: 3`
- `ERROR - MCP tool execution failure for '{tool}': {error}`

### 5. Verify Addon Files
```cmd
dir "%APPDATA%\Blender Foundation\Blender\5.0\scripts\addons\elite_mcp_bridge_v2"
```
Should list 15+ Python files including `__init__.py` and all `routes_*.py`.

---

## Recovery Procedures

### Full System Reset
1. Close Blender
2. Delete `~/.blender_mcp_lock`
3. Re-run `install_bridge.bat`
4. Open Blender
5. Enable addon
6. Restart MCP server (close and reopen IDE)

### Database Reset
```cmd
del data\blender_meta.db
setup_and_index.bat
```

### Addon Reset
1. Blender > Edit > Preferences > Add-ons
2. Disable "Elite MCP Bridge v2"
3. Close Blender
4. Delete `%APPDATA%\Blender Foundation\Blender\5.0\scripts\addons\elite_mcp_bridge_v2\`
5. Re-run `install_bridge.bat`
6. Open Blender and re-enable

---

## Performance Tips

| Issue | Solution |
|-------|----------|
| Slow render | Reduce Cycles samples to 128 for preview, 512 for final |
| Heavy scene lag | Use `batch_operations: purge_orphans` to clean unused data |
| BMesh timeout | Split mesh operations across multiple calls |
| Screenshot fails | Minimize Blender UI complexity, close floating panels |
| Bridge slow response | Ensure no heavy operations blocking main thread |

---

## Known Limitations

1. **Single Blender instance**: The lock file supports only one active Blender session
2. **No network access**: Bridge is localhost-only by design (security)
3. **120s timeout**: Code execution is limited to 2 minutes per call
4. **No GUI interaction**: Cannot click UI buttons or use modal operators
5. **Thread safety**: All `bpy` calls must go through the execution queue (handled automatically)
