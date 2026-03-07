"""
Blender Expert MCP Server v2.5
Exposes ~65 structured Blender tools + 3 documentation tools via MCP protocol.
"""
import os
import sys
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["DATASETS_VERBOSITY"] = "error"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import asyncio
import logging
from pathlib import Path

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
import mcp.types as types

from dotenv import load_dotenv

# Import Domain Services
from services.database import DatabaseManager
from services.vector_store import VectorStore
from services.indexer_service import IndexerService
from services.blender_bridge_client import BlenderBridgeClient

# Import v2 Tools
from mcp_tools.blender_tools_v2 import get_blender_tools_v2
from mcp_tools.blender_tools_handler_v2 import BlenderToolsHandlerV2
from mcp_tools.docs_tools import get_docs_tools, DocsToolsHandler

logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
DOCS_DIR = os.getenv("DOCS_DIR", "./docs_source")
DB_PATH = os.getenv("DB_PATH", "./data/blender_meta.db")
BLENDER_LOCK_FILE = Path.home() / ".blender_mcp_lock"

# Dependency Injection
db_manager = DatabaseManager(DB_PATH)
vector_store = VectorStore(db_manager)
indexer_service = IndexerService(db_manager, vector_store, DOCS_DIR)
bridge_client = BlenderBridgeClient(BLENDER_LOCK_FILE)

docs_handler = DocsToolsHandler(db_manager, vector_store, indexer_service, DOCS_DIR)
blender_handler = BlenderToolsHandlerV2(bridge_client)

server = Server("blender-expert-mcp")

# Cache tool name sets for fast routing
_blender_tool_names = {t.name for t in get_blender_tools_v2()}
_docs_tool_names = {t.name for t in get_docs_tools()}


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Combines all v2 Blender tools + documentation tools."""
    return get_blender_tools_v2() + get_docs_tools()


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Routes tool calls to the appropriate handler."""
    if not arguments:
        arguments = {}

    try:
        if name in _blender_tool_names:
            return await blender_handler.handle(name, arguments)
        elif name in _docs_tool_names:
            return await docs_handler.handle(name, arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"MCP tool execution failure for '{name}': {e}")
        return [types.TextContent(
            type="text",
            text=f"FATAL SERVER ERROR executing '{name}': {e}"
        )]


async def main():
    logger.info("Starting Blender MCP v2.5 Server on STDIO Transport.")
    logger.info(f"Blender tools: {len(_blender_tool_names)} | Doc tools: {len(_docs_tool_names)}")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="blender-expert-mcp",
                server_version="2.5.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            )
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("MCP Server v2.5 shutdown cleanly.")
