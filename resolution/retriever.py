"""Hybrid (BM25 + dense-ish) retrieval over the deeplink catalog.

Matching is always performed on catalog metadata (description / message /
qna_description) — never on the masked URI string itself (brief §4.2,
"Catalog Integrity"; FixFlow_Idea_v3.md finding G notes the URIs are opaque
tokens, matching on them is meaningless and forbidden).

The "dense" half here is TF-IDF cosine similarity, not a neural embedding.
This is a deliberate P0 stand-in: it needs no model download and runs in
milliseconds, which matters for the brief's P95 <= 300ms cache-hit target and
P95 <= 8s cold-path target. The interface (`HybridRetriever.search`) is
stable, so swapping in a real sentence-embedding model later (per the
FixFlow tech stack doc) is a drop-in change, not a rewrite. Benchmark before
locking either way.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from catalog.models import CatalogEntry
from catalog.loader import Catalog

_TOKEN_RE = re.compile(r"[a-z0-9]+")

_NEGATIVE_WORDS = {"disable", "turn off", "off", "stop", "remove", "deactivate"}
_POSITIVE_WORDS = {"enable", "turn on", "on", "start", "activate"}


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _polarity(text: str) -> str:
    """Crude Enable/Disable polarity signal for tie-breaking near-identical
    catalog entries (e.g. DL-0541 "Disable Back up data" vs DL-0542 "Enable
    Back up data") that BM25/TF-IDF alone cannot separate when the query
    text doesn't literally say either word.

    This is a stopgap for Dev B's own catalog-matching layer, not a
    replacement for N2 (FixFlow_TwoDev_Plan.md: Dev A owns the real
    intent-signature polarity gate at the cache layer). Troubleshooting
    steps default to "enable/fix" intent when no explicit negation appears —
    a wrong default here is a bounded, visible error (score log shows the
    tie), not a silent one.
    """
    lowered = text.lower()
    if any(w in lowered for w in _NEGATIVE_WORDS):
        return "negative"
    if any(w in lowered for w in _POSITIVE_WORDS):
        return "positive"
    return "positive"  # default: troubleshooting steps skew toward enabling a fix


def _minmax(scores: np.ndarray) -> np.ndarray:
    lo, hi = scores.min(), scores.max()
    if hi - lo < 1e-9:
        return np.zeros_like(scores)
    return (scores - lo) / (hi - lo)


@dataclass
class RetrievalResult:
    entry: CatalogEntry
    score: float
    bm25_score: float
    dense_score: float


class HybridRetriever:
    def __init__(
        self,
        catalog: Catalog,
        bm25_weight: float = 0.8,
        dense_weight: float = 0.2,
        polarity_tie_epsilon: float = 0.02,
    ):
        # Weighted 0.8/0.2 toward BM25, not 0.5/0.5: measured against the
        # official sample (test_auto_action_resolves_to_official_ground_truth),
        # the TF-IDF "dense" stand-in produces spurious n-gram collisions
        # (e.g. "personal data" in a query matching an unrelated "personal
        # data intelligence" entry) that outrank the correct exact-keyword
        # match. Lexical BM25 is more trustworthy for this catalog's short,
        # keyword-heavy descriptions. Re-tune if/when a real embedding model
        # replaces the TF-IDF stand-in.
        self.catalog = catalog
        self.bm25_weight = bm25_weight
        self.dense_weight = dense_weight
        self.polarity_tie_epsilon = polarity_tie_epsilon

        self.entries: list[CatalogEntry] = catalog.resolvable_entries()
        texts = [e.searchable_text() for e in self.entries]

        tokenized = [_tokenize(t) for t in texts]
        self._bm25 = BM25Okapi(tokenized)

        self._vectorizer = TfidfVectorizer(
            lowercase=True, stop_words="english", ngram_range=(1, 2)
        )
        self._tfidf_matrix = self._vectorizer.fit_transform(texts)

    def search(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        if not self.entries:
            return []

        bm25_scores = np.array(self._bm25.get_scores(_tokenize(query)))
        query_vec = self._vectorizer.transform([query])
        dense_scores = cosine_similarity(query_vec, self._tfidf_matrix).ravel()

        norm_bm25 = _minmax(bm25_scores)
        norm_dense = _minmax(dense_scores)
        combined = self.bm25_weight * norm_bm25 + self.dense_weight * norm_dense

        # Pull a wider pool than top_k so the polarity tie-break has
        # candidates to work with even after reordering.
        pool_size = max(top_k * 3, 10)
        pool_order = np.argsort(-combined)[:pool_size]
        results = [
            RetrievalResult(
                entry=self.entries[i],
                score=float(combined[i]),
                bm25_score=float(norm_bm25[i]),
                dense_score=float(norm_dense[i]),
            )
            for i in pool_order
        ]
        results = self._polarity_tiebreak(query, results)
        return results[:top_k]

    def _polarity_tiebreak(
        self, query: str, results: list[RetrievalResult]
    ) -> list[RetrievalResult]:
        if len(results) < 2:
            return results
        top_score = results[0].score
        tied = [r for r in results if top_score - r.score <= self.polarity_tie_epsilon]
        if len(tied) < 2:
            return results

        query_polarity = _polarity(query)
        matching = [r for r in tied if _polarity(r.entry.searchable_text()) == query_polarity]
        if not matching:
            return results

        # Promote the best polarity-matching tied candidate to the front;
        # everything else keeps its relative order.
        best_match = max(matching, key=lambda r: r.score)
        rest = [r for r in results if r is not best_match]
        return [best_match] + rest
