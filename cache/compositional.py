"""Novelty N1: Compositional Multi-Intent Cache and Goal Combiner."""
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from cache.gated_cache import GatedSemanticCache
from cache.store import CacheStore
from enrichment.clause_splitter import decompose_query_intents
from enrichment.intent_signature import IntentSignature
from schema import Action, Goal, actionCategory


class CompositionalCacheResult(BaseModel):
    """Result object for compositional multi-intent cache queries."""
    hit: bool = Field(False, description="True if all sub-intents hit the cache")
    partial_hit: bool = Field(False, description="True if at least one, but not all, sub-intents hit")
    hit_type: Optional[str] = Field(None, description="full_compositional, partial_compositional, single_exact, single_semantic")
    goals: List[Goal] = Field(default_factory=list, description="Resolved Goal contexts")
    missing_clauses: List[Tuple[str, Any]] = Field(default_factory=list, description="Sub-intents requiring cold-path extraction")
    latency_ms: float = Field(0.0, description="Cache lookup latency in milliseconds")


def deduplicate_critical_actions(goals: List[Goal]) -> List[Goal]:
    """
    Deduplicate shared critical actions (e.g. Device Restart) across multiple Goal contexts.
    Ensures users are never instructed to perform heavy critical operations twice.
    """
    if len(goals) <= 1:
        return goals

    seen_critical_names = set()
    cleaned_goals: List[Goal] = []

    for goal in goals:
        clean_actions: List[Action] = []
        for action in goal.actions:
            # Check if action is critical and previously seen
            if action.category == actionCategory.critical:
                normalized_name = action.actionName.strip().lower()
                if normalized_name in seen_critical_names:
                    # Drop duplicate critical action
                    continue
                seen_critical_names.add(normalized_name)

            clean_actions.append(action)

        cleaned_goals.append(
            Goal(
                goal=goal.goal,
                title=goal.title,
                score=goal.score,
                actions=clean_actions,
            )
        )

    return cleaned_goals


class CompositionalCache(GatedSemanticCache):
    """
    Novelty N1: Compositional Multi-Intent Cache.
    Decomposes compound complaints into discrete sub-intents, evaluates cache
    hits independently, and composes cached Goal contexts without LLM calls.
    """

    def __init__(
        self,
        store: Optional[CacheStore] = None,
        similarity_threshold: float = 0.82,
        embed_fn: Optional[Callable[[str], List[float]]] = None,
    ):
        super().__init__(store=store, similarity_threshold=similarity_threshold, embed_fn=embed_fn)

    def get_compound(self, query: str) -> CompositionalCacheResult:
        """
        Evaluate single or compound queries compositionally.
        """
        start_time = time.perf_counter()
        decomposed = decompose_query_intents(query)

        # Single intent path: fallback directly to base gated lookup
        if len(decomposed) <= 1:
            base_res = self.get(query)
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            if base_res.hit and base_res.goal:
                return CompositionalCacheResult(
                    hit=True,
                    partial_hit=False,
                    hit_type=f"single_{base_res.hit_type}",
                    goals=[base_res.goal],
                    missing_clauses=[],
                    latency_ms=round(latency_ms, 2),
                )
            return CompositionalCacheResult(
                hit=False,
                partial_hit=False,
                hit_type=None,
                goals=[],
                missing_clauses=decomposed,
                latency_ms=round(latency_ms, 2),
            )

        # Multi-intent path: independent lookup per clause
        resolved_goals: List[Goal] = []
        missing_clauses: List[Tuple[str, Any]] = []

        for clause_text, clause_sig in decomposed:
            sub_res = self.get(clause_text)
            if sub_res.hit and sub_res.goal:
                resolved_goals.append(sub_res.goal)
            else:
                missing_clauses.append((clause_text, clause_sig.to_dict()))

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        # Full Hit: All sub-intents resolved from cache
        if len(missing_clauses) == 0 and len(resolved_goals) == len(decomposed):
            deduped_goals = deduplicate_critical_actions(resolved_goals)
            return CompositionalCacheResult(
                hit=True,
                partial_hit=False,
                hit_type="full_compositional",
                goals=deduped_goals,
                missing_clauses=[],
                latency_ms=round(latency_ms, 2),
            )

        # Partial Hit: At least one clause hit, but others missed
        if len(resolved_goals) > 0 and len(missing_clauses) > 0:
            return CompositionalCacheResult(
                hit=False,
                partial_hit=True,
                hit_type="partial_compositional",
                goals=resolved_goals,
                missing_clauses=missing_clauses,
                latency_ms=round(latency_ms, 2),
            )

        # Full Miss
        return CompositionalCacheResult(
            hit=False,
            partial_hit=False,
            hit_type=None,
            goals=[],
            missing_clauses=decomposed,
            latency_ms=round(latency_ms, 2),
        )

    def put_compound(
        self,
        query: str,
        goals: List[Goal],
    ) -> None:
        """
        Store compound resolutions both as individual sub-intents and overall query.
        Ensures future queries benefit combinatorially from extracted sub-intents.
        """
        decomposed = decompose_query_intents(query)

        # If sub-intents match the number of goals, cache each sub-intent separately
        if len(decomposed) == len(goals):
            for (clause_text, _), goal in zip(decomposed, goals):
                self.put(clause_text, goal)

        # Also cache the overall query
        if goals:
            self.put(query, goals[0])
