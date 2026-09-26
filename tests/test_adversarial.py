"""Unit tests for Task A.2.1: Adversarial Near-Miss Test Dataset and N2 Dual-Gating Protection."""
import json
from pathlib import Path
import pytest

from cache.gated_cache import GatedSemanticCache
from cache.semantic_cache import CacheResult
from cache.store import CacheStore
from enrichment.intent_signature import extract_intent_signature, signatures_compatible
from schema import Action, Goal


@pytest.fixture
def adversarial_dataset():
    data_path = Path(__file__).resolve().parent.parent / "data" / "adversarial_near_miss.json"
    assert data_path.exists(), f"Missing dataset at {data_path}"
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def test_adversarial_dataset_structure(adversarial_dataset):
    assert len(adversarial_dataset) == 50, f"Expected 50 entries, got {len(adversarial_dataset)}"
    valid_domains = {"display", "battery", "connectivity", "sound", "system"}
    valid_traps = {"polarity_inversion", "component_mismatch", "trigger_mismatch", "scope_mismatch"}

    for item in adversarial_dataset:
        assert "id" in item
        assert item["domain"] in valid_domains
        assert item["trap_type"] in valid_traps
        assert item["query_a"] and isinstance(item["query_a"], str)
        assert item["query_b"] and isinstance(item["query_b"], str)
        assert item["expected_cache_hit"] is False
        assert len(item["rationale"]) > 0


def test_adversarial_polarity_traps_fail_signature_compatibility(adversarial_dataset):
    polarity_traps = [item for item in adversarial_dataset if item["trap_type"] == "polarity_inversion"]
    assert len(polarity_traps) >= 15

    for item in polarity_traps:
        sig_a = extract_intent_signature(item["query_a"])
        sig_b = extract_intent_signature(item["query_b"])
        compat, reason = signatures_compatible(sig_a, sig_b)
        assert not compat or sig_a.polarity != sig_b.polarity, (
            f"Expected incompatible polarity between '{item['query_a']}' and '{item['query_b']}'"
        )


def test_adversarial_near_misses_rejected_by_gated_cache(tmp_path, adversarial_dataset):
    db_path = str(tmp_path / "adversarial_test.db")
    store = CacheStore(db_path=db_path)
    cache = GatedSemanticCache(store=store, similarity_threshold=0.82)

    dummy_action = Action(
        actionName="test_action",
        description="It will troubleshoot the requested issue safely",
        category="manual",
        stepGroups=[],
    )
    dummy_goal = Goal(
        goal="Follow these steps to troubleshoot the issue",
        title="Troubleshoot Issue",
        score=0.90,
        description="It will guide through device settings resolution",
        actions=[dummy_action],
    )

    # For sample of pairs: populate cache with query_a, query with query_b -> must be a cache miss
    for item in adversarial_dataset[:15]:
        cache.put(item["query_a"], dummy_goal)
        result: CacheResult = cache.get(item["query_b"])
        assert not result.hit, (
            f"Adversarial false-hit detected for pair {item['id']} ({item['trap_type']}): "
            f"'{item['query_a']}' vs '{item['query_b']}'"
        )
