import sqlite3
import hashlib
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

class HashCache:
    """
    Incremental hash cache using SQLite.
    Stores file metadata to avoid re-hashing unchanged files.
    """
    def __init__(self, db_path: str = "scripts/lib/hash_cache.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS file_cache (
                    path TEXT PRIMARY KEY,
                    size INTEGER,
                    mtime REAL,
                    hash TEXT,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_path ON file_cache(path)")

    def get_hash(self, file_path: Path) -> Tuple[str, bool]:
        """
        Get hash for file, either from cache or by computing it.
        Returns (hash, from_cache).
        """
        stat = file_path.stat()
        size = stat.st_size
        mtime = stat.st_mtime
        path_str = str(file_path.absolute())

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT hash FROM file_cache WHERE path = ? AND size = ? AND mtime = ?",
                (path_str, size, mtime)
            )
            row = cursor.fetchone()
            if row:
                return row[0], True

        # Not in cache or changed, compute it
        file_hash = self._compute_hash(file_path)
        self._update_cache(path_str, size, mtime, file_hash)
        return file_hash, False

    def _compute_hash(self, file_path: Path) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _update_cache(self, path: str, size: int, mtime: float, file_hash: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO file_cache (path, size, mtime, hash, last_seen)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (path, size, mtime, file_hash)
            )

if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python hash_cache.py <file_path>")
        sys.exit(1)
        
    target = Path(sys.argv[1])
    if not target.exists():
        print(f"Error: {target} not found")
        sys.exit(1)
        
    cache = HashCache()
    h, cached = cache.get_hash(target)
    print(json.dumps({"hash": h, "cached": cached}))
