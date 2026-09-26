"""Unit tests for Novelty N2: Intent-Signature Extraction and Gated Semantic Cache."""
import shutil
import tempfile
from pathlib import Path
import pytest

from cache import CacheStore, GatedSemanticCache
from enrichment import (
    IntentSignature,
    extract_intent_signature,
    signatures_compatible,
)
from schema import Action, Goal, StepGroup, actionCategory


@pytest.fixture
def temp_gated_cache():
    temp_dir = tempfile.mkdtemp()
    db_path = str(Path(temp_dir) / "gated_test_cache.db")
    store = CacheStore(db_path=db_path)
    cache = GatedSemanticCache(store=store, similarity_threshold=0.60)

    yield cache

    shutil.rmtree(temp_dir, ignore_errors=True)


class TestIntentSignatureExtraction:
    def test_extract_polarity(self):
        sig_normal = extract_intent_signature("My battery is draining rapidly")
        assert sig_normal.polarity == "normal"
        assert sig_normal.domain == "Battery"

        sig_negated = extract_intent_signature("My battery is not charging when plugged in")
        assert sig_negated.polarity == "negated"
        assert sig_negated.domain == "Battery"

        sig_wont = extract_intent_signature("Phone screen won't turn on at all")
        assert sig_wont.polarity == "negated"

    def test_extract_triggers(self):
        sig = extract_intent_signature("Screen started flickering after the software update")
        assert sig.trigger == "after_update"

        sig_drop = extract_intent_signature("Display blank after dropping device in water")
        assert sig_drop.trigger == "after_drop"

    def test_signature_compatibility_rules(self):
        sig_drain = extract_intent_signature("Battery draining fast")
        sig_not_charge = extract_intent_signature("Battery not charging")

        # Must reject: polarity mismatch and opposing symptoms
        compat, reason = signatures_compatible(sig_drain, sig_not_charge)
        assert compat is False
        assert "Polarity mismatch" in reason or "Incompatible symptoms" in reason

        # True paraphrase must accept
        sig_dying = extract_intent_signature("Phone battery dies very quickly")
        compat_para, _ = signatures_compatible(sig_drain, sig_dying)
        assert compat_para is True


class TestGatedCacheFalseHitProtection:
    def test_near_miss_query_rejected_by_gate(self, temp_gated_cache):
        # Store troubleshooting plan for battery drain
        drain_goal = Goal(
            goal="Follow these steps to perform this Battery Troubleshooting",
            title="Battery drain",
            score=0.92,
            actions=[
                Action(
                    actionName="Turn on Power Saving",
                    description="It will limit background usage to save battery",
                    category=actionCategory.auto,
                    stepGroups=[StepGroup(steps=["Open Settings.", "Turn on Power saving."])],
                )
            ],
        )

        temp_gated_cache.put("My Galaxy phone battery is draining fast", drain_goal)

        # 1. Adversarial near-miss: "not charging"
        near_miss_query = "My Galaxy phone battery is not charging"
        result_near_miss = temp_gated_cache.get(near_miss_query)

        # Vector similarity may be elevated due to lexical overlap ("My Galaxy phone battery is..."),
        # but Intent Gate MUST reject the hit!
        assert result_near_miss.hit is False, "Gated cache failed to reject near-miss query!"

        # 2. Legitimate paraphrase: "battery dying quickly"
        paraphrase_query = "My Galaxy phone battery is dying quickly"
        result_para = temp_gated_cache.get(paraphrase_query)
        assert result_para.hit is True, "Gated cache rejected a valid paraphrase!"
        assert result_para.goal is not None
        assert result_para.goal.title == "Battery drain"
