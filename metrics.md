# System Performance Metrics & Evaluation Report

**Generated:** 2026-09-27 06:48 UTC (eval/run_screen_eval.py)
**Scope:** resolution-only (N3 screen resolution, N4 catalog-side validation). Step accuracy, latency, and cost require the API + extraction layers, not yet built — see note at bottom.

---

## 2. Accuracy Benchmarks (resolution slice only)

Evaluated against `eval/dev_set.json` (7 scenarios — see that file's `_readme` for scope and provenance; this is NOT yet the brief's called-for 80-100 scenario hand-labelled set).

| Evaluation Metric | Scale / Anchor | Score |
| :--- | :--- | :--- |
| Screen resolution accuracy (exact target screen) | 0-100% | 100.0% |
| Parent-menu error rate (wrong page-vs-leaf level, not just wrong answer) | 0-100%, lower is better | 0.0% |
| Manual-category no-deeplink compliance | 0-100% | 100.0% |

## 6. Known Edge Cases & System Limitations

- Dev set is resolution-only and partly self-constructed (see `eval/dev_set.json` provenance field per scenario) — accuracy here should NOT be reported as the brief's step-accuracy metric.
- Step accuracy (0-3 scale), deeplink relevance (0-2 scale), P95 latency (cache hit / cold path), cost per query, and the ablation table (baseline vs hybrid vs rules vs path-rerank) all require Dev A's extraction + API + caching layers to run end-to-end. Not measurable from resolution/ alone.
- Real N3 failure modes found and fixed during development (see resolution/screen_graph.py docstrings): breadcrumb-filter over-exclusion, leaf-vs-page decisions gated on word overlap instead of retrieval score, and a page-tie-break that mis-ranked unrelated low-score entries. All three are now covered by regression tests in tests/test_screen_graph.py.
