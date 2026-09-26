"""Baseline Exact and Cosine Vector Cache for fast-path troubleshooting retrieval."""
import hashlib
import math
import re
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from cache.store import CacheStore
from schema import Goal


def normalize_query(query: str) -> str:
    """Normalize query text for hash and similarity matching."""
    text = query.strip().lower()
    # Remove leading numbering like "1. ", "2) "
    text = re.sub(r'^\d+[\.\)]\s*', '', text)
    # Normalize punctuation and collapse whitespace
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def compute_query_hash(normalized_query: str) -> str:
    """Compute deterministic SHA-256 hash for exact-match lookup."""
    return hashlib.sha256(normalized_query.encode("utf-8")).hexdigest()


def default_lightweight_embed(text: str, dim: int = 128) -> List[float]:
    """
    Fast, deterministic CPU embedding using hashed character 3-grams and word tokens.
    Operates in <2ms on CPU without large external weight dependencies.
    """
    norm = normalize_query(text)
    words = norm.split()
    features = [0.0] * dim

    # Word unigrams
    for w in words:
        idx = int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16) % dim
        features[idx] += 2.0

    # Character 3-grams
    padded = f"_{norm}_"
    for i in range(len(padded) - 2):
        trigram = padded[i:i + 3]
        idx = int(hashlib.md5(trigram.encode("utf-8")).hexdigest(), 16) % dim
        features[idx] += 1.0

    # L2 normalize
    norm_sq = sum(x * x for x in features)
    if norm_sq > 0:
        inv_norm = 1.0 / math.sqrt(norm_sq)
        features = [x * inv_norm for x in features]

    return features


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two unit-normalized vectors."""
    if len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    return float(dot)


@dataclass
class CacheResult:
    """Container for cache lookup outcomes."""
    hit: bool
    hit_type: Optional[str]  # "exact", "semantic", None
    goal: Optional[Goal]
    similarity: float
    latency_ms: float
    query_hash: Optional[str] = None


class SemanticCache:
    """Two-tier semantic cache: Level 1 (Exact Hash, 0ms) + Level 2 (Cosine Vector, <150ms)."""

    def __init__(
        self,
        store: Optional[CacheStore] = None,
        similarity_threshold: float = 0.85,
        embed_fn: Optional[Callable[[str], List[float]]] = None,
    ):
        self.store = store or CacheStore()
        self.similarity_threshold = similarity_threshold
        self.embed_fn = embed_fn or default_lightweight_embed

    def get(self, query: str) -> CacheResult:
        """
        Query the two-tier cache.
        Level 1: Exact Hash match.
        Level 2: Cosine similarity vector search over cached embeddings.
        """
        start_time = time.perf_counter()
        normalized = normalize_query(query)
        q_hash = compute_query_hash(normalized)

        # Tier 1: Exact Hash Match
        exact_entry = self.store.get_by_hash(q_hash)
        if exact_entry:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            try:
                goal = Goal.model_validate(exact_entry["goal_payload"])
                return CacheResult(
                    hit=True,
                    hit_type="exact",
                    goal=goal,
                    similarity=1.0,
                    latency_ms=latency_ms,
                    query_hash=q_hash,
                )
            except Exception:
                pass

        # Tier 2: Vector Cosine Similarity
        query_vec = self.embed_fn(query)
        cached_entries = self.store.get_all_embeddings()

        best_sim = 0.0
        best_goal_data = None
        best_hash = None

        for item_hash, item_vec, item_goal, *rest in cached_entries:
            sim = cosine_similarity(query_vec, item_vec)
            if sim > best_sim:
                best_sim = sim
                best_goal_data = item_goal
                best_hash = item_hash

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        if best_sim >= self.similarity_threshold and best_goal_data is not None:
            try:
                goal = Goal.model_validate(best_goal_data)
                return CacheResult(
                    hit=True,
                    hit_type="semantic",
                    goal=goal,
                    similarity=best_sim,
                    latency_ms=latency_ms,
                    query_hash=best_hash,
                )
            except Exception:
                pass

        return CacheResult(
            hit=False,
            hit_type=None,
            goal=None,
            similarity=best_sim,
            latency_ms=latency_ms,
            query_hash=None,
        )

    def put(
        self,
        query: str,
        goal: Goal,
        signature: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Insert a goal into the cache with its computed embedding and hash."""
        normalized = normalize_query(query)
        q_hash = compute_query_hash(normalized)
        embedding = self.embed_fn(query)

        self.store.save(
            query_hash=q_hash,
            raw_query=query,
            normalized_query=normalized,
            goal_payload=goal.model_dump(),
            embedding=embedding,
            signature=signature,
        )
        return q_hash

    def count(self) -> int:
        return self.store.count()

    def clear(self) -> None:
        self.store.clear()
