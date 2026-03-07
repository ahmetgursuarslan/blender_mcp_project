"""
Blender Tools Handler v2.0
Routes all MCP tool calls through the unified /api endpoint on the bridge.
"""
import asyncio
import json
import logging
import mcp.types as types
from services.blender_bridge_client import BlenderBridgeClient
from tenacity import RetryError

logger = logging.getLogger(__name__)

# Tools that return images
IMAGE_TOOLS = {"take_blender_screenshot", "render_image", "viewport_screenshot"}

# Tools routed via /api (everything except legacy 3)
LEGACY_TOOLS = {"get_blender_state", "execute_blender_code", "take_blender_screenshot"}


class BlenderToolsHandlerV2:
    """
    Unified handler that routes all tool calls through the bridge.
    Legacy tools use their original endpoints.
    New v2 tools use the unified POST /api endpoint.
    """

    def __init__(self, bridge_client: BlenderBridgeClient):
        self.bridge = bridge_client

    async def _safe_bridge_call(self, endpoint: str, payload: dict = None) -> dict:
        try:
            return await self.bridge.request(endpoint, payload)
        except RetryError:
            return {"status": "error", "message": "Blender bridge exhausted retry thresholds. Is Blender frozen?"}
        except Exception as e:
            return {"status": "error", "message": f"Bridge transport error: {e}"}

    async def handle(self, name: str, arguments: dict) -> list[types.TextContent | types.ImageContent]:
        """Route a tool call to the appropriate bridge endpoint."""

        # ─── Universal health check (skip for get_blender_state which is itself a health indicator) ───
        if name != "get_blender_state":
            ping = await self._safe_bridge_call("/ping")
            if ping.get("status") != "success":
                return [types.TextContent(type="text", text=f"Connection blocked: Blender Bridge is not responding. Ensure Blender is running with the Elite MCP Bridge addon enabled. Ping result: {ping.get('message', 'No response')}")]

        # ─── Legacy: get_blender_state ───
        if name == "get_blender_state":
            result = await self._safe_bridge_call("/state")
            if result.get("status") == "success":
                return [types.TextContent(type="text", text=json.dumps(result.get("data", {}), indent=2))]
            return [types.TextContent(type="text", text=f"Failed: {result.get('message', 'Unknown')}")]

        # ─── Legacy: execute_blender_code ───
        elif name == "execute_blender_code":
            code = arguments.get("code")
            result = await self._safe_bridge_call("/execute", {"code": code})
            if result.get("status") == "success":
                return [types.TextContent(type="text", text=f"[SUCCESS] {result.get('message', '')}\n[STDOUT]\n{result.get('output', '')}")]
            else:
                return [types.TextContent(type="text", text=f"[FAILURE] {result.get('message', '')}\n[TRACEBACK]\n{result.get('traceback', '')}")]

        # ─── Legacy: take_blender_screenshot ───
        elif name == "take_blender_screenshot":
            result = await self._safe_bridge_call("/screenshot")
            if result.get("status") == "success" and "image_base64" in result:
                return [types.ImageContent(type="image", data=result["image_base64"], mimeType="image/png")]
            return [types.TextContent(type="text", text=f"Screenshot failed: {result.get('message', '')}")]

        # ─── v2 Tools: route via /api ───
        else:
            result = await self._safe_bridge_call("/api", {"tool": name, "params": arguments})

            if result.get("status") == "success":
                # Check if result contains an image
                if "image_base64" in result:
                    return [types.ImageContent(type="image", data=result["image_base64"], mimeType="image/png")]

                # Text response
                response_data = result.get("data", result.get("message", "Done."))
                if isinstance(response_data, (dict, list)):
                    text = json.dumps(response_data, indent=2, default=str)
                else:
                    text = str(response_data)

                return [types.TextContent(type="text", text=text)]
            else:
                error_msg = result.get("message", "Unknown error")
                tb = result.get("traceback", "")
                full_msg = f"[ERROR] {error_msg}"
                if tb:
                    full_msg += f"\n[TRACEBACK]\n{tb}"
                return [types.TextContent(type="text", text=full_msg)]
