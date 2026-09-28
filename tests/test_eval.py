from __future__ import annotations

from eval.metrics import (
    ScenarioResult,
    screen_resolution_accuracy,
    parent_menu_error_rate,
    manual_no_deeplink_compliance,
)
from eval.run_screen_eval import run, summarize
from eval.report import generate_metrics_md


def test_parent_menu_error_distinguishes_wrong_level_from_wrong_leaf():
    """A wrong answer that's still leaf-vs-leaf (picked the wrong toggle on
    the right page) should NOT count as a parent-menu error — only a wrong
    answer that also got the page-vs-leaf level wrong should."""
    wrong_but_same_level = ScenarioResult(
        "s1", "auto", "DL-A", "DL-B", expected_is_page_level=False, predicted_is_page_level=False
    )
    wrong_and_wrong_level = ScenarioResult(
        "s2", "auto", "DL-A", "DL-B", expected_is_page_level=False, predicted_is_page_level=True
    )
    correct = ScenarioResult(
        "s3", "auto", "DL-A", "DL-A", expected_is_page_level=False, predicted_is_page_level=False
    )

    assert wrong_but_same_level.is_parent_menu_error is False
    assert wrong_and_wrong_level.is_parent_menu_error is True
    assert correct.is_parent_menu_error is False

    results = [wrong_but_same_level, wrong_and_wrong_level, correct]
    assert screen_resolution_accuracy(results) == 1 / 3
    assert parent_menu_error_rate(results) == 1 / 3


def test_manual_compliance_ignores_non_manual_scenarios():
    results = [
        ScenarioResult("s1", "manual", None, None, None, None),
        ScenarioResult("s2", "manual", None, "bixby://x", None, False),  # should have been None
        ScenarioResult("s3", "auto", "DL-A", "DL-A", False, False),
    ]
    assert manual_no_deeplink_compliance(results) == 0.5


def test_full_harness_runs_and_scores_own_dev_set():
    """Integration check: the harness wires catalog -> retriever -> binder
    correctly end to end. 100% here reflects that the dev set was built by
    verifying against this same pipeline (see dev_set.json's _readme) - it
    proves the harness works, not that resolution is bug-free on unseen
    data."""
    results = run()
    summary = summarize(results)
    assert summary["n_scenarios"] >= 23  # 7 original + 16 hand-labelled (2026-09-29)
    assert summary["screen_resolution_accuracy"] >= 0.9
    # Known miss, kept in the set on purpose: the catalog mislabels adaptive
    # battery as "Enable Adaptive Display" and the Battery page outranks it.
    assert set(summary["failures"]) <= {"labelled_battery_adaptive_battery_on"}


def test_metrics_md_renders_without_error():
    summary = {
        "screen_resolution_accuracy": 0.857,
        "parent_menu_error_rate": 0.0,
        "manual_no_deeplink_compliance": 1.0,
    }
    md = generate_metrics_md(summary, dev_set_size=7)
    assert "85.7%" in md
    assert "0.0%" in md
    assert "resolution-only" in md
