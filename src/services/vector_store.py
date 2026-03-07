import logging
import contextlib
from typing import List, Dict, Any
import numpy as np
from fastembed import TextEmbedding
from sqlite_vec import serialize_float32

from services.database import DatabaseManager

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Handles Document Chunk ingestion, Embeddings generation (fastembed),
    and Vector Search (sqlite-vec) inside a unified SQLite database.
    """
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        
        # Initialize the zero-dependency ONNX CPU embedding model
        logger.info("Initializing fastembed CPU model (all-MiniLM-L6-v2)...")
        self.model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        self._init_schema()

    def _init_schema(self):
        """Creates tables for documents, chunks, and the vec0 virtual table."""
        with self.db.transaction() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    last_modified REAL NOT NULL,
                    content_hash TEXT NOT NULL
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    markdown_content TEXT NOT NULL,
                    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
                )
            ''')
            
            # 384 dimensions for all-MiniLM-L6-v2
            # vec0 requires strict type formatting. chunk_id ties directly to chunks.id
            conn.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(
                    chunk_id INTEGER PRIMARY KEY,
                    embedding float[384]
                )
            ''')

    def embed_texts(self, texts: List[str]) -> List[np.ndarray]:
        """Runs FastEmbed model efficiently to batch-create vectors."""
        # Fastembed returns a generator yielding float32 numpy arrays
        return list(self.model.embed(texts))

    def upsert_document(self, file_path: str, last_modified: float, content_hash: str, chunks: List[str]):
        """
        Safely upserts an entire document and its vectored chunks in one resilient transaction.
        If chunking/vectoring fails, the document state completely rolls back.
        """
        if not chunks:
            return

        with self.db.transaction() as conn:
            # 1. Delete existing document logic (triggers CASCADE delete on chunks)
            # The vec_chunks table does not natively support SQL triggers for CASCADE delete on virtual tables, 
            # so we must manually delete dependent virtual records first.
            
            # Find existing doc
            cursor = conn.execute("SELECT id FROM documents WHERE file_path = ?", (file_path,))
            row = cursor.fetchone()
            if row:
                doc_id = row['id']
                # Delete orphaned vectors
                conn.execute('''
                    DELETE FROM vec_chunks 
                    WHERE chunk_id IN (SELECT id FROM chunks WHERE document_id = ?)
                ''', (doc_id,))
                
                # Delete document (removes rows in 'chunks' table due to CASCADE)
                conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            
            # 2. Insert new document record
            cursor = conn.execute(
                "INSERT INTO documents (file_path, last_modified, content_hash) VALUES (?, ?, ?)",
                (file_path, last_modified, content_hash)
            )
            new_doc_id = cursor.lastrowid
            
            # 3. Generate Embeddings (this is done outside the sqlite loop for raw speed, 
            # but inside the transaction block to guarantee atomic writes)
            embeddings = self.embed_texts(chunks)
            
            # 4. Insert chunks and their corresponding vectors
            for chunk_idx, (text_content, embedding) in enumerate(zip(chunks, embeddings)):
                cursor = conn.execute(
                    "INSERT INTO chunks (document_id, chunk_index, markdown_content) VALUES (?, ?, ?)",
                    (new_doc_id, chunk_idx, text_content)
                )
                chunk_id = cursor.lastrowid
                
                # Insert into the virtual vector table formatting the float32 array
                conn.execute(
                    "INSERT INTO vec_chunks (chunk_id, embedding) VALUES (?, ?)",
                    (chunk_id, serialize_float32(embedding))
                )

    def search(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """
        Semantic search leveraging sqlite-vec's KNN matching directly in SQL!
        Returns a beautifully joined structured data object.
        """
        query_embedding = list(self.model.embed([query]))[0]
        
        with contextlib.closing(self.db.get_connection()) as conn:
            # Native vector distance computation in SQL, returning nearest K
            # We explicitly join the virtual vec table with our chunks and documents.
            cursor = conn.execute('''
                SELECT 
                    d.file_path, 
                    c.markdown_content, 
                    vec_distance_L2(v.embedding, ?) AS distance
                FROM vec_chunks v
                JOIN chunks c ON c.id = v.chunk_id
                JOIN documents d ON d.id = c.document_id
                WHERE v.embedding MATCH ? AND k = ?
                ORDER BY distance ASC
            ''', (serialize_float32(query_embedding), serialize_float32(query_embedding), top_k))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "file_path": row["file_path"],
                    "content": row["markdown_content"],
                    "distance": row["distance"]
                })
            
            return results
