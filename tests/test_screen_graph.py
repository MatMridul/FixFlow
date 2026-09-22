"""N3 tests. All three scenarios are grounded in real data, not synthetic
fixtures:
  1. The brief's own Appendix-B worked example (multi-action step group ->
     must resolve to the shared parent page, not one of the two sub-toggles
     each clause individually keyword-matches).
  2. A single specific sub-toggle on the same page (must resolve to the
     leaf control, not the parent page) — the control case proving the
     fix doesn't just collapse everything to page-level.
  3. The official sample_output.json backup scenario, as a regression
     guard: the N3 breadcrumb filter must not break the plain P0 case
     (regression caught during development — the leaf-level tie-break was
     silently undoing the retriever's own polarity fix).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from catalog.loader import load_catalog
from resolution.retriever import HybridRetriever
from resolution.screen_graph import resolve_screen, split_steps, merge_same_screen_actions

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(DATA_DIR / "deeplinks.json")


@pytest.fixture(scope="module")
def retriever(catalog):
    return HybridRetriever(catalog)


def test_split_steps_separates_navigation_from_action():
    steps = [
        "Navigate to and open Settings.",
        "Tap on Display.",
        "Tap on Navigation bar.",
        "Select your preferred navigation type between Buttons and Swipe gestures.",
    ]
    nav, action = split_steps(steps)
    assert nav == ["Display", "Navigation bar"]  # "Settings" is filtered as a generic root
    assert action == ["Select your preferred navigation type between Buttons and Swipe gestures."]


def test_multi_action_resolves_to_parent_page_not_a_sub_toggle(retriever):
    """The parent-menu failure this novelty exists to catch: two distinct
    action clauses in one step group, each of which individually
    keyword-matches a DIFFERENT specific catalog toggle. Correct answer is
    the shared page both clauses actually live on."""
    steps = [
        "Navigate to and open Settings.",
        "Tap on Display.",
        "Tap on Navigation bar.",
        "Select your preferred navigation type between Buttons and Swipe gestures.",
        "Optionally toggle on Gesture hint to display guidance lines at the bottom of the screen.",
    ]
    result = resolve_screen(retriever, steps)
    assert result.entry.id == "DL-0169"
    assert result.entry.message == "View Navigation bar"
    assert result.is_page_level is True
    assert result.parent_menu_guard_applied is True


def test_single_specific_toggle_resolves_to_leaf_not_the_page(retriever):
    """Control case: exactly one specific action naming a real sub-control
    must NOT be swallowed into the parent page."""
    steps = [
        "Navigate to and open Settings.",
        "Tap on Display.",
        "Tap on Navigation bar.",
        "Enable the input method button option.",
    ]
    result = resolve_screen(retriever, steps)
    assert result.entry.id == "DL-0137"
    assert result.is_page_level is False
    assert result.parent_menu_guard_applied is False


def test_backup_scenario_regression(retriever):
    """P0 case must still resolve correctly once N3's breadcrumb filter is
    layered on top — this caught a real bug where the leaf tie-break
    silently undid the retriever's polarity fix."""
    steps = [
        "Navigate to and open Settings.",
        "Tap on Accounts and backup.",
        "Select Back up data to secure your personal files.",
    ]
    result = resolve_screen(retriever, steps)
    assert result.entry.id == "DL-0542"
    assert result.entry.message == "Enable Back up data (Samsung Cloud)"


def test_merge_same_screen_consecutive_actions():
    actions = [
        {
            "actionName": "Pick Nav Type",
            "stepGroups": [
                {"steps": ["Tap on Display."], "actionableDeeplink": {"deeplink": "bixby://masked/act/X"}}
            ],
        },
        {
            "actionName": "Toggle Gesture Hint",
            "stepGroups": [
                {"steps": ["Toggle on Gesture hint."], "actionableDeeplink": {"deeplink": "bixby://masked/act/X"}}
            ],
        },
        {
            "actionName": "Different Screen",
            "stepGroups": [
                {"steps": ["Tap on Battery."], "actionableDeeplink": {"deeplink": "bixby://masked/act/Y"}}
            ],
        },
    ]
    merged = merge_same_screen_actions(actions)
    assert len(merged) == 2
    assert len(merged[0]["stepGroups"]) == 2  # first two merged (same screen X)
    assert len(merged[1]["stepGroups"]) == 1  # third stays separate (screen Y)


def test_merge_does_not_touch_non_consecutive_same_screen():
    """Two actions on the same screen but separated by a different one
    must NOT be merged — that would scramble safe-first/critical-last
    ordering for no benefit."""
    actions = [
        {"stepGroups": [{"steps": ["a"], "actionableDeeplink": {"deeplink": "X"}}]},
        {"stepGroups": [{"steps": ["b"], "actionableDeeplink": {"deeplink": "Y"}}]},
        {"stepGroups": [{"steps": ["c"], "actionableDeeplink": {"deeplink": "X"}}]},
    ]
    merged = merge_same_screen_actions(actions)
    assert len(merged) == 3
