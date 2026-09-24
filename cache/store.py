"""Persistent SQLite storage engine for FixFlow cache."""
import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class CacheStore:
    """Thread-safe SQLite persistent store for query hashes, vector embeddings, and Goal payloads."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Default to local cache file in data/
            base_dir = Path(__file__).resolve().parent.parent / "data"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(base_dir / "cache_store.db")
        else:
            self.db_path = db_path

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS semantic_cache (
                    query_hash TEXT PRIMARY KEY,
                    raw_query TEXT NOT NULL,
                    normalized_query TEXT NOT NULL,
                    embedding_json TEXT,
                    goal_payload TEXT NOT NULL,
                    signature_json TEXT,
                    hit_count INTEGER DEFAULT 0,
                    created_at REAL NOT NULL,
                    last_accessed_at REAL NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_norm ON semantic_cache(normalized_query)")

    def get_by_hash(self, query_hash: str) -> Optional[Dict[str, Any]]:
        """Exact lookup by SHA-256 hash."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT raw_query, normalized_query, embedding_json, goal_payload, hit_count FROM semantic_cache WHERE query_hash = ?",
                (query_hash,)
            )
            row = cursor.fetchone()
            if row:
                conn.execute(
                    "UPDATE semantic_cache SET hit_count = hit_count + 1, last_accessed_at = ? WHERE query_hash = ?",
                    (time.time(), query_hash)
                )
                return {
                    "raw_query": row[0],
                    "normalized_query": row[1],
                    "embedding": json.loads(row[2]) if row[2] else None,
                    "goal_payload": json.loads(row[3]),
                    "hit_count": row[4] + 1,
                }
        return None

    def get_all_embeddings(self) -> List[Tuple[str, List[float], Dict[str, Any]]]:
        """Retrieve all cached items with embeddings for vector search."""
        results = []
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT query_hash, embedding_json, goal_payload FROM semantic_cache WHERE embedding_json IS NOT NULL"
            )
            for row in cursor.fetchall():
                q_hash, emb_json, goal_json = row
                try:
                    emb = json.loads(emb_json)
                    goal = json.loads(goal_json)
                    results.append((q_hash, emb, goal))
                except Exception:
                    continue
        return results

    def save(
        self,
        query_hash: str,
        raw_query: str,
        normalized_query: str,
        goal_payload: Dict[str, Any],
        embedding: Optional[List[float]] = None,
        signature: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Insert or replace a cache entry."""
        now = time.time()
        emb_json = json.dumps(embedding) if embedding else None
        sig_json = json.dumps(signature) if signature else None
        goal_json = json.dumps(goal_payload)

        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO semantic_cache (
                    query_hash, raw_query, normalized_query, embedding_json,
                    goal_payload, signature_json, created_at, last_accessed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(query_hash) DO UPDATE SET
                    goal_payload=excluded.goal_payload,
                    embedding_json=coalesce(excluded.embedding_json, semantic_cache.embedding_json),
                    signature_json=coalesce(excluded.signature_json, semantic_cache.signature_json),
                    last_accessed_at=excluded.last_accessed_at
            """, (query_hash, raw_query, normalized_query, emb_json, goal_json, sig_json, now, now))

    def count(self) -> int:
        """Return total number of entries in the cache."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM semantic_cache")
            return cursor.fetchone()[0]

    def clear(self) -> None:
        """Clear all entries from the store."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM semantic_cache")
