import asyncio
from pathlib import Path

import mcp.types as types

from services.database import DatabaseManager
from services.vector_store import VectorStore
from services.indexer_service import IndexerService

def get_docs_tools():
    """Returns the tool definitions for documentation."""
    return [
        types.Tool(
            name="search_blender_manual",
            description="Executes a CPU-optimized semantic search across the documentation database and returns the most relevant chunks. Great for querying general concepts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language query to search for. E.g. 'How to script procedural extrusions via BMesh?'"
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="read_specific_page",
            description="Reads the full Markdown-converted content of a specific HTML file from the local disk cache without relying on semantic chunking.",
            inputSchema={
                "type": "object",
                "properties": {
                    "relative_path": {
                        "type": "string",
                        "description": "Relative path to the HTML file (e.g., 'render/cycles/baking.html')."
                    }
                },
                "required": ["relative_path"]
            }
        ),
        types.Tool(
            name="update_index",
            description="Triggers the indexer to rescan the DOCS folder and update the SQLite vector geometries. Runs securely as a background transactional job.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

class DocsToolsHandler:
    def __init__(self, db_manager: DatabaseManager, vector_store: VectorStore, indexer: IndexerService, docs_dir: str):
        self.db = db_manager
        self.vector_store = vector_store
        self.indexer = indexer
        self.docs_dir = Path(docs_dir)

    async def handle(self, name: str, arguments: dict):
        if name == "search_blender_manual":
            query = arguments.get("query")
            
            # Offload blocking SQLite-VEC lookup to background thread
            results = await asyncio.to_thread(self.vector_store.search, query, 4)
            
            if not results:
                return [types.TextContent(type="text", text="No matches found in the documentation database.")]
                
            formatted = []
            for idx, r in enumerate(results):
                formatted.append(f"### Source: `{r['file_path']}` (Dist: {r['distance']:.4f})\n\n{r['content']}\n")
                
            return [types.TextContent(type="text", text="\n---\n".join(formatted))]

        elif name == "read_specific_page":
            rel_path = arguments.get("relative_path")
            target = (self.docs_dir / rel_path).resolve()
            
            # Anti path-traversal firewall
            if not str(target).startswith(str(self.docs_dir.resolve())):
                 return [types.TextContent(type="text", text="Security Error: Prevented unauthorized path traversal.")]
                 
            if not target.exists() or not target.is_file():
                return [types.TextContent(type="text", text=f"Error: {rel_path} does not exist.")]
                
            try:
                # Direct read
                with open(target, 'r', encoding='utf-8', errors='ignore') as f:
                    html_content = f.read()
                md_content = self.indexer.parse_html_to_markdown(html_content)
                return [types.TextContent(type="text", text=md_content or "Warning: Successfully loaded file but no valid markdown could be parsed.")]
            except Exception as e:
                return [types.TextContent(type="text", text=f"Read failure: {e}")]
                
        elif name == "update_index":
            # Run the heavy indexing job async
            await asyncio.to_thread(self.indexer.index_all)
            return [types.TextContent(type="text", text="Indexer Matrix has been fully recalibrated. Database synced with disk state.")]
