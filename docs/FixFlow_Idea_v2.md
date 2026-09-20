# FixFlow — Smart Guided Troubleshooting Engine

**Samsung PRISM GenAI Hackathon · Theme 02**
**Document:** Idea source of truth, v2 (verified against the Theme 02 brief)

> **Pitch:** FixFlow turns vague, compound Galaxy complaints into grounded, self-verifying, one-tap troubleshooting plans — and gets faster and cheaper the more complaints it sees.

---

## 1. Verification of v1 Against the Theme 02 Brief

v1 had the right instincts (catalog as source of truth, deterministic validation, measure before adding complexity) but misread the core task in several places. These must be fixed before any code is written.

### 1.1 Critical corrections

| # | v1 said | Brief actually says | Fix |
|---|---|---|---|
| 1 | Steps come from an LLM planner reasoning over a symptom → cause world model | **Plans must derive purely from the provided SIIS reference text.** No viable solution → `contexts: []` + `"fallback": "no_match"` | The engine is an *extractor + resolver*, not a free reasoner. Anything not in SIIS text is a hallucinated step. |
| 2 | World model infers causes like "background activity", "display usage" | Same rule as above | Speculative causal graphs are out. Replaced by two graphs mined only from supplied data (see §4.3, §4.1). |
| 3 | Categories: `standard / critical / manual` | `auto / critical / manual` | Use the enum from `schema.py`. `manual` actions **cannot** carry an `actionableDeeplink`. |
| 4 | `actionableDeeplink` is a URL string on the action | It is a `Deeplink` **object** (`deeplink`, `description`, `message`, `classes`, `originalType`) and lives on each **StepGroup**, alongside `validationDeeplink` | Follow `schema.py` exactly. |
| 5 | `query_variations` sits inside the goal | Response wrapper is `{query, query_variations, response: {contexts: [Goal]}, meta: {latency_ms, cache_hit, model, cost_usd}}` | See §6. |
| 6 | Retrieval over an action catalog generates a plan for any query | If `siis_response` is omitted, the engine only does **semantic lookup against pre-warmed cache**. No SIIS + cache miss → `"no_siis_context"` fallback | Cold path requires SIIS text. |
| 7 | `sis_responses.json` | `siis_responses.json` | Typo. |
| 8 | "Reusable mapping for 10k+ scenarios" | Not in the attached brief | Drop the claim unless it appears in another official doc. |

### 1.2 Missing from v1 entirely

Text-level output rules (goal syntax, 2–3 word sentence-case title, 5–7 word description starting with "It will", Title Case action names, 8–10 query variations), the `bixby://dummy_positive` placeholder rule, `GET /health`, the `meta` block, `results.jsonl` + `metrics.md` deliverables, the P95 ≤ 8 s cold-path target, and — most importantly — **`validationDeeplink`**, which v1 never mentions (see Novelty N4).

### 1.3 Scope to cut

Multi-turn session state (the API contract is a single stateless POST; nothing grades it), the speculative causal graph, the "ATLAS" branding in the submission, and any animation not backed by real computation.

---

## 2. Novelty Audit — Why v1 Would Look Like Everyone Else's

The brief is unusually prescriptive. It hands every team the pipeline, the retrieval method, the ablation table, and the pitfalls. Anything it names is **table stakes**, not novelty.

| Component | In the brief? | Novel? |
|---|---|---|
| Query enrichment + 8–10 paraphrases | Yes (Stage 0) | No |
| BM25 + dense hybrid retrieval | Yes (Roadmap Phase 2) | No |
| Semantic fast-path cache, ≥80% hit rate | Yes (Stage 3, eval) | No |
| Catalog-only deeplinks, URL scrubbing | Yes (§4.2, pitfalls) | No |
| Programmatic validators + repair loops | Yes (pitfall 5) | No |
| Safe-first, critical-last ordering | Yes | No |
| Baseline vs hybrid vs rules ablation | Yes (`metrics.md`) | No |
| "LLM proposes, catalog disposes" | Implied by catalog-integrity rule | No |
| Symptom → cause world model | No | Yes, but **violates** the no-hallucination rule |
| Multi-turn session state | No | Yes, but ungraded |

**Verdict:** v1 has near-zero *valid* novelty. Its one distinctive idea breaks a non-negotiable constraint. Expect most submissions to converge on the brief's own pipeline diagram.

**Strategy:** keep the brief's pipeline as the P0 baseline and win on five things the brief *hints at but doesn't solve* — each contract-safe, each measurable.

---

## 3. The Thesis (Revised)

> **Everyone will build the pipeline. We make it compositional, safe under paraphrase, screen-exact, self-verifying, and honestly scored.**

Design principle carried over from v1, now scoped correctly:

> **SIIS text decides *what* to do. The catalog decides *where* it happens. The LLM only translates between them.**

---

## 4. Novelties

### N1 — Compositional Multi-Intent Cache

**Gap in brief:** Its own first example is compound — *"Screen flickers and the battery dies fast"* — and `metrics.md` §6 explicitly asks for "unhandled multi-intent edge cases." A single-key semantic cache misses every unseen *combination* of already-solved problems.

**Mechanism:**
1. Clause segmentation splits the complaint into sub-intents (conjunction/clause splitter + per-clause intent signature, see N2).
2. Each sub-intent is looked up in the cache independently.
3. **Full hit** → compose cached Goals into `contexts: [Goal, Goal]`, dedupe shared critical actions (e.g., one restart), return with zero LLM calls.
4. **Partial hit** → run the cold pipeline only for the missing sub-intent; compose.
5. **Full miss** → normal cold path, then write *each* sub-intent back to the cache separately.

**Why it matters:** hit rate grows combinatorially rather than linearly, and partial hits cut cold-path cost proportionally. `contexts` is already a list in `schema.py`, so this is contract-native.

**Metrics:** hit rate on unseen *compound* queries (single-key cache vs compositional), cost/query on partial hits, step accuracy of composed vs freshly generated plans.

**Effort:** Medium. **Risk:** over-splitting a single intent ("slow and laggy") — mitigate by merging clauses whose signatures match.

---

### N2 — Intent-Signature Gated Cache (False-Hit Protection)

**Gap in brief:** It measures cache *hit rate* only. Pure cosine caches return confidently wrong plans for near-miss queries: *"battery drains fast"* vs *"battery not charging"*, *"screen too dim"* vs *"screen too bright"*. A wrong cached plan is worse than a slow correct one.

**Mechanism:** every cache entry and incoming query gets a discrete **intent signature**, extracted in a few milliseconds without an LLM (keyword lexicon mined from `queries.json` + a small classifier on the local embedding):

```text
signature = {
  domain:     Battery | Display | Camera | Performance,
  component:  e.g. "navigation bar", "brightness",
  symptom:    e.g. drain, overheat, flicker, slow, crash,
  polarity:   normal | negated          ("not charging" ≠ "charging"),
  trigger:    none | after_update | after_app_install | ...
}
```

A cache hit requires **both** embedding similarity ≥ τ **and** a compatible signature. Signature also becomes the canonical key, which directly serves the brief's *Deterministic Execution* gate.

**Metrics (new, not in brief):** false-hit rate on a hand-built **adversarial near-miss set** (~50 pairs), alongside hit rate on true paraphrases. Report the precision/recall trade-off as τ varies.

**Effort:** Low–Medium. **Risk:** signature too strict lowers hit rate below 80% — tune on the curve, don't guess.

---

### N3 — Path-Constrained Screen Resolution (Settings Screen Graph)

**Gap in brief:** It names *parent-menu matching* as a core challenge and grades *Screen Resolution Accuracy*, but its suggested method (BM25 + dense top-1) is exactly what matches parent menus, because "Display settings" is textually close to "Navigation bar settings under Display."

**Mechanism:** this is where v1's "world model" survives — rebuilt from supplied data only.
1. **Offline:** parse every `deeplinks.json` entry's `description` / `message` / `qna_description` into a navigation path (e.g., `Display › Navigation bar`) and assemble a **Settings Screen Graph**.
2. **Online:** parse the step group's navigation steps (`Tap on Display.` → `Tap on Navigation bar.`) into a path.
3. Retrieve candidates with hybrid search, then **rerank by path alignment**: reward the deepest matching node, penalise candidates whose path is a strict prefix of the step path (the parent-menu error).
4. Valid screen not in catalog → `bixby://dummy_positive`. `manual` action → no deeplink. Matching never touches the masked URI string.
5. The same graph enforces **One Action = One Screen**: consecutive steps resolving to the same node are merged into one action.

**Metrics:** screen resolution accuracy, and a separately reported **parent-menu error rate**. Add as "Variant C" in the ablation table.

**Effort:** Medium. **Risk:** inconsistent description phrasing — fall back to plain hybrid score when path parsing yields < 2 nodes.

---

### N4 — Self-Verifying Plans via `validationDeeplink`

**Gap in brief:** `schema.py` defines `ValidationDeepLink` (`key`, `resultType`, `condition`, `value`) and `deeplinks.json` ships "control types and toggle validation rules" — yet the worked example sets `validationDeeplink: null`. Most teams will copy that. This is the one field in the contract that turns a plan from *instructions* into a *closed loop*.

**Mechanism:**
1. For every step group resolving to a catalog entry with a toggle/validation rule, populate `validationDeeplink` from the catalog (never generated).
2. Derive the expected target state from the SIIS step text (e.g., "toggle **on** Gesture hint" → `resultType: boolean, condition: equal, value: "true"`).
3. Client behaviour it enables: **skip** steps already satisfied, **confirm** a fix took effect after the tap, and **escalate** to the next action only if verification fails.

**Demo:** a mock device-state panel in the frontend (clearly labelled as simulated) shows a step being auto-skipped because the toggle is already in the correct state.

**Metrics:** % of eligible step groups with a valid `validationDeeplink`, correctness of expected value against hand labels, average steps skipped per plan on simulated states.

**Effort:** Low–Medium. **Risk:** must first confirm what validation metadata `deeplinks.json` really contains — **inspect on day one.**

---

### N5 — Evidence-Calibrated `score` + Step Provenance

**Gap in brief:** `score` is "confidence 0.0–1.0" with no definition. LLM-emitted scores (like the example's 0.93) are uncalibrated decoration.

**Mechanism:**
1. Every extracted step is aligned to the SIIS sentence it came from (provenance). Steps with no supporting sentence above an overlap threshold are **dropped** — this is a programmatic enforcement of "No Hallucinated Steps."
2. `score` is computed, not generated:
   `score = calibrate(retrieval margin, grounding coverage, deeplink path-alignment, validator pass rate)`
3. Fit the calibration on the hand-labelled dev set; below a threshold → return the `no_match` fallback instead of a weak plan.
4. Provenance stays **out** of the contract payload; it is exposed via a debug trace and visualised in the demo UI.

**Metrics:** reliability diagram / expected calibration error of `score` vs actual step accuracy; hallucinated-step rate with vs without provenance filtering.

**Effort:** Low. **Risk:** small labelled set — label ~80–100 scenarios across the four domains (needed for evaluation anyway).

---

### Stretch (only after N1–N5 are measured)

**S1 — Code-mixed complaint robustness.** Add Hinglish / Tanglish complaint variants (*"phone bahut garam ho raha hai"*) to the unseen-paraphrase test set and to cache pre-warming. Outputs stay English. Relevant to Samsung R&D India; cheap to test, strong differentiator if it holds.

**S2 — Follow-up refinement in the demo only.** A second user message narrows an existing plan (e.g., adds the trigger "after the update") by updating the intent signature and re-running lookup. Presented as a UI feature, not an API change.

---

## 5. Architecture

```text
POST /v1/troubleshoot  { query, siis_response? }
          │
          ▼
┌──────────────────────────────┐
│ 0. Enrichment                │  normalise · clause split (N1)
│                              │  intent signature per clause (N2)
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐   full hit ──► compose Goals ──► response (≤300 ms)
│ 1. Compositional Gated Cache │   partial ──► cold path for missing clauses only
│    (N1 + N2)                 │   miss + no SIIS ──► contexts: [] · no_siis_context
└──────────────┬───────────────┘
               ▼  (cold path, requires SIIS text)
┌──────────────────────────────┐
│ 2. Structure Extraction      │  LLM, schema-constrained output
│                              │  step ↔ SIIS provenance filter (N5)
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ 3. Screen Resolution         │  hybrid retrieval over catalog metadata
│    (N3)                      │  path-alignment rerank on Screen Graph
│                              │  one action = one screen merge
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ 4. Verification Binding (N4) │  attach validationDeeplink from catalog
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ 5. Validator + Repair Loop   │  schema · word counts · casing · goal syntax
│                              │  URL regex scrub · catalog URI whitelist
│                              │  manual ⇒ no deeplink · ordering auto → critical
│                              │  calibrated score + no_match gate (N5)
└──────────────┬───────────────┘
               ▼
       write per-clause cache ──► response + meta
```

**LLM calls on cold path:** one extraction call (+ one repair call only if validation fails). Paraphrase generation happens offline during cache pre-warming, not per request.

---

## 6. Output Contract (from `schema.py` + Appendix B)

```json
{
  "query": "Screen flickers and the battery dies fast",
  "query_variations": ["...8 to 10 paraphrases..."],
  "response": {
    "contexts": [
      {
        "goal": "Follow these steps to perform this Display Troubleshooting",
        "title": "Screen flicker",
        "score": 0.0,
        "actions": [
          {
            "actionName": "Adjust Screen Brightness",
            "description": "It will stabilise your display brightness",
            "category": "auto",
            "stepGroups": [
              {
                "steps": ["Open Settings.", "Tap on Display.", "..."],
                "actionableDeeplink": {
                  "deeplink": "<verbatim URI from deeplinks.json>",
                  "description": "<catalog description>",
                  "message": "<catalog message>"
                },
                "validationDeeplink": {
                  "deeplink": "<verbatim URI>",
                  "key": "<catalog key>",
                  "resultType": "boolean",
                  "condition": "equal",
                  "value": "true"
                }
              }
            ]
          }
        ]
      },
      { "goal": "Follow these steps to perform this Battery Troubleshooting", "...": "..." }
    ]
  },
  "meta": { "latency_ms": 0, "cache_hit": true, "model": "<model id>", "cost_usd": 0.0 }
}
```

Illustrative only — field values above are placeholders, not real catalog entries. `schema.py` and `samples/` are authoritative; confirm where the `fallback` flag lives by checking `samples/`.

**Hard rules checklist** (each becomes a unit-tested validator):

| Field | Rule |
|---|---|
| `goal` | `Follow these steps to perform this <Topic> Troubleshooting` (or `Configuration`) |
| `title` | 2–3 words, sentence case |
| `score` | float in [0, 1] |
| `actionName` | Title Case, exactly one screen |
| `description` | 5–7 words, starts with "It will" |
| `steps` | imperative, one interaction each, no URLs |
| `category` | `auto` · `critical` (last) · `manual` (no actionable deeplink) |
| `actionableDeeplink` | verbatim from catalog, or `bixby://dummy_positive` for valid uncatalogued screens |
| `query_variations` | 8–10, mixed registers incl. typos |
| Response body | pure JSON, no markdown, no preamble, zero web URLs |

---

## 7. Evaluation Plan

### 7.1 Brief's metrics (must report)

Schema validity ≥ 99% · rule compliance ≥ 95% · URL leaks = 0 · catalog URI validity 100% · auto actions with valid deeplink ≥ 90% · step accuracy (0–3) · deeplink relevance (0–2) · P95 ≤ 300 ms on exact and paraphrase hits · P95 ≤ 8 s cold · paraphrase hit rate ≥ 80% · cost per query.

### 7.2 Our added metrics (the novelty evidence)

| Novelty | Metric |
|---|---|
| N1 | Hit rate on unseen compound queries: single-key vs compositional; cost on partial hits |
| N2 | False-hit rate on adversarial near-miss set; hit/false-hit curve over τ |
| N3 | Parent-menu error rate; screen accuracy vs plain hybrid |
| N4 | Valid `validationDeeplink` coverage; expected-value correctness |
| N5 | Calibration error of `score`; hallucinated-step rate with/without provenance filter |

### 7.3 Ablation table (extends the brief's `metrics.md` §5)

| Variant | Step acc. | Screen acc. | Parent-menu err. | P95 | Cost/query |
|---|---|---|---|---|---|
| Baseline: full LLM deeplink mapping | | | | | |
| A: Hybrid BM25 + dense | | | | | |
| B: Pure rules-based mapping | | | | | |
| **C: A + path-constrained rerank (N3)** | | | | | |

| Cache variant | Paraphrase hit rate | False-hit rate | Compound hit rate |
|---|---|---|---|
| Exact string | | | |
| Cosine only | | | |
| **Cosine + signature (N2)** | | | |
| **+ compositional (N1)** | | | |

**All numbers come from real runs.** No placeholder metrics in the deck.

### 7.4 Test sets to build

Hand-labelled dev set (~80–100 scenarios, all four domains) · unseen paraphrase set (formal, casual, keyword-only, frustrated, typo) · adversarial near-miss pairs (~50) · compound queries (~30, built from pairs of solved scenarios) · no-SIIS and unsupported-issue cases for fallback testing.

---

## 8. Demo Script (3 scenes, ~3 min)

**Scene 1 — Compound complaint, full cache hit.** "Screen flickers and battery dies fast" → two Goal cards appear in well under 300 ms, `cache_hit: true`, `cost_usd: 0.0`. Side panel shows the two clause signatures that each hit.

**Scene 2 — The near-miss trap.** "Battery won't charge" — a cosine-only cache would return the drain plan (shown greyed out). FixFlow rejects it on signature polarity and runs the cold path. This is the moment that separates us.

**Scene 3 — Self-verifying plan.** Cold-path extraction with provenance highlighting (each step linked to its SIIS sentence), screen graph shows the resolver choosing `Display › Navigation bar` over `Display`, and the simulated device panel auto-skips a toggle that's already on.

**Closer:** unsupported complaint ("phone smells like burning plastic") → `contexts: []`, `no_match`. No invented fix.

---

## 9. Build Priorities

| Tier | Scope | Exit criterion |
|---|---|---|
| **P0 — Contract** | Inspect data; catalog compiler; schema validators; extraction prompt + repair loop; hybrid resolution; ordering; exact + cosine cache; `/v1/troubleshoot`, `/health`; `results.jsonl`; eval harness | All brief gates pass on the 5 samples + dev set |
| **P1 — Differentiators** | N2 signature gate → N3 path rerank → N5 calibrated score → N4 validation binding → N1 compositional cache | Each has a measured delta vs P0 |
| **P2 — Product** | Frontend (conversation · reasoning trace · action cards · simulated device state); Docker; `metrics.md`; deck; video | Demo script runs end to end |
| **P3 — Stretch** | S1 code-mixed robustness; S2 demo follow-up | Only if P1 numbers are in |

Order within P1 is by effort-to-evidence: N2 and N3 are cheapest to prove; N1 depends on N2.

**Rule carried from v1:** a component that shows no measurable gain in its ablation gets removed, even if it's one of ours.

---

## 10. Tech Stack (initial, benchmark before locking)

FastAPI + Pydantic (schema from `schema.py`) · local small embedding model on CPU for cache + retrieval (keeps hits under 300 ms) · BM25 + FAISS for hybrid search · SQLite or on-disk store for the persistent cache · one hosted small LLM for extraction, chosen by the cost/accuracy benchmark · regex + whitelist validators · Docker · lightweight React frontend.

---

## 11. Repository

```text
fixflow/
├── api/            # FastAPI app, /v1/troubleshoot, /health
├── catalog/        # deeplink compiler, Settings Screen Graph (N3)
├── enrichment/     # clause splitter (N1), intent signature (N2)
├── cache/          # gated + compositional cache
├── extraction/     # LLM prompt, provenance filter (N5)
├── resolution/     # hybrid retrieval, path rerank, validation binding (N4)
├── validation/     # schema + text-rule validators, repair loop, scoring
├── eval/           # test sets, harness, metrics.md generator
├── frontend/
├── data/           # supplied starter assets, untouched
├── results.jsonl
├── metrics.md
├── Dockerfile
└── README.md
```

---

## 12. Open Questions — Resolve on Day One

1. What validation / control-type fields does `deeplinks.json` actually contain? (Gates N4.)
2. Are descriptions consistent enough to parse navigation paths? (Gates N3.)
3. Where does the `fallback` flag sit in the response — `meta` or top level? (Check `samples/`.)
4. How many `queries.json` scenarios have a matching `siis_responses.json` entry? (Sets pre-warm coverage.)
5. Does any official doc besides this brief mention the 10k+ scenario scale?

---

## 13. Source-of-Truth Hierarchy

1. Official Theme 02 brief — non-negotiable
2. Supplied datasets + `schema.py` + `samples/` — define the contract
3. Measured evaluation results — beat assumptions
4. This document — product and architecture direction
5. Team brainstorming — welcome, but never silently overrides 1–4

**Naming:** FixFlow is the product. "ATLAS" is internal team vocabulary only and does not appear in the submission.
