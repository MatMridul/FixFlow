"""Renders metrics.md in the table format specified by
FixFlow_Idea_v3.md §7.3 (extends the brief's own metrics.md §5).

Only the screen-resolution row/columns Dev B's own modules can measure are
filled in here (Screen acc., Parent-menu err.). Step accuracy, P95 latency,
and cost/query require Dev A's extraction + caching layers (P95 needs a
live API; cost needs a real LLM call) and are left as `-` with a note,
rather than guessed.
"""
from __future__ import annotations

from datetime import datetime, timezone


def generate_metrics_md(summary: dict, dev_set_size: int) -> str:
    accuracy_pct = f"{summary['screen_resolution_accuracy'] * 100:.1f}%"
    parent_menu_pct = f"{summary['parent_menu_error_rate'] * 100:.1f}%"
    manual_pct = f"{summary['manual_no_deeplink_compliance'] * 100:.1f}%"
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return f"""# System Performance Metrics & Evaluation Report

**Generated:** {generated} (eval/run_screen_eval.py)
**Scope:** resolution-only (N3 screen resolution, N4 catalog-side validation). Step accuracy, latency, and cost require the API + extraction layers, not yet built — see note at bottom.

---

## 2. Accuracy Benchmarks (resolution slice only)

Evaluated against `eval/dev_set.json` ({dev_set_size} scenarios — see that file's `_readme` for scope and provenance; this is NOT yet the brief's called-for 80-100 scenario hand-labelled set).

| Evaluation Metric | Scale / Anchor | Score |
| :--- | :--- | :--- |
| Screen resolution accuracy (exact target screen) | 0-100% | {accuracy_pct} |
| Parent-menu error rate (wrong page-vs-leaf level, not just wrong answer) | 0-100%, lower is better | {parent_menu_pct} |
| Manual-category no-deeplink compliance | 0-100% | {manual_pct} |

## 6. Known Edge Cases & System Limitations

- Dev set is resolution-only and partly self-constructed (see `eval/dev_set.json` provenance field per scenario) — accuracy here should NOT be reported as the brief's step-accuracy metric.
- Step accuracy (0-3 scale), deeplink relevance (0-2 scale), P95 latency (cache hit / cold path), cost per query, and the ablation table (baseline vs hybrid vs rules vs path-rerank) all require Dev A's extraction + API + caching layers to run end-to-end. Not measurable from resolution/ alone.
- Real N3 failure modes found and fixed during development (see resolution/screen_graph.py docstrings): breadcrumb-filter over-exclusion, leaf-vs-page decisions gated on word overlap instead of retrieval score, and a page-tie-break that mis-ranked unrelated low-score entries. All three are now covered by regression tests in tests/test_screen_graph.py.
"""
