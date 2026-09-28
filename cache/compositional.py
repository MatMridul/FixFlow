"""Novelty N1: Compositional Multi-Intent Cache and Goal Combiner."""
import hashlib
import re
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from cache.gated_cache import GatedSemanticCache
from cache.store import CacheStore
from enrichment.clause_splitter import decompose_query_intents
from cache import lexical
from cache.semantic_cache import cosine_similarity
from enrichment.intent_signature import IntentSignature, extract_intent_signature, signatures_compatible
from schema import Action, Goal, actionCategory


_ENABLE_RE = re.compile(r"\b(turn(ing)? on|switch(ing)? on|enable|enabling|activate)\b", re.I)
_DISABLE_RE = re.compile(r"\b(turn(ing)? off|switch(ing)? off|disable|disabling|deactivate)\b", re.I)


def _command_polarity(text: str) -> Optional[str]:
    on, off = bool(_ENABLE_RE.search(text)), bool(_DISABLE_RE.search(text))
    if on == off:
        return None
    return "on" if on else "off"


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
        # SIIS-article index: fingerprint -> [(query, signature, goals)]. See get_by_article().
        self._articles: Dict[str, List[Tuple[str, IntentSignature, List[dict]]]] = {}
        self._articles_lock = threading.Lock()
        # Pre-warmed paraphrase keys (brief roadmap, Phase 3): each cold plan is
        # indexed under its query AND its 8-10 query_variations -> [(text, plan_id)].
        self._variant_keys: List[Tuple[str, int, List[float]]] = []  # (text, plan_id, hashed vec)
        self._variant_lex: List[Dict[str, float]] = []
        self._variant_plans: List[List[dict]] = []
        self._variant_idf: Optional[Dict[str, float]] = None

    # Lowest blended similarity at which a same-article request counts as a
    # paraphrase. The kit reuses one article for different complaints (six
    # rows share "Blank or black display"): those pairs score <= 0.49 except
    # two near-identical "screen completely black" complaints (0.63), while
    # true paraphrases (eval/paraphrases.json) score >= 0.50.
    ARTICLE_MIN_SIMILARITY = 0.50

    @staticmethod
    def article_fingerprint(title: str, content: str) -> str:
        text = re.sub(r"\s+", " ", f"{title}\n{content}".strip().lower())
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    # Blended similarity a no-article paraphrase needs against some indexed key.
    # eval/paraphrases.json sweep with offline (template) variations: 0.60 -> 60% hit,
    # 49/54 hits the right plan; LLM-written variations lift recall further.
    VARIANT_MIN_SIMILARITY = 0.60

    def put_article(self, fingerprint: str, query: str, goals: List[Goal],
                    variations: Optional[List[str]] = None) -> None:
        payload = [g.model_dump() for g in goals]
        entry = (query, extract_intent_signature(query), payload)
        with self._articles_lock:
            self._articles.setdefault(fingerprint, []).append(entry)
            plan_id = len(self._variant_plans)
            self._variant_plans.append(payload)
            for text in [query] + [v for v in (variations or []) if isinstance(v, str)]:
                self._variant_keys.append((text, plan_id, self.embed_fn(text)))
            self._variant_idf = None  # IDF + word vectors recomputed lazily on next lookup

    def _current_idf(self) -> Dict[str, float]:
        with self._articles_lock:
            if self._variant_idf is None:
                by_plan: Dict[int, List[str]] = {}
                for text, plan_id, _ in self._variant_keys:
                    by_plan.setdefault(plan_id, []).append(text)
                self._variant_idf = lexical.idf_table(by_plan.values())
                self._variant_lex = [lexical.vector(k[0], self._variant_idf) for k in self._variant_keys]
            return self._variant_idf

    def _blended_similarity(self, a: str, b: str) -> float:
        """Hashed n-gram cosine and synonym-aware IDF word cosine, averaged."""
        idf = self._current_idf()
        return 0.5 * cosine_similarity(self.embed_fn(a), self.embed_fn(b)) + 0.5 * lexical.cosine(
            lexical.vector(a, idf), lexical.vector(b, idf))

    def get_by_variants(self, query: str) -> CompositionalCacheResult:
        """No-article paraphrase lookup over each plan's query + variations.

        Similarity blends the hashed n-gram embedding with synonym-aware IDF
        word overlap (cache/lexical.py). Candidates must pass the intent gate
        (minus its "negated complaint" rule, which splits "won't turn on" from
        "went black"), must not flip an on/off command, and must not name a
        different Settings feature ("timeout" vs "brightness").
        """
        start = time.perf_counter()
        idf = self._current_idf()
        with self._articles_lock:
            keys = list(self._variant_keys)
            plans = list(self._variant_plans)
            lex_vecs = list(self._variant_lex)
        query_vec = self.embed_fn(query)
        query_lex = lexical.vector(query, idf)
        query_sig = extract_intent_signature(query)
        query_pol = _command_polarity(query)
        best_plan, best_sim = None, 0.0
        for (text, plan_id, text_vec), text_lex in zip(keys, lex_vecs):
            sim = 0.5 * cosine_similarity(query_vec, text_vec) + 0.5 * lexical.cosine(query_lex, text_lex)
            if sim < self.VARIANT_MIN_SIMILARITY or sim <= best_sim:
                continue
            text_pol = _command_polarity(text)
            if query_pol and text_pol and query_pol != text_pol:
                continue
            compatible, why = signatures_compatible(query_sig, extract_intent_signature(text))
            if not (compatible or why.startswith("Polarity mismatch")):
                continue
            if lexical.setting_conflict(query, text):
                continue
            best_plan, best_sim = plan_id, sim
        latency_ms = (time.perf_counter() - start) * 1000.0
        if best_plan is None:
            return CompositionalCacheResult(hit=False, hit_type=None, goals=[], missing_clauses=[],
                                            latency_ms=round(latency_ms, 2))
        return CompositionalCacheResult(hit=True, hit_type="variant",
                                        goals=[Goal.model_validate(g) for g in plans[best_plan]],
                                        missing_clauses=[], latency_ms=round(latency_ms, 2))

    def get_by_article(self, query: str, fingerprint: str) -> CompositionalCacheResult:
        """Paraphrase hit keyed on the knowledge article, not just the wording.

        The hashed n-gram embedding only reaches 0.82 similarity for ~1 in 9
        real paraphrases (measured on eval/paraphrases.json), and lowering the
        threshold instead makes paraphrases of one "black screen" complaint
        hit another scenario's plan. When the caller sends the same SIIS
        article, the scenario is already pinned down: a compatible intent
        signature plus loose wording overlap is enough, and it can never
        serve a plan built from a different article.
        """
        start = time.perf_counter()
        with self._articles_lock:
            entries = list(self._articles.get(fingerprint, []))
        query_polarity = _command_polarity(query)
        best, best_sim = None, 0.0
        for cached_query, cached_sig, goals in entries:
            # The full signature gate is too strict here: it reads "won't turn
            # on" as negated and "went black" as normal, which rejected 36 of
            # 90 true paraphrases. The article already pins the scenario, so
            # only an explicit on/off command conflict ("turn on Dark mode" vs
            # "turn off Dark mode") marks a different question.
            cached_polarity = _command_polarity(cached_query)
            if query_polarity and cached_polarity and query_polarity != cached_polarity:
                continue
            sim = self._blended_similarity(query, cached_query)
            if sim >= self.ARTICLE_MIN_SIMILARITY and sim > best_sim:
                best, best_sim = goals, sim
        latency_ms = (time.perf_counter() - start) * 1000.0
        if best is None:
            return CompositionalCacheResult(hit=False, hit_type=None, goals=[], missing_clauses=[],
                                            latency_ms=round(latency_ms, 2))
        return CompositionalCacheResult(hit=True, hit_type="article", goals=[Goal.model_validate(g) for g in best],
                                        missing_clauses=[], latency_ms=round(latency_ms, 2))

    def clear(self) -> None:
        super().clear()
        with self._articles_lock:
            self._articles.clear()
            self._variant_keys.clear()
            self._variant_plans.clear()
            self._variant_lex = []
            self._variant_idf = None

    def get_compound(self, query: str) -> CompositionalCacheResult:
        """
        Evaluate single or compound queries compositionally.
        1. Fast-Path: Check if the full query hits directly in cache (exact/semantic).
        2. Compositional Path: If miss, decompose into sub-intents and evaluate per-clause hits.
        """
        start_time = time.perf_counter()

        # 1. Primary Full-Query Fast-Path Lookup
        full_res = self.get(query)
        if full_res.hit and full_res.goal is not None:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return CompositionalCacheResult(
                hit=True,
                partial_hit=False,
                hit_type=f"full_{full_res.hit_type}",
                goals=[full_res.goal],
                missing_clauses=[],
                latency_ms=round(latency_ms, 2),
            )

        # 2. Compositional Multi-Intent Lookup
        decomposed = decompose_query_intents(query)
        if len(decomposed) <= 1:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
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
