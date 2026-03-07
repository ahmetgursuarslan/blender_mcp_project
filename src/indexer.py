import os
import sqlite3
import hashlib
import re
from typing import List, Tuple
from pathlib import Path

import faiss
import numpy as np
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DOCS_DIR = os.getenv("DOCS_DIR", "./docs_source")
DB_PATH = os.getenv("DB_PATH", "./data/blender_meta.db")
FAISS_PATH = os.getenv("FAISS_PATH", "./data/blender_vectors.index")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "600"))

# Initialize SentenceTransformer model
model = SentenceTransformer("all-MiniLM-L6-v2")
EMBEDDING_DIM = model.get_sentence_embedding_dimension()

def get_file_hash(file_path: str) -> str:
    """Calculate MD5 hash of a file."""
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def init_db(db_path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Documents table tracks files and their modification state
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE NOT NULL,
            last_modified REAL NOT NULL,
            content_hash TEXT NOT NULL
        )
    ''')
    
    # Chunks table stores the vector ID and markdown content mapped to documents
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL,
            markdown_content TEXT NOT NULL,
            faiss_id INTEGER UNIQUE NOT NULL,
            FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
        )
    ''')
    
    # App-level tracking for the next available FAISS ID
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')
    
    # Ensure foreign keys are enabled
    cursor.execute("PRAGMA foreign_keys = ON")
    conn.commit()
    return conn

def get_next_faiss_id(conn: sqlite3.Connection) -> int:
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM meta WHERE key = 'next_faiss_id'")
    row = cursor.fetchone()
    if row:
        return int(row[0])
    return 0

def increment_faiss_id(conn: sqlite3.Connection, current: int, increment: int):
    cursor = conn.cursor()
    new_val = current + increment
    cursor.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('next_faiss_id', ?)", (str(new_val),))
    conn.commit()

def load_or_create_faiss_index() -> faiss.IndexIDMap:
    if os.path.exists(FAISS_PATH):
        try:
            return faiss.read_index(FAISS_PATH)
        except Exception as e:
            print(f"Error loading existing FAISS index: {e}. Recreating.")
            
    base_index = faiss.IndexFlatL2(EMBEDDING_DIM)
    index = faiss.IndexIDMap(base_index)
    return index

def save_faiss_index(index: faiss.IndexIDMap):
    os.makedirs(os.path.dirname(FAISS_PATH), exist_ok=True)
    faiss.write_index(index, FAISS_PATH)

def parse_html_to_markdown(html_content: str) -> str:
    soup = BeautifulSoup(html_content, 'lxml')
    
    # Remove unwanted tags, including Sphinx-specific navigation items
    for tag in soup(["nav", "footer", "script", "style"]):
        tag.decompose()
        
    for class_name in ["sphinxsidebar", "related", "wy-nav-side", "headerlink"]:
        for element in soup.find_all(class_=class_name):
            element.decompose()
            
    # Extract main article content if available, else use body
    article = soup.find('main') or soup.find('article') or soup.find('div', class_='documentwrapper') or soup.find('body')
    if not article:
        return ""
        
    # Convert back to string and generate markdown
    cleaned_html = str(article)
    markdown_text = md(cleaned_html, heading_style="ATX")
    return markdown_text

def semantic_chunk_markdown(markdown_text: str, max_words: int) -> List[str]:
    """
    Chunk markdown based on H1/H2/H3 headers and max word count.
    Preserves contextual integrity.
    """
    lines = markdown_text.split('\n')
    chunks = []
    current_chunk = []
    current_word_count = 0
    
    for line in lines:
        is_header = bool(re.match(r'^#{1,3}\s+', line.strip()))
        words_in_line = len(line.split())
        
        # Split on headers if maintaining the block exceeds max_words, OR if it's naturally a good break point
        if is_header and current_word_count > 0:
            chunks.append('\n'.join(current_chunk))
            current_chunk = [line]
            current_word_count = words_in_line
        else:
            if current_word_count + words_in_line > max_words and current_chunk:
                # Max words exceeded, yield the chunk
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_word_count = words_in_line
            else:
                current_chunk.append(line)
                current_word_count += words_in_line
                
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
        
    return [c.strip() for c in chunks if c.strip()]

def index_documents():
    conn = init_db(DB_PATH)
    cursor = conn.cursor()
    faiss_index = load_or_create_faiss_index()
    
    docs_dir_path = Path(DOCS_DIR)
    if not docs_dir_path.exists():
        os.makedirs(docs_dir_path, exist_ok=True)
        print(f"Directory {DOCS_DIR} created. Please populate.")
        return

    html_files = list(docs_dir_path.rglob("*.html"))
    total_files = len(html_files)
    print(f"Found {total_files} HTML files to analyse in {DOCS_DIR}.")

    next_faiss_id = get_next_faiss_id(conn)
    processed = 0
    updated = 0
    
    for file_path in html_files:
        try:
            rel_path = file_path.relative_to(docs_dir_path).as_posix()
            stat = file_path.stat()
            last_modified = stat.st_mtime
            
            # Check if file needs updating
            cursor.execute("SELECT id, last_modified, content_hash FROM documents WHERE file_path = ?", (rel_path,))
            row = cursor.fetchone()
            
            needs_update = False
            doc_id = None
            
            if not row:
                needs_update = True
            else:
                doc_id, db_mtime, db_hash = row
                if last_modified > db_mtime:
                    # File modified recently, check hash to be sure
                    current_hash = get_file_hash(str(file_path))
                    if current_hash != db_hash:
                        needs_update = True
                        
            if not needs_update:
                processed += 1
                continue
                
            # Read and process the new/updated file
            current_hash = get_file_hash(str(file_path))
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
                
            markdown_content = parse_html_to_markdown(html_content)
            if not markdown_content:
                continue
                
            chunks = semantic_chunk_markdown(markdown_content, max_words=CHUNK_SIZE)
            if not chunks:
                continue
                
            # Handle existing chunk deletion for updates
            if doc_id is not None:
                cursor.execute("SELECT faiss_id FROM chunks WHERE document_id = ?", (doc_id,))
                old_faiss_ids = [r[0] for r in cursor.fetchall()]
                
                # Remove old vectors from FAISS
                if old_faiss_ids:
                    faiss_index.remove_ids(np.array(old_faiss_ids, dtype=np.int64))
                    
                # Delete old chunks from SQLite
                cursor.execute("DELETE FROM chunks WHERE document_id = ?", (doc_id,))
                
                # Update document meta
                cursor.execute("UPDATE documents SET last_modified = ?, content_hash = ? WHERE id = ?", (last_modified, current_hash, doc_id))
            else:
                # Insert new document
                cursor.execute("INSERT INTO documents (file_path, last_modified, content_hash) VALUES (?, ?, ?)", (rel_path, last_modified, current_hash))
                doc_id = cursor.lastrowid
                
            # Generate and add new embeddings
            embeddings = model.encode(chunks)
            
            num_chunks = len(chunks)
            faiss_ids = np.arange(next_faiss_id, next_faiss_id + num_chunks, dtype=np.int64)
            
            faiss_index.add_with_ids(embeddings, faiss_ids)
            
            for chunk_idx, (chunk, fid) in enumerate(zip(chunks, faiss_ids)):
                cursor.execute(
                    "INSERT INTO chunks (document_id, chunk_index, markdown_content, faiss_id) VALUES (?, ?, ?, ?)",
                    (doc_id, chunk_idx, chunk, int(fid))
                )
                
            next_faiss_id += num_chunks
            updated += 1
            processed += 1
            
            if processed % 50 == 0:
                print(f"Processed {processed}/{total_files} files (Updated: {updated})...")
                conn.commit() # Periodic commit
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            
    increment_faiss_id(conn, next_faiss_id, 0) # Save the final ID counter
    conn.commit()
    conn.close()
    
    save_faiss_index(faiss_index)
    print(f"Indexing complete. Processed {processed} files. Updated/Added {updated}. Total FAISS entries: {faiss_index.ntotal}")

if __name__ == "__main__":
    index_documents()
