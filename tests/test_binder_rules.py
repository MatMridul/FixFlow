"""Binder rules from the hackathon FAQ (Q5/Q7/Q15) plus the absolute
relevance gate and the real-SIIS-phrasing breadcrumb cases."""
from __future__ import annotations

import pytest

from catalog.loader import load_catalog
from resolution.binder import DUMMY_POSITIVE_URI, bind_actionable_deeplink, resolve_goal_deeplinks_with_stats
from resolution.retriever import HybridRetriever
from resolution.screen_graph import resolve_screen, split_steps
from schema import Action, Goal, StepGroup, actionCategory


@pytest.fixture(scope="module")
def catalog():
    return load_catalog()


@pytest.fixture(scope="module")
def retriever(catalog):
    return HybridRetriever(catalog)


def test_nonsense_never_gets_a_real_catalog_link(catalog, retriever):
    """Regression: normalized scores made "Bake a chocolate cake" bind
    "Enable Slow Keys" at 0.80. The raw-cosine gate rejects it; as an auto
    action it falls back to dummy_positive (FAQ Q15), never a real screen."""
    res = bind_actionable_deeplink(["Bake a chocolate cake at 180 degrees."], "auto", catalog, retriever)
    assert res.status == "dummy_positive"
    assert res.actionable_deeplink["deeplink"] == DUMMY_POSITIVE_URI


def test_dummy_positive_text_is_5_to_7_words(catalog, retriever):
    res = bind_actionable_deeplink(["Bake a chocolate cake at 180 degrees."], "auto", catalog, retriever, action_name="Bake Cake")
    for field in ("description", "message"):
        assert 5 <= len(res.actionable_deeplink[field].split()) <= 7


def test_critical_via_hardware_buttons_gets_no_link(catalog, retriever):
    steps = ["Press and hold the Power and Volume down buttons for 20 seconds."]
    res = bind_actionable_deeplink(steps, "critical", catalog, retriever)
    assert res.status == "critical_no_screen"
    assert res.actionable_deeplink is None


def test_critical_through_settings_gets_a_link(catalog, retriever):
    steps = ["Navigate to and open Settings.", "Tap General management.", "Tap Factory data reset."]
    res = bind_actionable_deeplink(steps, "critical", catalog, retriever)
    assert res.status == "matched"
    assert res.actionable_deeplink["deeplink"].startswith("bixby://masked/")


@pytest.mark.parametrize("steps, expected", [
    (["Go to Settings, tap Display, and then tap Navigation bar.", "Select Buttons to turn off full screen gestures."], "DL-0169"),
    (["Go to Settings, tap Display, and then tap the switch next to Touch sensitivity."], "DL-0126"),
])
def test_real_siis_phrasing_resolves(retriever, steps, expected):
    """Regression: the old parser only understood "Tap on X." steps, so the
    chained "Go to Settings, tap Display, and then tap Navigation bar."
    resolved to "Double tap space bar to add period"."""
    assert resolve_screen(retriever, steps).entry.id == expected


def test_split_steps_reads_chained_nav_clauses():
    labels, actions = split_steps(["Go to Settings, tap Display, and then tap Navigation bar."])
    assert labels == ["Display", "Navigation bar"]
    assert actions == []


def test_goal_resolution_reports_contract_2_and_merges(catalog, retriever):
    goal = Goal(
        goal="Follow these steps to perform this Display Troubleshooting",
        title="Display issue",
        score=0.0,
        actions=[
            Action(actionName="Adjust Dark Mode", description="It will adjust display settings nicely",
                   category=actionCategory.auto,
                   stepGroups=[StepGroup(steps=["Navigate to and open Settings.", "Tap on Display.",
                                                "Tap on Dark mode settings.", "Adjust the dim wallpaper value for Dark mode."])]),
            Action(actionName="Inspect Cable", description="It will rule out cable damage",
                   category=actionCategory.manual,
                   stepGroups=[StepGroup(steps=["Examine the USB connections for any corrosion."])]),
        ],
    )
    goal, stats = resolve_goal_deeplinks_with_stats(goal, catalog, retriever)
    auto = goal.actions[0]
    assert auto.stepGroups[0].actionableDeeplink is not None
    assert goal.actions[1].stepGroups[0].actionableDeeplink is None  # manual stays link-free
    assert 0.0 < stats.retrieval_margin <= 1.0
    assert 0.0 < stats.path_alignment <= 1.0
    assert stats.bound == 1


@pytest.mark.parametrize(
    "steps,name",
    [
        # LLM-style steps that cleared the raw-cosine gate but hit the wrong screen.
        (["Open Settings.", "Tap Apps.", "Select your email app.", "Tap Storage.", "Tap Clear cache."],
         "Clear Email App Cache"),  # was: Storage Share
        (["Swipe down from the top right to open Quick settings.", "Tap Smart View.",
          "Select your TV from Available devices."], "Enable Smart View"),  # was: Swipe for pop-up view
    ],
)
def test_weak_match_without_label_support_falls_back_to_dummy(catalog, retriever, steps, name):
    result = bind_actionable_deeplink(steps, "auto", catalog, retriever, action_name=name)
    assert result.status == "dummy_positive"
    assert result.actionable_deeplink["deeplink"] == DUMMY_POSITIVE_URI


def test_strong_match_still_binds(catalog, retriever):
    steps = ["Open Settings.", "Tap Display.", "Tap Navigation bar.", "Select Buttons."]
    result = bind_actionable_deeplink(steps, "auto", catalog, retriever, action_name="Change Navigation Bar")
    assert result.status == "matched"
    assert "navigation bar" in result.actionable_deeplink["description"].lower()
