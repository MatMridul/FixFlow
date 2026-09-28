# System Performance Metrics & Evaluation Report
**Model(s):** LLM chain in priority order: gemini:gemini-2.5-flash → mistral:mistral-small-latest → mistral:ministral-8b-latest → groq:openai/gpt-oss-120b. Served this run: ministral-8b-latest ×19, openai/gpt-oss-120b ×9, fixflow-deterministic-v2 ×2
**Embeddings:** Deeplink retrieval: BM25 (rank-bm25) + TF-IDF cosine (scikit-learn); no neural embedding model. Semantic cache: 128-dim hashed word + char-trigram vectors plus an intent signature (symptom × component).
**Environment:** 10 vCPU / 16 GB RAM / Darwin 25.5.0 (arm64), Python 3.11.7. API run in-process via FastAPI TestClient.
**Generated:** 2026-09-28 19:45 UTC by `scripts/benchmark.py` (re-run it to reproduce).

---

## 1. Schema & Rule Compliance
Evaluated on `results.jsonl` (20 kit rows) plus the 10 unseen scenarios in `eval/unseen_scenarios.json`.

| Metric | Target | Measured Value |
| :--- | :--- | :--- |
| Schema-valid output lines | >= 99% | 100% (20/20 results.jsonl); 100% of live cold responses |
| Rule compliance (Goal / Title / Description syntax) | >= 95% | 100.0% (144/144 checks) |
| Absolute URL leaks | 0 | 0 |
| Deeplink catalog validity (exact URI match) | 100% | 100% (24/24; `bixby://dummy_positive` counted as valid per FAQ Q15) |
| Auto actions carrying valid actionable deeplink | >= 90% | 100% (22/22) |
| Query variations: 8-10 unique per line | 100% | 100% |
| Unseen scenarios with valid, non-empty plan (FAQ A4) | 100% | 10/10 |

---

## 2. Accuracy Benchmarks
Step accuracy is scored automatically on the 30 live cold responses (kit + unseen), as a sum of three 0-1 parts. It is a proxy for the brief's hand-scored rubric, not a replacement for it:
- **Correctness (grounding):** share of steps whose content words are ≥50% present in the SIIS text.
- **Completeness:** share of SIIS section headings whose words appear in the plan.
- **Ordering:** 1 if every critical action comes after all non-critical ones.

Deeplink relevance is scored on the 22 hand-labelled auto scenarios in `eval/dev_set.json` (2 = exact target screen, 1 = right screen but wrong level (page vs toggle), 0 = wrong).

| Evaluation Metric | Scale / Anchor | Score |
| :--- | :--- | :--- |
| Step accuracy (completeness, correctness, ordering) | 0.0 - 3.0 | 2.70 (grounding 0.96, completeness 0.74, ordering 1.00) |
| Deeplink relevance (exact target screen vs. parent menu) | 0.0 - 2.0 | 1.95 (exact screen 95.5%, parent-menu errors 4.5%) |

---

## 3. Latency Benchmarks (N >= 30 requests per path)

| Execution Path | Target (P95) | N | P50 (ms) | P95 (ms) |
| :--- | :--- | :--- | :--- | :--- |
| Cache hit - exact query match | <= 300 ms | 30 | 3.3 | 10.1 |
| Cache hit - unseen semantic paraphrase (article sent) | <= 300 ms | 81 hits of 90 | 5.4 | 16.8 |
| Cache hit - unseen semantic paraphrase (no article) | <= 300 ms | 72 hits of 90 | 3.6 | 8.4 |
| Cold query - full pipeline extraction & mapping | <= 8000 ms | 30 | 4674 | 5964 |

Exact-repeat hit rate: 100%. 4 of the 30 first calls were served by the shared-article cache (the kit reuses one article for several near-identical complaints). Their cold timings above were re-measured on a fresh cache. Cold requests are bounded by a 7.3 s LLM budget with hedged requests (the next model is raced after 2.5 s). Past the budget, the offline extractor answers, so a slow provider never breaks the 8 s target.

---

## 4. Operational Cost & Cache Efficacy

| Metric Item | Target | Measured Value |
| :--- | :--- | :--- |
| Cold query average inference cost | Tracked | $0.000281 (list price; free-tier keys were billed $0) |
| Cache hit inference cost | $0.00 | $0.00 |
| Semantic cache hit rate, paraphrase + same article | >= 80% | 90% (81/90); right plan in 74/81 hits |
| Semantic cache hit rate, paraphrase only (no article) | >= 80% | 80% (72/90); right plan in 51/72 hits |
| Cost derivation method | - | (prompt tokens + completion tokens) × list rate per model (`extraction/llm_client.py::_PRICE_PER_M`) |

Paraphrases come from `eval/paraphrases.json`: 90 paraphrases (3 per scenario) written once by Groq `openai/gpt-oss-120b` and never stored in the cache. "Right plan" means the hit returned the same plan as that scenario's own cold call. With an article attached, a paraphrase is matched through the article's fingerprint plus a compatible intent (it can never return another article's plan). Without one, it is matched against every cached plan's query and its 8-10 pre-computed `query_variations` (brief roadmap Phase 3), using hashed n-gram and synonym-aware word similarity behind the intent gate.

---

## 5. Architectural Ablation Analysis
Deeplink mapping only (extraction is held fixed), on the 22 labelled auto scenarios of `eval/dev_set.json`. The "Step Accuracy" column here is exact-screen accuracy, since only the mapping stage varies.

| Architecture Variant | Step Accuracy | Latency (P95) | Cost / Query | Key Observations |
| :--- | :--- | :--- | :--- | :--- |
| Baseline: Full LLM Deeplink Mapping | 95.5% (21/22) | 1947 ms | $0.000121 | The LLM picks from the top-40 retrieved candidates (sending all 578 entries per step is too slow for the 8 s budget). Adds a network call per action and depends on free-tier availability. |
| Variant A: Hybrid BM25 + Dense Embedding Retrieval | 95.5% (21/22) | 10 ms | $0.000000 | **Shipped.** BM25 + TF-IDF, then a breadcrumb filter, a page-vs-toggle rule, polarity twins (Enable/Disable) and a label-support check. Deterministic and runs in milliseconds. |
| Variant B: Pure Rules-Based Deeplink Mapping | 54.5% (12/22) | 8 ms | $0.000000 | BM25 top-1 with no screen-graph rules. It picks sub-toggles over pages and gets Enable/Disable twins backwards. |

---

## 5b. Novelty Ablations (team plan N2, N5)

| Component | Variant | Measured | Notes |
| :--- | :--- | :--- | :--- |
| N2 intent-signature cache gate | Cosine-only cache | false-hit rate 8% on 50 adversarial near-miss pairs; paraphrase hit 18% | `data/adversarial_near_miss.json`: polarity ("turn on" vs "turn off"), component, trigger and scope traps |
| N2 intent-signature cache gate | Gated (shipped) | false-hit rate 0%; paraphrase hit 11% | A false hit serves the wrong plan instantly. The gate trades some paraphrase recall for that safety. |
| No-article paraphrase lookup (variations index) | Blended similarity ≥ 0.60 + relaxed gate + setting-conflict check | false-hit rate 12% on the same 50 pairs | Only used when no article is sent; a miss there would return an empty plan, so recall is favoured. With an article, the stricter article path applies. |
| N5 calibrated confidence score | Evidence-based score | ECE 0.093 over 80 scenarios | `data/calibration_dev_set.json` is team-generated (`scripts/generate_calibration_dev_set.py`), so this checks the calibrator against its own labels, not real-world outcomes. |

Paraphrase hit rates in this table use each cache type on its own (put the original query, get the paraphrase), so they can differ from the end-to-end API figure in section 4.

---

## 6. Known Edge Cases & System Limitations
* **Embeddings:** retrieval uses TF-IDF as the "dense" half, not a neural embedding model. It is fast and needs no downloads, but it misses synonyms that share no words (e.g. "blue light" vs "Eye comfort shield").
* **Catalog mislabels:** some entries carry the wrong message (adaptive battery is labelled "Enable Adaptive Display"). The resolver also reads the description, but `labelled_battery_adaptive_battery_on` still resolves to the Battery page and is kept in the dev set as a known miss.
* **Missing screens:** the catalog has no Software update, Safe mode or Smart View screens. Critical actions stay unlinked (optional per FAQ Q7), and auto actions fall back to `bixby://dummy_positive` with a generated description and message.
* **Free-tier LLM availability:** during development, Gemini 3.x returned 503 "high demand" and mistral-medium/small returned 429. The chain handles this with hedging and short cooldowns, but the model that answers varies between runs. Output quality follows the serving model, and the offline extractor is the floor.
* **Shared articles:** the kit reuses one SIIS article for several complaints. A request is served from the same-article cache only when its wording is close to an earlier complaint on that article (blended similarity ≥ 0.50). Near-identical complaints ("screen completely black") share a plan; "flashes when charging" on the same article does not.
* **Paraphrases without an article** are matched against cached queries and their `query_variations`. The hit rate is lower than with an article, and about 12% of adversarial near-miss pairs pass this path (section 5b), because a miss there would return an empty plan.
* **Multi-intent complaints** ("screen flickers and battery dies") get one Goal, built around the article that was supplied. A second intent is only covered if the article covers it.
* **Step-accuracy numbers are automated proxies** (grounding, heading coverage, ordering), not the jury's hand-scored rubric. The dev sets are small (22 labelled screens, 10 unseen scenarios) and partly self-labelled, as noted in each file's `_readme`.
* **Goal regex:** we emit no trailing period, matching `sample_output.json` and the brief's worked example. The FAQ's prose shows one; our own check accepts both.
