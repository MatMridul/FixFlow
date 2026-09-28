"""SIIS Knowledge Base Auto-Retriever for arbitrary user queries.

Indexes the Samsung internal knowledge store (SIIS responses) with BM25 + TF-IDF
hybrid scoring. When a user enters any custom or arbitrary device complaint
without manually providing a reference SIIS article, this retriever automatically
identifies and attaches the most relevant technical troubleshooting article so
FixFlow can run cold-path extraction and resolution.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import numpy as np
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> List[str]:
    return _TOKEN_RE.findall(text.lower())


@dataclass
class SIISArticleMatch:
    id: str
    title: str
    content: str
    score: float
    bm25_score: float
    cosine_score: float
    method: str = "hybrid-bm25-tfidf"


class SIISRetriever:
    """Hybrid BM25 + TF-IDF retriever over Samsung SIIS troubleshooting articles."""

    def __init__(
        self,
        articles: List[dict],
        bm25_weight: float = 0.5,
        tfidf_weight: float = 0.5,
        min_cosine_threshold: float = 0.08,
        min_hybrid_threshold: float = 0.15,
    ):
        self.articles = articles
        self.bm25_weight = bm25_weight
        self.tfidf_weight = tfidf_weight
        self.min_cosine_threshold = min_cosine_threshold
        self.min_hybrid_threshold = min_hybrid_threshold

        self._corpus_texts = []
        self._tokenized_corpus = []

        for art in self.articles:
            title = art.get("title", "")
            orig_q = art.get("original_query", "")
            content = art.get("content", "")
            combined = f"{title} {orig_q} {content}".strip()
            self._corpus_texts.append(combined)
            self._tokenized_corpus.append(_tokenize(combined))

        if self._tokenized_corpus:
            self._bm25 = BM25Okapi(self._tokenized_corpus)
            self._vectorizer = TfidfVectorizer(stop_words="english")
            self._tfidf_matrix = self._vectorizer.fit_transform(self._corpus_texts)
        else:
            self._bm25 = None
            self._vectorizer = None
            self._tfidf_matrix = None

    @classmethod
    def from_file(cls, path: str | Path) -> "SIISRetriever":
        file_path = Path(path)
        if not file_path.is_file():
            logger.warning(f"SIIS data file not found at {file_path}")
            return cls(articles=[])

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        articles = []
        for r in data.get("responses", []):
            siis = r.get("siis_response", {})
            articles.append({
                "id": r.get("id", ""),
                "original_query": r.get("original_query", ""),
                "title": siis.get("title", ""),
                "content": siis.get("content", ""),
            })

        return cls(articles=articles)

    @classmethod
    def default(cls) -> "SIISRetriever":
        default_path = Path(__file__).resolve().parent.parent / "data" / "siis_responses.json"
        return cls.from_file(default_path)

    def retrieve(self, query: str) -> Optional[SIISArticleMatch]:
        """Find the most relevant SIIS article for a query.

        Returns None if no articles are indexed or if the highest score
        falls below the minimum relevance threshold (out-of-domain queries).
        """
        if not self.articles or self._bm25 is None or self._vectorizer is None:
            return None

        clean_query = query.strip()
        if not clean_query:
            return None

        tokens = _tokenize(clean_query)
        if not tokens:
            return None

        # 1. BM25 score
        bm25_scores = self._bm25.get_scores(tokens)
        max_bm25 = bm25_scores.max() if len(bm25_scores) > 0 else 0.0
        bm25_norm = bm25_scores / (max_bm25 + 1e-9) if max_bm25 > 0 else bm25_scores

        # 2. TF-IDF Cosine similarity
        q_vec = self._vectorizer.transform([clean_query])
        cosine_scores = cosine_similarity(q_vec, self._tfidf_matrix)[0]

        # 3. Hybrid fusion
        hybrid_scores = (self.bm25_weight * bm25_norm) + (self.tfidf_weight * cosine_scores)
        best_idx = int(np.argmax(hybrid_scores))

        best_cosine = float(cosine_scores[best_idx])
        best_hybrid = float(hybrid_scores[best_idx])
        best_bm25 = float(bm25_scores[best_idx])

        # Relevance gating: must show meaningful lexical or semantic alignment
        if best_cosine < self.min_cosine_threshold or best_bm25 <= 0.0:
            logger.info(
                f"Query '{clean_query[:50]}' did not meet SIIS retrieval threshold "
                f"(cosine={best_cosine:.3f} < {self.min_cosine_threshold}, bm25={best_bm25:.3f})"
            )
            return None

        chosen = self.articles[best_idx]
        return SIISArticleMatch(
            id=chosen["id"],
            title=chosen["title"],
            content=chosen["content"],
            score=round(best_hybrid, 4),
            bm25_score=round(best_bm25, 4),
            cosine_score=round(best_cosine, 4),
        )
