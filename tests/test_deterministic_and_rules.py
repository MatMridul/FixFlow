"""Deterministic extraction on real SIIS docs, query variations, URL
scrubbing, and FAQ formatting rules."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from extraction.deterministic import extract_goal_deterministic
from extraction.query_variations import generate_query_variations, merge_variations
from validation.repair import fit_description, fit_title
from validation.scrubber import contains_urls, scrub_urls

DATA = Path(__file__).resolve().parent.parent / "data"
SIIS = json.loads((DATA / "siis_responses.json").read_text())["responses"]
QUERIES = [l.strip() for l in (DATA / "input.txt").read_text().splitlines() if l.strip()]


def _goal(row: int):
    s = SIIS[row - 1]["siis_response"]
    return extract_goal_deterministic(QUERIES[row - 1], s["title"], s["content"])


def test_steps_are_imperative_not_raw_prose():
    """Regression: the old fallback emitted "I understand you're having
    trouble..." as a step."""
    for action in _goal(2).actions:
        for step in action.stepGroups[0].steps:
            assert not step.lower().startswith(("i understand", "let's", "here's", "please"))


def test_categories_follow_faq_definitions():
    cats = {a.actionName: a.category.value for a in _goal(2).actions}
    assert cats["Force a Restart"] == "critical"
    assert cats["Charge the Device"] == "manual"
    assert cats["Check for Physical Damage and Liquid Exposure"] == "manual"


def test_swipe_is_not_treated_as_wipe():
    """Regression: substring matching made "Swipe Gestures" critical."""
    cats = {a.actionName: a.category.value for a in _goal(6).actions}
    assert cats["Swipe Gestures for Multi Window"] == "auto"


def test_goal_topic_comes_from_the_users_complaint():
    g = _goal(2)
    assert g.goal == "Follow these steps to perform this Blank Screen Troubleshooting"
    assert 2 <= len(g.title.split()) <= 3


def test_every_row_yields_actions():
    for row in range(1, 21):
        assert _goal(row).actions, f"row {row} produced no actions"


@pytest.mark.parametrize("row", range(1, 21))
def test_query_variations_8_to_10_unique(row):
    v = generate_query_variations(QUERIES[row - 1], "Blank Screen")
    assert 8 <= len(v) <= 10
    assert len({x.lower() for x in v}) == len(v)
    assert all(not contains_urls(x) for x in v)


def test_merge_variations_pads_short_llm_output_and_dedupes():
    out = merge_variations(["same", "Same", "other"], "My screen is black", "Blank Screen")
    assert out[:2] == ["same", "other"]
    assert 8 <= len(out) <= 10


@pytest.mark.parametrize("text", [
    "Visit samsung.com/support for help",
    "See the guide at help.html",
    "![img](pic.png)",
    '<a href="x">link</a>',
    "go to https://example.org",
])
def test_scrubber_catches_every_faq_leak_form(text):
    assert contains_urls(text)
    assert not contains_urls(scrub_urls(text))


def test_scrubber_leaves_normal_text_alone():
    for t in ["Tap Wi-Fi.", "Open Settings, e.g. Display.", "Charge for 1.5 hours."]:
        assert not contains_urls(t)


@pytest.mark.parametrize("desc", [
    "It will facilitate secure data transfer between your devices",
    "It will help you locate the nearest Samsung service center and schedule",
    "It will fix",
    "It will clear temporary glitches by restarting",
])
def test_fit_description_forces_5_to_7_words(desc):
    fitted = fit_description(desc)
    assert fitted.startswith("It will")
    assert 5 <= len(fitted.split()) <= 7


def test_fit_title_forces_2_to_3_words():
    assert 2 <= len(fit_title("Screen display flicker issue").split()) <= 3
    assert 2 <= len(fit_title("Flicker").split()) <= 3


def test_guard_category_corrects_llm_labels():
    from extraction.deterministic import guard_category
    from schema import actionCategory as C

    assert guard_category("Charge the Device", ["Plug in the charger."], C.auto) == C.manual
    assert guard_category("Force Restart Device", ["Press and hold Power and Volume down."], C.manual) == C.critical
    # Settings-driven steps keep the LLM's auto label even with a manual-ish word.
    assert guard_category("Check Premium Care", ["Open Settings.", "Tap Warranty."], C.auto) == C.auto
