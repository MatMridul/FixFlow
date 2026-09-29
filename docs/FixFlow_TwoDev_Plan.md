# FixFlow — Team Implementation Plan: Hemish (Team Lead) & Mridul (Co-Developer) + Jules (CI/Test Worker)

**Samsung PRISM GenAI Hackathon · Theme 02**  
**Companion to `FixFlow_Idea_v3.md`** (the source-of-truth idea doc). This document outlines the division of work across **Hemish Jain (Team Lead & Primary Member)** and **Mridul Mathur (Core Co-Developer)**, augmented by **Google Jules (Autonomous Cloud AI)** for continuous testing, bug fixing, and CI/CD.

> **Team Leadership:** **Hemish Jain** serves as the **Team Lead & Primary Member** overseeing overall architecture, resolution systems, and hackathon submission.  
> **Core Split Principle:** FixFlow's pipeline has two halves that meet at the `Goal` contract object.  
> * **Hemish Jain (Team Lead / Dev A)** owns the **Catalog → Resolution & Evaluation** half (catalog, screen graph, retrieval, deeplink binding, eval lead, UI architecture).  
> * **Mridul Mathur (Dev B)** owns the **Input → Intelligence** half (enrichment, cache, extraction, scoring, API orchestrator).  
> * **Jules (Google AI Agent)** acts as the **Autonomous QA/CI Worker** to absorb repetitive tasks (test suites, regression bug fixes, CI/CD pipelines, boilerplate, and linting) so Hemish and Mridul can focus entirely on high-leverage architecture and novelty implementation.

---

## 1. Ownership Map

| Directory / Component | Primary Owner | Purpose | Role of Jules |
|---|---|---|---|
| `enrichment/` | **Mridul (Dev A)** | Clause splitter (N1), intent signature (N2), query normalisation | Generates test cases for complex multi-intent query strings |
| `cache/` | **Mridul (Dev A)** | Gated + compositional cache (N1, N2) | Writes cache hit/miss benchmark tests & near-miss datasets |
| `extraction/` | **Mridul (Dev A)** | LLM prompt, provenance filter (N5) | Adds mocks & fixture tests for SIIS sentence extraction |
| `validation/` | **Mridul (Dev A)** | Schema + text-rule validators, repair loop, calibrated scoring (N5) | Implements regex edge-case tests & validator unit tests |
| `api/` | **Mridul (Dev A)** (Lead) | `/v1/troubleshoot`, `/health`, response + `meta` assembly | Writes FastAPI integration tests (TestClient) |
| `catalog/` | **Hemish (Dev B)** | Deeplink compiler, Settings Screen Graph (N3) | Generates parsing tests for `deeplinks.json` |
| `resolution/` | **Hemish (Dev B)** | Hybrid retrieval (BM25+FAISS), path rerank, validation binding (N4) | Adds benchmark scripts for retrieval latency & accuracy |
| `eval/` | **Hemish (Dev B)** (Lead) | Test-set harness, `metrics.md` generator, ablation tables | Automates test harness execution and metric aggregations |
| `frontend/` | **Hemish (Dev B)** | React UI: conversation, reasoning trace, action cards, simulated device | Scaffolds UI components & boilerplate layout |
| `Dockerfile` & `.github/` | **Jules** (Autonomous) | Containerisation, cold-start pre-caching, GitHub Actions CI/CD | Creates, verifies, and maintains GitHub Actions workflows |
| `data/` | **Shared** | Supplied starter assets — **read-only, never edited** | Read-only access |
| `schema.py` | **Shared** | Contract, copied from `student_kit/` — **never edited** | Read-only contract adherence verification |

**Novelty Ownership:**
* **Mridul (Dev A):** **N1** (Compositional Cache), **N2** (Intent Signature Gate), **N5** (Calibrated Scoring & Provenance)
* **Hemish (Dev B):** **N3** (Settings Screen Graph & Path Rerank), **N4** (Validation Deeplink Binding)

---

## 2. How We Utilize Jules (100 Tasks/Day Quota)

Jules takes care of recurring engineering toil via GitHub Issues and PRs so Mridul and Hemish remain focused on core intelligence and architecture:

1. **Automated Unit & Integration Test Generation:**
   * Write comprehensive `pytest` test suites for all modules in `validation/`, `catalog/`, `cache/`, and `resolution/`.
   * Test edge cases: malformed JSON, empty SIIS responses, missing catalog keys, out-of-order steps.
2. **Automated Bug Fixing & Edge Case Handling:**
   * When an eval test fails or a validator rejects an edge case, assign the issue to Jules with the traceback to fix the logic and submit a PR.
3. **Continuous Integration & Delivery (CI/CD):**
   * Maintain `.github/workflows/ci.yml` running tests, linting (`ruff`/`black`), type-checking (`mypy`), and verifying schema compliance on every push.
4. **Boilerplate & Utilities:**
   * Fast text normalization helpers, data formatting scripts, and Docker optimizations.

---

## 3. Day 0 — Joint Foundation (Mridul & Hemish)

1. **Lock the contract:** Copy `schema.py` from `student_kit/` into the repo. Freeze it.
2. **Resolve Day-One Open Questions:**
   * **Mridul:** Graded output shape validation (minimal vs full envelope) + SIIS topical match labeling.
   * **Hemish:** Catalog validation inspection (`{deeplink, key}`) + description navigation path extractability.
3. **Agree Interface Contracts:**
   * **Contract 1 (Extraction → Resolution):** Mridul outputs `Goal` with steps and empty deeplinks; Hemish populates `actionableDeeplink` and `validationDeeplink`.
   * **Contract 2 (Resolution → Scoring):** Hemish provides `retrieval_margin` and `path_alignment`; Mridul consumes them in `calibrate()`.
4. **Stand up API Stubs:** Create initial `POST /v1/troubleshoot` and `GET /health` endpoints returning a mock valid `Goal` payload.

---

## 4. Phased Implementation Plan

### Hemish Jain (Team Lead / Dev A) — Catalog, Resolution & Release
* **P0:** Catalog compiler over `deeplinks.json` (metadata matching, verbatim URI copy) · BM25 + FAISS hybrid retrieval · Safe → critical ordering · `manual` no-deeplink · `dummy_positive` handling.
* **P1:** **N3** Settings Screen Graph + path-alignment reranker + one-action-one-screen merge → **N4** `validationDeeplink` binding (derive result/condition/value from SIIS + control types).
* **P2:** Eval harness + `metrics.md` generator + ablation tables · React demo frontend with simulated device panel · Dockerfile + `results.jsonl`.

### Mridul Mathur (Dev B) — Input, Pipeline & Intelligence
* **P0:** Schema & text-rule validators (soft word-count target per finding C) · URL regex scrubber · repair loop · exact + cosine cache · LLM extraction prompt · API response + `meta` block.
* **P1:** **N2** Intent-signature gate (Display-skewed lexicon from `input.txt`) → **N5** Step-SIIS provenance filter + calibrated scoring → **N1** Compositional multi-intent cache.
* **P2:** Adversarial near-miss test set (~50 pairs) · Calibration dataset · `no_match` & `no_siis_context` fallback handling.
* **P2:** Eval harness + `metrics.md` generator + ablation tables · React demo frontend with simulated device panel · Dockerfile + `results.jsonl`.

---

## 5. Sync Points & Quality Gates

* **End of P0:** First end-to-end integration test through live FastAPI. Target: 100% schema validity and baseline rule pass.
* **End of P1:** Measure individual deltas for all 5 novelties (N1–N5) using Hemish's eval harness. Any component without a measurable gain is pruned.
* **End of P2:** Full ablation benchmark run, frontend polish, Docker verification, and final submission packaging.
