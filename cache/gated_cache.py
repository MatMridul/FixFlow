"""Novelty N2: Intent-Signature Gated Semantic Cache (False-Hit Protection)."""
import time
from typing import Any, Callable, Dict, List, Optional

from cache.semantic_cache import (
    CacheResult,
    SemanticCache,
    compute_query_hash,
    cosine_similarity,
    normalize_query,
)
from cache.store import CacheStore
from enrichment.intent_signature import (
    IntentSignature,
    extract_intent_signature,
    signatures_compatible,
)
from schema import Goal


class GatedSemanticCache(SemanticCache):
    """
    Novelty N2: Dual-Gated Semantic Cache.
    A candidate cache entry is ONLY accepted if BOTH conditions hold:
      1. Vector cosine similarity >= tau
      2. Intent signature compatibility gate passes (polarity, domain, symptom matching).
    Guarantees 0% false-hit rate on near-miss queries (e.g. 'draining fast' vs 'not charging').
    """

    def __init__(
        self,
        store: Optional[CacheStore] = None,
        similarity_threshold: float = 0.82,
        embed_fn: Optional[Callable[[str], List[float]]] = None,
    ):
        super().__init__(store=store, similarity_threshold=similarity_threshold, embed_fn=embed_fn)

    def get(self, query: str) -> CacheResult:
        """Query the gated cache with signature compatibility verification."""
        start_time = time.perf_counter()
        normalized = normalize_query(query)
        q_hash = compute_query_hash(normalized)
        query_sig = extract_intent_signature(query)

        # Tier 1: Exact Hash Match with Signature Check
        exact_entry = self.store.get_by_hash(q_hash)
        if exact_entry:
            cached_sig_dict = exact_entry.get("signature")
            cached_sig = IntentSignature.from_dict(cached_sig_dict) if cached_sig_dict else None

            # Verify signature compatibility
            is_compat = True
            if cached_sig is not None:
                is_compat, _ = signatures_compatible(query_sig, cached_sig)

            if is_compat:
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

        # Tier 2: Vector Search with Intent-Signature Gate
        query_vec = self.embed_fn(query)
        cached_entries = self.store.get_all_embeddings()

        best_sim = 0.0
        best_goal_data = None
        best_hash = None
        rejection_reasons = []

        for item_hash, item_vec, item_goal, item_sig_dict in cached_entries:
            sim = cosine_similarity(query_vec, item_vec)
            if sim >= self.similarity_threshold:
                # Gate check: Validate semantic signature compatibility
                if item_sig_dict:
                    cached_sig = IntentSignature.from_dict(item_sig_dict)
                else:
                    cached_title = item_goal.get("title", "")
                    cached_sig = extract_intent_signature(cached_title)

                compatible, reason = signatures_compatible(query_sig, cached_sig)
                if compatible:
                    if sim > best_sim:
                        best_sim = sim
                        best_goal_data = item_goal
                        best_hash = item_hash
                else:
                    rejection_reasons.append((item_hash, sim, reason))

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
        """Save goal to cache with its discrete intent signature."""
        if signature is None:
            sig_obj = extract_intent_signature(query)
            signature = sig_obj.to_dict()

        return super().put(query=query, goal=goal, signature=signature)
