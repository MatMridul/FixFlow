"""Unit tests for exact hash and cosine vector semantic cache."""
import shutil
import tempfile
import time
from pathlib import Path
import pytest

from cache import CacheStore, SemanticCache, normalize_query
from schema import Action, Goal, StepGroup, actionCategory


@pytest.fixture
def temp_cache_dir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_goal():
    return Goal(
        goal="Follow these steps to perform this Display Troubleshooting",
        title="Screen flicker",
        score=0.94,
        actions=[
            Action(
                actionName="Adjust Brightness",
                description="It will stabilize your display brightness",
                category=actionCategory.auto,
                stepGroups=[
                    StepGroup(
                        steps=["Open Settings.", "Tap on Display.", "Adjust brightness."]
                    )
                ],
            )
        ],
    )


class TestSemanticCache:
    def test_exact_hash_hit_latency_and_content(self, temp_cache_dir, sample_goal):
        db_path = str(Path(temp_cache_dir) / "test_cache.db")
        store = CacheStore(db_path=db_path)
        cache = SemanticCache(store=store)

        query = "My Samsung screen is flickering constantly"
        cache.put(query, sample_goal)

        # Level 1: Exact Hit
        result = cache.get(query)
        assert result.hit is True
        assert result.hit_type == "exact"
        assert result.similarity == 1.0
        assert result.latency_ms < 50.0  # P95 target ≤ 50ms
        assert result.goal is not None
        assert result.goal.title == "Screen flicker"

    def test_semantic_cosine_similarity_hit(self, temp_cache_dir, sample_goal):
        db_path = str(Path(temp_cache_dir) / "test_cache.db")
        store = CacheStore(db_path=db_path)
        cache = SemanticCache(store=store, similarity_threshold=0.75)

        stored_query = "Screen flickers and display blinks rapidly"
        cache.put(stored_query, sample_goal)

        # Paraphrase query
        paraphrase_query = "Screen flickers and display flashes rapidly"
        result = cache.get(paraphrase_query)

        assert result.hit is True
        assert result.hit_type in ("exact", "semantic")
        assert result.similarity >= 0.75
        assert result.latency_ms < 150.0  # P95 target ≤ 150ms
        assert result.goal is not None
        assert result.goal.title == "Screen flicker"

    def test_cache_miss_on_unrelated_query(self, temp_cache_dir, sample_goal):
        db_path = str(Path(temp_cache_dir) / "test_cache.db")
        store = CacheStore(db_path=db_path)
        cache = SemanticCache(store=store, similarity_threshold=0.85)

        cache.put("Screen flickers and display blinks", sample_goal)

        unrelated_query = "Audio speaker produces crackling noise during phone calls"
        result = cache.get(unrelated_query)

        assert result.hit is False
        assert result.goal is None

    def test_persistent_storage_across_reconnect(self, temp_cache_dir, sample_goal):
        db_path = str(Path(temp_cache_dir) / "persistent.db")

        # Session 1: Write
        store1 = CacheStore(db_path=db_path)
        cache1 = SemanticCache(store=store1)
        cache1.put("Battery drains too fast", sample_goal)
        assert cache1.count() == 1

        # Session 2: Read from new instance
        store2 = CacheStore(db_path=db_path)
        cache2 = SemanticCache(store=store2)
        assert cache2.count() == 1
        res = cache2.get("Battery drains too fast")
        assert res.hit is True
        assert res.goal is not None
        assert res.goal.title == "Screen flicker"

    def test_query_normalization(self):
        q1 = "1.   My Screen Is Flickering!!   "
        q2 = "my screen is flickering"
        assert normalize_query(q1) == normalize_query(q2)
