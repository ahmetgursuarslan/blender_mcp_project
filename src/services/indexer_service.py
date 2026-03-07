import os
import contextlib
import hashlib
import re
import logging
from pathlib import Path
from typing import List, Optional

from bs4 import BeautifulSoup
from markdownify import markdownify as md

from services.database import DatabaseManager
from services.vector_store import VectorStore

logger = logging.getLogger(__name__)

class IndexerService:
    """
    Handles HTML reading, conversion to Markdown, chunking, and feeding vectors
    into the VectorStore. Focuses on resilient parsing.
    """
    def __init__(self, db_manager: DatabaseManager, vector_store: VectorStore, docs_dir: str, chunk_size: int = 600):
        self.db = db_manager
        self.vector_store = vector_store
        self.docs_dir = Path(docs_dir)
        self.chunk_size = chunk_size

    def _get_file_hash(self, file_path: str) -> str:
        """Calculates MD5 hash for rapid cache invalidation."""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def parse_html_to_markdown(self, html_content: str) -> str:
        """Dumb-proof resilient HTML to Markdown parser."""
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Remove navigation/noise
            for tag in soup(["nav", "footer", "script", "style"]):
                tag.decompose()
                
            for class_name in ["sphinxsidebar", "related", "wy-nav-side", "headerlink"]:
                for element in soup.find_all(class_=class_name):
                    element.decompose()
                    
            article = soup.find('main') or soup.find('article') or soup.find('div', class_='documentwrapper') or soup.find('body')
            if not article:
                return ""
                
            return md(str(article), heading_style="ATX")
        except Exception as e:
            logger.error(f"Failed to parse HTML structure securely: {e}")
            return ""

    def semantic_chunk_markdown(self, markdown_text: str) -> List[str]:
        """Simple, deterministic semantic chunking based on headers and word count constraints."""
        lines = markdown_text.split('\n')
        chunks = []
        current_chunk = []
        current_word_count = 0
        
        for line in lines:
            words = len(line.split())
            if bool(re.match(r'^#{1,3}\s+', line.strip())) and current_word_count > 0:
                chunks.append('\n'.join(current_chunk).strip())
                current_chunk = [line]
                current_word_count = words
            elif current_word_count + words > self.chunk_size and current_chunk:
                chunks.append('\n'.join(current_chunk).strip())
                current_chunk = [line]
                current_word_count = words
            else:
                current_chunk.append(line)
                current_word_count += words
                
        if current_chunk:
            chunks.append('\n'.join(current_chunk).strip())
            
        return [c for c in chunks if c]

    def process_file_resilient(self, file_path: Path) -> bool:
        """
        Process exactly one file resiliently, rolling back completely on error.
        Returns True if processing succeeded or wasn't needed. False on fatal failure.
        """
        try:
            rel_path = file_path.relative_to(self.docs_dir).as_posix()
            last_modified = file_path.stat().st_mtime
            current_hash = self._get_file_hash(str(file_path))
            
            with contextlib.closing(self.db.get_connection()) as conn:
                cursor = conn.execute("SELECT last_modified, content_hash FROM documents WHERE file_path = ?", (rel_path,))
                row = cursor.fetchone()
                
                # Cache checking
                if row:
                    db_mtime, db_hash = row["last_modified"], row["content_hash"]
                    if last_modified <= db_mtime and current_hash == db_hash:
                        return True # Sub-system unchanged, skip
                        
            # If cache miss, parse & update
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
                
            markdown = self.parse_html_to_markdown(html_content)
            if not markdown:
                logger.warning(f"File {file_path} yielded zero valid markdown. Skipping vector mapping.")
                return True
                
            chunks = self.semantic_chunk_markdown(markdown)
            if not chunks:
                return True
                
            # Upsert document into sqlite-vec with atomicity
            self.vector_store.upsert_document(rel_path, last_modified, current_hash, chunks)
            return True
            
        except Exception as e:
            logger.error(f"Critical isolated failure computing vector mesh for {file_path}: {e}")
            return False

    def index_all(self):
        """Scans the designated DOCS directory and indexes all local files."""
        if not self.docs_dir.exists():
            logger.info(f"Directory {self.docs_dir} created. Please populate with HTML blender docs.")
            self.docs_dir.mkdir(parents=True, exist_ok=True)
            return

        html_files = list(self.docs_dir.rglob("*.html"))
        logger.info(f"Found {len(html_files)} HTML files. Indexing via CPU Matrix engine...")
        
        success = 0
        failed = 0
        for file in html_files:
            if self.process_file_resilient(file):
                success += 1
            else:
                failed += 1
                
        logger.info(f"Indexing Complete. Successful: {success}. Failed: {failed}.")
