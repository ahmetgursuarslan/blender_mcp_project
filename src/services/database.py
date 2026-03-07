import sqlite3
import os
import contextlib
import logging
import sqlite_vec
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Core Database Manager providing resilient SQLite connections.
    Enforces WAL mode for high concurrency and registers sqlite-vec extensions.
    """
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_dir()
        self._initialize_database()

    def _ensure_dir(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """
        Returns a hardened SQLite connection:
        - autocommit is disabled (requires explicit commit, protects against partial states)
        - timeout=10.0 (waits up to 10 seconds if database is locked by another writer)
        """
        conn = sqlite3.connect(
            self.db_path,
            timeout=10.0,
            isolation_level="DEFERRED" # Better concurrency
        )
        conn.row_factory = sqlite3.Row
        
        # Load the sqlite-vec extension into the connection
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        
        return conn

    def _initialize_database(self):
        """Sets up WAL journal mode and core meta-tables if they don't exist."""
        with contextlib.closing(self.get_connection()) as conn:
            # Enable WAL mode for concurrent reads/writes
            conn.execute("PRAGMA journal_mode=WAL;")
            # Wait up to 5 seconds when busy before raising database locked error
            conn.execute("PRAGMA busy_timeout=5000;")
            # Enable Foreign Keys
            conn.execute("PRAGMA foreign_keys = ON;")
            
            conn.commit()

    @contextlib.contextmanager
    def transaction(self):
        """
        Context manager for safe database transactions.
        Automatically rolls back on exceptions and raises them.
        """
        conn = self.get_connection()
        try:
            # SQLite BEGIN DEFERRED TRANSACTION is implicit with sqlite3 when isolation_level is set,
            # but explicit BEGIN makes the isolation obvious.
            conn.execute("BEGIN TRANSACTION")
            yield conn
            conn.commit()
        except Exception as e:
            logger.error(f"Transaction failed, rolling back. Error: {e}")
            conn.rollback()
            raise e
        finally:
            conn.close()
