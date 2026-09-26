"""Tests for Novelty N5: Step-to-SIIS Provenance Bipartite Filter and Calibrated Scorer."""
import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from extraction.provenance import compute_sentence_overlap, filter_provenance, split_into_sentences
from schema import Action, Goal, StepGroup, actionCategory
from validation.calibrator import calibrate_score


def test_split_into_sentences():
    text = "First troubleshooting step. Make sure display is clean! Did you check adaptive brightness?"
    sentences = split_into_sentences(text)
    assert len(sentences) == 3
    assert "First troubleshooting step." in sentences
    assert "Make sure display is clean!" in sentences
    assert "Did you check adaptive brightness?" in sentences


def test_compute_sentence_overlap_high_and_low():
    siis_sentences = [
        "To fix display flickering, open Settings and tap on Display.",
        "Adjust the screen refresh rate to standard 60Hz mode."
    ]

    # Highly relevant step
    score_high, matched = compute_sentence_overlap("Tap on Display in Settings", siis_sentences)
    assert score_high >= 0.50
    assert matched == siis_sentences[0]

    # Completely unrelated hallucinated step
    score_low, _ = compute_sentence_overlap("Perform a hard factory reset on the device", siis_sentences)
    assert score_low < 0.15


def test_filter_provenance_prunes_hallucinations():
    siis_text = "To resolve flickering, navigate to Display settings and toggle off Adaptive Brightness."

    grounded_action = Action(
        actionName="Toggle Adaptive Brightness",
        description="It will stabilize your screen brightness",
        category=actionCategory.auto,
        stepGroups=[
            StepGroup(
                steps=[
                    "Open Settings.",
                    "Tap on Display.",
                    "Toggle off Adaptive Brightness."
                ]
            )
        ]
    )

    hallucinated_action = Action(
        actionName="Factory Reset Device",
        description="It will completely erase all user data",
        category=actionCategory.critical,
        stepGroups=[
            StepGroup(
                steps=[
                    "Format internal storage partition.",
                    "Execute factory firmware wipe."
                ]
            )
        ]
    )

    goal = Goal(
        goal="Follow these steps to perform this Display Troubleshooting",
        title="Screen flicker",
        score=0.9,
        actions=[grounded_action, hallucinated_action]
    )

    filtered_goal, coverage, prov_map = filter_provenance(goal, siis_text, threshold=0.15)

    # Hallucinated action should be completely pruned
    assert len(filtered_goal.actions) == 1
    assert filtered_goal.actions[0].actionName == "Toggle Adaptive Brightness"
    # Grounded steps in Display action should be retained
    assert len(filtered_goal.actions[0].stepGroups[0].steps) >= 2
    # Coverage should be between 0.3 and 0.8 (since factory reset steps were rejected)
    assert 0.3 <= coverage <= 0.8
    assert len(prov_map) == 5  # 3 grounded + 2 hallucinated checked


def test_calibrate_score_deterministic_formula():
    # Perfect alignment
    score_perfect = calibrate_score(grounding_coverage=1.0, validator_pass_rate=1.0, retrieval_margin=1.0, path_alignment=1.0)
    assert score_perfect == 1.0

    # Total failure
    score_zero = calibrate_score(grounding_coverage=0.0, validator_pass_rate=0.0, retrieval_margin=0.0, path_alignment=0.0)
    assert score_zero == 0.0

    # Weighted calculation: 0.40 * 0.8 + 0.30 * 1.0 + 0.15 * 0.9 + 0.15 * 0.7 = 0.32 + 0.30 + 0.135 + 0.105 = 0.86
    score_mixed = calibrate_score(
        grounding_coverage=0.8,
        validator_pass_rate=1.0,
        retrieval_margin=0.9,
        path_alignment=0.7
    )
    assert score_mixed == 0.86


def test_api_e2e_cold_path_provenance_and_calibration(tmp_path):
    from cache import CacheStore, GatedSemanticCache
    test_db = str(tmp_path / "test_prov_cache.db")
    isolated_cache = GatedSemanticCache(store=CacheStore(db_path=test_db))
    app = create_app(cache=isolated_cache)
    client = TestClient(app)

    payload = {
        "query": "My screen flickers when playing games",
        "siis_response": {
            "title": "Screen Flickering and Display Refresh Rate Troubleshooting",
            "content": "To fix screen flickering, open Settings, tap Display, and change Motion Smoothness to Standard."
        }
    }

    res = client.post("/v1/troubleshoot", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["meta"]["cache_hit"] is False
    assert len(data["response"]["contexts"]) == 1

    goal = data["response"]["contexts"][0]
    # Calibrated score should be empirical and strictly positive
    assert 0.40 <= goal["score"] <= 1.0
    assert len(goal["actions"]) >= 1
