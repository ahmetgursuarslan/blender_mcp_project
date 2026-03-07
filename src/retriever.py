import os
import sys
import contextlib
import sqlite3
import faiss
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "./data/blender_meta.db")
FAISS_PATH = os.getenv("FAISS_PATH", "./data/blender_vectors.index")

# Lazy loading to avoid heavy memory footprints when not specifically querying
_model = None
_index = None

@contextlib.contextmanager
def suppress_stdout_stderr():
    """A context manager that redirects stdout and stderr to devnull"""
    with open(os.devnull, "w") as fnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = fnull
        sys.stderr = fnull
        try:  
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

def get_model():
    global _model
    if _model is None:
        with suppress_stdout_stderr():
            _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def get_faiss_index():
    global _index
    if _index is None:
        if not os.path.exists(FAISS_PATH):
            raise FileNotFoundError("FAISS index not found. Run indexer first.")
        _index = faiss.read_index(FAISS_PATH)
    return _index

def reload_faiss_index():
    """Forces a reload of the FAISS index from disk, used after updates."""
    global _index
    if os.path.exists(FAISS_PATH):
        _index = faiss.read_index(FAISS_PATH)

def query_docs(query: str, top_k: int = 4) -> str:
    """
    RAG Logic: Encodes query, searches FAISS, and fetches exact chunks.
    Format is optimized for LLM reading.
    """
    try:
        model = get_model()
        index = get_faiss_index()
    except Exception as e:
        return f"Error loading search index: {e}"
        
    query_embedding = model.encode([query])
    distances, indices = index.search(query_embedding, top_k)
    
    if len(indices) == 0 or len(indices[0]) == 0:
        return "No results found for your query."
        
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
    except Exception as e:
        return f"Error connecting to metadata database: {e}"
        
    results = []
    
    for idx_dist, faiss_id in enumerate(indices[0]):
        if faiss_id == -1:
            continue
            
        # Join chunks with documents to get the file path and content
        cursor.execute('''
            SELECT d.file_path, c.markdown_content 
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE c.faiss_id = ?
        ''', (int(faiss_id),))
        
        row = cursor.fetchone()
        
        if row:
            file_path, content = row
            # Beautifully structured format for the LLM
            chunk_result = f"### Source: `{file_path}` (Match Rank: {idx_dist + 1})\n\n{content}\n"
            results.append(chunk_result)
            
    conn.close()
    
    if not results:
        return "No valid chunks found in the database despite FAISS match. This might indicate database corruption."
        
    return "\n---\n".join(results)
