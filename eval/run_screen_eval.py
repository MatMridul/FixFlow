"""Runs eval/dev_set.json through the real resolution pipeline
(catalog -> HybridRetriever -> bind_actionable_deeplink, i.e. N3+N4 as
actually wired together, not resolve_screen in isolation) and reports the
metrics from eval/metrics.py.

Usage: python -m eval.run_screen_eval
"""
from __future__ import annotations

import json
from pathlib import Path

from catalog.loader import load_catalog
from resolution.retriever import HybridRetriever
from resolution.binder import bind_actionable_deeplink
from eval.metrics import (
    ScenarioResult,
    screen_resolution_accuracy,
    parent_menu_error_rate,
    manual_no_deeplink_compliance,
)
from eval.report import generate_metrics_md

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEV_SET_PATH = Path(__file__).resolve().parent / "dev_set.json"
REPO_ROOT = Path(__file__).resolve().parent.parent


def _entry_id_from_deeplink_uri(catalog, uri: str | None) -> str | None:
    if uri is None:
        return None
    for entry in catalog:
        if entry.deeplink == uri:
            return entry.id
    return None


def run() -> list[ScenarioResult]:
    catalog = load_catalog(DATA_DIR / "deeplinks.json")
    retriever = HybridRetriever(catalog)
    dev_set = json.loads(DEV_SET_PATH.read_text(encoding="utf-8"))

    results = []
    for scenario in dev_set["scenarios"]:
        bind_result = bind_actionable_deeplink(
            scenario["steps"], scenario["category"], catalog, retriever
        )
        predicted_id = _entry_id_from_deeplink_uri(
            catalog,
            bind_result.actionable_deeplink["deeplink"] if bind_result.actionable_deeplink else None,
        )
        results.append(
            ScenarioResult(
                scenario_id=scenario["id"],
                category=scenario["category"],
                expected_deeplink_id=scenario["expected_deeplink_id"],
                predicted_deeplink_id=predicted_id,
                expected_is_page_level=scenario["expected_is_page_level"],
                predicted_is_page_level=bind_result.is_page_level if bind_result.actionable_deeplink else None,
            )
        )
    return results


def summarize(results: list[ScenarioResult]) -> dict:
    return {
        "screen_resolution_accuracy": screen_resolution_accuracy(results),
        "parent_menu_error_rate": parent_menu_error_rate(results),
        "manual_no_deeplink_compliance": manual_no_deeplink_compliance(results),
        "n_scenarios": len(results),
        "failures": [r.scenario_id for r in results if r.expected_deeplink_id is not None and not r.correct],
    }


if __name__ == "__main__":
    results = run()
    summary = summarize(results)
    print(json.dumps(summary, indent=2))

    dev_set = json.loads(DEV_SET_PATH.read_text(encoding="utf-8"))
    md = generate_metrics_md(summary, dev_set_size=len(dev_set["scenarios"]))
    (REPO_ROOT / "metrics.md").write_text(md, encoding="utf-8")
    print(f"\nWrote {REPO_ROOT / 'metrics.md'}")
