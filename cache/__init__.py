from cache.compositional import (
    CompositionalCache,
    CompositionalCacheResult,
    deduplicate_critical_actions,
)
from cache.gated_cache import GatedSemanticCache
from cache.semantic_cache import (
    CacheResult,
    SemanticCache,
    compute_query_hash,
    cosine_similarity,
    default_lightweight_embed,
    normalize_query,
)
from cache.store import CacheStore

__all__ = [
    "CacheStore",
    "SemanticCache",
    "GatedSemanticCache",
    "CompositionalCache",
    "CompositionalCacheResult",
    "deduplicate_critical_actions",
    "CacheResult",
    "normalize_query",
    "compute_query_hash",
    "default_lightweight_embed",
    "cosine_similarity",
]


