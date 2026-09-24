# FixFlow — Engineering Tasks & Implementation Checklist

**Samsung PRISM GenAI Hackathon · Theme 02**  
**Lead Developer (Dev A):** Mridul  
**Collaborator (Dev B):** Hemish  
**Autonomous Worker:** Google Jules  
**Status:** In Progress (Spec-First Mode)

---

## 🛠️ Operating Rules & Branching Strategy

1. **Spec-First:** Every task must have its specification (interfaces, inputs, outputs, error handling) discussed and approved by Mridul before writing code.
2. **Git Hygiene:** No direct pushes to `main`. Every task is developed on its dedicated branch: `feature/mridul-<task-slug>`.
3. **Ground Truth:** All logic derives strictly from `FixFlow_Idea_v3.md`, `schema.py`, and actual dataset findings.

---

## 📋 Phase 0: Contract Locking & P0 Core Pipeline

*Goal: Stand up the core extraction, validation, caching, and API routing pipeline. Exit criteria: 100% schema validity and successful end-to-end execution on sample inputs.*

- [x] **Task A.0.1 — Schema & Contract Freezing**
  - **Branch:** `feature/mridul-schema-contracts`
  - **Files:** `schema.py`, `api/models.py`
  - **Spec Scope:**
    - Copy & freeze official `schema.py` (`Goal`, `Action`, `StepGroup`, `Deeplink`, `ValidationDeepLink`, `ContextDeeplinkResponse`).
    - Define API request envelope `{query: str, siis_response: Optional[SIISResponse] = None}`.
    - Define API response wrapper including `meta` block (`latency_ms`, `cache_hit`, `model`, `cost_usd`, `fallback`).
  - **Acceptance Criteria:** `pydantic.ValidationError` raised on illegal schemas; sample output JSON passes schema validation.

- [x] **Task A.0.2 — Validation & Text-Rule Engine**
  - **Branch:** `feature/mridul-validation-rules`
  - **Files:** `validation/rules.py`, `validation/schema_validator.py`, `validation/scrubber.py`
  - **Spec Scope:**
    - `goal` syntax validator: `Follow these steps to perform this <Topic> Troubleshooting` (or `Configuration`).
    - `title` validator: 2–3 words, sentence case.
    - `actionName` validator: Title Case, exactly one screen.
    - `description` validator: Starts with "It will", soft word-count tolerance (per Finding C).
    - `steps` validator: Imperative sentences, one interaction per step.
    - `category` validator: `auto` | `critical` (must be sorted last) | `manual` (cannot carry `actionableDeeplink`).
    - URL Regex Scrubber: Strip all external web URLs (`http://`, `https://`, markdown links) from steps and descriptions.
  - **Acceptance Criteria:** Unit tests verifying all positive/negative validation rules; 0 URL leaks.

- [ ] **Task A.0.3 — Single-Shot JSON Repair Loop**
  - **Branch:** `feature/mridul-repair-loop`
  - **Files:** `validation/repair.py`
  - **Spec Scope:**
    - Intercept validator failure traces (e.g. missing "It will" prefix, malformed casing, broken JSON syntax).
    - Construct targeted self-repair prompt with exact error message and invalid payload.
    - Re-validate repaired output; fall back gracefully if repair fails.
  - **Acceptance Criteria:** Cap repair to max 1 LLM call; recovers from simulated malformed outputs.

- [ ] **Task A.0.4 — Schema-Constrained LLM Extractor**
  - **Branch:** `feature/mridul-llm-extractor`
  - **Files:** `extraction/prompt.py`, `extraction/extractor.py`
  - **Spec Scope:**
    - Design few-shot system prompt forcing LLM to extract structured troubleshooting steps **strictly** from the provided SIIS text.
    - Output intermediate `Goal` objects with empty deeplink fields (ready for Dev B / Hemish to resolve).
    - Temperature = 0.0 for deterministic output.
  - **Acceptance Criteria:** Zero invented steps outside SIIS context; returns intermediate `Goal` matching Contract 1.

- [ ] **Task A.0.5 — Baseline Exact & Cosine Vector Cache**
  - **Branch:** `feature/mridul-baseline-cache`
  - **Files:** `cache/semantic_cache.py`, `cache/store.py`
  - **Spec Scope:**
    - Level 1: Exact string hash lookup (0 ms).
    - Level 2: Local dense embedding similarity cache using CPU-friendly embedding model (`sentence-transformers` / small onnx).
    - Sub-300ms response time on cache hit.
    - Persistent on-disk storage (SQLite / JSON store).
  - **Acceptance Criteria:** P95 latency ≤ 50ms on exact hit, ≤ 150ms on cosine hit; returns cached `Goal`.

- [ ] **Task A.0.6 — FastAPI Orchestrator & Telemetry Wrapper**
  - **Branch:** `feature/mridul-api-orchestrator`
  - **Files:** `api/app.py`, `api/routes.py`
  - **Spec Scope:**
    - `POST /v1/troubleshoot` orchestrating Cache → Extractor → (Dev B Resolver) → Validator → Response.
    - `GET /health` returning service status, cache entry count, and model readiness.
    - Real-time latency stopwatch and cost tracking (`cost_usd = 0.0` on cache hit).
  - **Acceptance Criteria:** Both endpoints respond cleanly with 200 OK and accurate `meta` fields.

> 🏁 **Checkpoint 0 (P0 Integration):** Wire Dev A pipeline with Dev B's catalog resolver. Verify end-to-end run on 20 rows of `input.txt` + `siis_responses.json`.

---

## 🚀 Phase 1: Core Novelties & Differentiators

*Goal: Implement and measure Mridul's three key architectural novelties (N1, N2, N5).*

- [ ] **Task A.1.1 — Novelty N2: Intent-Signature Gated Cache (False-Hit Protection)**
  - **Branch:** `feature/mridul-n2-intent-signature`
  - **Files:** `enrichment/intent_signature.py`, `cache/gated_cache.py`
  - **Spec Scope:**
    - Fast lexicon-based signature extractor (0 LLM calls):
      `signature = {domain, component, symptom, polarity, trigger}`
    - Mined lexicon based on `input.txt` (Display domain) + Device ontology.
    - Gated Cache Rule: Cache hit requires **both** cosine similarity $\ge \tau$ **AND** compatible signature (`polarity` match is mandatory).
  - **Acceptance Criteria:** Correctly rejects near-miss queries (*"battery draining fast"* vs *"battery not charging"*); false-hit rate drops to 0% on adversarial set.

- [ ] **Task A.1.2 — Novelty N5: Step Provenance Bipartite Filter & Score Calibrator**
  - **Branch:** `feature/mridul-n5-provenance-calibration`
  - **Files:** `extraction/provenance.py`, `validation/calibrator.py`
  - **Spec Scope:**
    - Sentence-level bipartite overlap between extracted steps and raw SIIS text.
    - Drop any candidate step with 0 supporting SIIS sentences (eliminates hallucinations).
    - Calibrate `Goal.score`:
      `score = calibrate(grounding_coverage, validator_pass_rate, retrieval_margin, path_alignment)`
    - Trigger `no_match` fallback if calibrated score falls below threshold $\theta$.
  - **Acceptance Criteria:** Hallucinated step rate = 0.0%; score reflects empirical grounding rather than raw LLM confidence.

- [ ] **Task A.1.3 — Novelty N1: Clause Splitter & Compositional Multi-Intent Cache**
  - **Branch:** `feature/mridul-n1-compositional-cache`
  - **Files:** `enrichment/clause_splitter.py`, `cache/compositional.py`
  - **Spec Scope:**
    - Compound complaint segmentation (conjunction parser & punctuation splitter).
    - Independent sub-intent signature extraction and cache lookup.
    - **Full Hit:** Compose cached `Goal`s into `contexts: [Goal, Goal]`, deduplicate shared critical actions (e.g. 1 restart).
    - **Partial Hit:** Cold-path extraction for missing sub-intent only; compose.
    - **Miss:** Full cold-path, write sub-intents to cache independently.
  - **Acceptance Criteria:** Compound queries (*"Screen flickers and battery dies fast"*) resolve under 300ms on cached components with 0 LLM calls.

> 🏁 **Checkpoint 1 (P1 Novelty Ablation):** Measure and record ablation deltas for N1, N2, and N5 in `metrics.md`.

---

## 🔬 Phase 2: Datasets, Calibration & Submission Packaging

*Goal: Build benchmark datasets, implement clean fallbacks, and harden the system for evaluation.*

- [ ] **Task A.2.1 — Adversarial Near-Miss Test Dataset**
  - **Branch:** `feature/mridul-adversarial-dataset`
  - **Files:** `data/adversarial_near_miss.json`
  - **Spec Scope:**
    - Hand-craft 50 near-miss pairs across domains (e.g. negated polarity, different components).
  - **Acceptance Criteria:** Used in `eval/` to benchmark Cosine-only Cache vs N2 Gated Cache.

- [ ] **Task A.2.2 — Calibration Dev-Set Ground Truth**
  - **Branch:** `feature/mridul-calibration-dev-set`
  - **Files:** `data/calibration_dev_set.json`
  - **Spec Scope:**
    - Label ~80–100 scenarios across 4 domains with ground-truth step relevance and grounding coverage.
  - **Acceptance Criteria:** Generates calibration reliability diagrams and ECE metrics in `metrics.md`.

- [ ] **Task A.2.3 — API Fallback & Edge-Case Handling**
  - **Branch:** `feature/mridul-fallbacks`
  - **Files:** `api/routes.py`, `api/models.py`
  - **Spec Scope:**
    - If no SIIS provided and cache miss $\rightarrow$ return `contexts: []`, `meta.fallback = "no_siis_context"`.
    - If complaint unsupported / calibrated score $< \theta \rightarrow$ return `contexts: []`, `meta.fallback = "no_match"`.
  - **Acceptance Criteria:** Complies with Theme 02 fallback rules without throwing 500 errors.

- [ ] **Task A.2.4 — Jules Activation & Regression Test Suite**
  - **Trigger:** Milestone 1 / P0 completion.
  - **Files:** `tests/test_validation_rules.py`, `tests/test_cache.py`, `tests/test_api.py`
  - **Scope:** Dispatch Jules to generate exhaustive `pytest` suites and configure CI/CD.
