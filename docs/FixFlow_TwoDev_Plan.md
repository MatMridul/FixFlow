# FixFlow — Two-Developer Implementation Plan

**Samsung PRISM GenAI Hackathon · Theme 02**
**Companion to `FixFlow_Idea_v2.md`** (the source-of-truth idea doc). This file divides that plan across **two developers** with clean ownership, defined interfaces, and sync points.

> **Split principle:** FixFlow's pipeline has two halves that meet at the `Goal` contract object. **Dev A owns the input → intelligence half** (enrichment, cache, extraction, scoring). **Dev B owns the catalog → resolution half** (catalog, screen graph, retrieval, deeplink binding). Schema, API, and eval are a shared spine with single-owner files so the two never edit the same code.

---

## 1. Ownership Map (who touches which directory)

Repo layout from `FixFlow_Idea_v2.md` §11. Each directory has exactly one owner to prevent merge collisions.

| Directory | Owner | Purpose |
|---|---|---|
| `enrichment/` | **A** | clause splitter (N1), intent signature (N2), query normalisation |
| `cache/` | **A** | gated + compositional cache (N1, N2) |
| `extraction/` | **A** | LLM prompt, provenance filter (N5) |
| `validation/` | **A** | schema + text-rule validators, repair loop, calibrated scoring (N5) |
| `api/` | **A** (lead) | `/v1/troubleshoot`, `/health`, response + `meta` assembly |
| `catalog/` | **B** | deeplink compiler, Settings Screen Graph (N3) |
| `resolution/` | **B** | hybrid retrieval, path rerank, validation binding (N4) |
| `eval/` | **B** (lead) | test-set harness, `metrics.md` generator, ablation tables |
| `frontend/` | **B** | React UI: conversation, reasoning trace, action cards, simulated device |
| `Dockerfile` | **B** | containerisation, cold-start handling |
| `data/` | shared | supplied starter assets — **read-only, never edited** |
| `schema.py` | shared | contract, copied from `student_kit/` — **never edited** |

**Novelty ownership:** Dev A → **N1, N2, N5**. Dev B → **N3, N4**.

---

## 2. Day 0 — Joint Foundation (both devs, pair on it)

Do these together before splitting. Forking before this is done breaks everything downstream.

1. **Lock the contract.** Copy `schema.py` from `student_kit/` into the repo. Agree it is frozen.
2. **Resolve the Day-One open questions** (`FixFlow_Idea_v2.md` §12) — split the data inspection:
   - **Dev A:** Q6 (graded output shape — minimal vs full envelope) + Q7 (SIIS-to-query topical match rate across all 20 rows).
   - **Dev B:** Q1 (catalog `validation` fields — confirmed `{deeplink, key}`) + Q2 (are `description`s parseable into nav paths — gates N3).
   - 30 min each, then share findings in the doc.
3. **Agree the two interface contracts** (§4 below).
4. **Stand up API stubs.** `POST /v1/troubleshoot` + `GET /health` returning a hardcoded valid `Goal` payload, so both devs integration-test against a live endpoint from hour one.

---

## 3. Per-Developer Tracks (phased, mapped to `FixFlow_Idea_v2.md` §9 tiers)

### Dev A — Input & Intelligence (front half)

| Tier | Tasks | Exit criterion |
|---|---|---|
| **P0** | Schema validators (goal syntax · 2–3 word title · Title-Case action · `It will` prefix; **word count is a SOFT target — do not hard-reject, official sample uses 9 & 12 words, finding C**) · URL regex scrubber · repair loop · exact + cosine cache · LLM extraction prompt · response + `meta` assembly | Validators pass on all 5 sample rows; extraction produces schema-valid `Goal`s |
| **P1** | **N2** intent-signature gate (lexicon mined from `input.txt`, Display-skewed) → **N5** step-SIIS provenance filter + calibrated `score` + `no_match` gate → **N1** compositional multi-intent cache (**depends on N2 — same owner, no cross-dev block**) | Each novelty has a measured delta vs P0 |
| **P2** | Adversarial near-miss test set (~50 pairs, for N2) · calibration dev-set labels (~80–100 scenarios) · owns `no_match` / `no_siis_context` fallback logic (lives at `meta`/API layer — **no `fallback` field exists in `schema.py`, finding D**) | Fallback returns cleanly; calibration curve plotted |

### Dev B — Catalog & Resolution (back half)

| Tier | Tasks | Exit criterion |
|---|---|---|
| **P0** | Catalog compiler (parse `deeplinks.json`; match on `description`/`message`/`qna_description`, **never on the masked URI string**) · BM25 + FAISS hybrid retrieval · safe → critical action ordering · `bixby://dummy_positive` handling · `manual` ⇒ no actionable deeplink | Retrieval returns verbatim catalog URIs; ordering + manual rules enforced |
| **P1** | **N3** Settings Screen Graph + path-alignment rerank + one-action-one-screen merge (**risk Medium–High — catalog `description` is full-sentence prose, no breadcrumb separators, finding F**) → **N4** `validationDeeplink` binding (copy `{deeplink, key}` verbatim; **derive `resultType`/`condition`/`value` from SIIS text + `originalType`/`control_type`, catalog does not supply them, finding E**) | Parent-menu error rate measured; validation coverage measured |
| **P2** | Eval harness + `metrics.md` generator + ablation tables · React frontend (conversation · reasoning trace · action cards · simulated device panel) · Docker · `results.jsonl` | Demo script (`FixFlow_Idea_v2.md` §8) runs end to end |

---

## 4. Interface Contracts (define Day 0, never break silently)

These are the only two places the halves touch. Lock the signatures early.

**Contract 1 — Extraction → Resolution.**
Dev A hands Dev B a `Goal` object with populated step text but **empty** deeplink fields. Dev B fills `actionableDeeplink` + `validationDeeplink` and returns it. Agree the exact intermediate shape (a `Goal` with `stepGroups[].actionableDeeplink = None`).

**Contract 2 — Resolution → Scoring (the N5 cross-dependency).**
Dev B exposes, per action, a `retrieval_margin` and a `path_alignment_score`. Dev A consumes them in the calibrator. This is the single entanglement point:

```python
# Dev A owns: grounding_coverage, validator_pass_rate
# Dev B owns: retrieval_margin, path_alignment
def calibrate(retrieval_margin, grounding_coverage,
              path_alignment, validator_pass_rate) -> float:
    ...  # returns Goal.score in [0, 1]
```

---

## 5. Integration & Sync Points

- **End of P0 (first end-to-end checkpoint):** wire A's extraction + B's resolution through the real API. **Target: all brief gates pass on the 5 sample rows.** If this fails, stop and fix before any P1 work.
- **End of each P1 novelty:** the owning dev reports a measured ablation delta vs P0. **Rule from `FixFlow_Idea_v2.md` §9: a component with no measurable gain gets cut, even if it's ours.**
- **P2:** Dev B's eval harness scores the combined A+B output; both devs fill their own rows in the ablation tables (§7 of the idea doc).

---

## 6. Load Balance & Contingency

- Dev A is algorithm-heavy early — cache, extraction, and scoring stack up through P1.
- Dev B carries retrieval + infra + frontend — lighter algorithmic load late, which is why Docker, frontend, and the eval harness sit on B to even the total out.
- **Contingency:** N1 is last for Dev A and depends on N2. If A slips, Dev B takes the compositional-cache **compose + dedupe** logic (merging cached `Goal`s, deduping shared critical actions) — B already owns Goal-merging patterns from action ordering, so it is a natural handoff.

---

## 7. Quick Checklists

### Dev A
- [ ] Copy + freeze `schema.py`; build Pydantic validators
- [ ] Text-rule validators (goal/title/description/action) with soft word-count
- [ ] URL scrubber + repair loop
- [ ] Exact + cosine semantic cache
- [ ] LLM extraction prompt (schema-constrained)
- [ ] Response + `meta` assembly in `api/`
- [ ] N2 intent-signature gate + near-miss test set
- [ ] N5 provenance filter + `calibrate()` + `no_match` gate
- [ ] N1 compositional multi-intent cache
- [ ] Answer §12 Q6, Q7

### Dev B
- [ ] Catalog compiler over `deeplinks.json` (metadata matching, verbatim URI copy)
- [ ] BM25 + FAISS hybrid retrieval
- [ ] Safe → critical ordering; `manual` no-deeplink; `dummy_positive`
- [ ] N3 Settings Screen Graph + path rerank + one-action-one-screen merge
- [ ] N4 `validationDeeplink` binding + derive result/condition/value
- [ ] Eval harness + `metrics.md` + ablation tables
- [ ] React frontend + simulated device panel
- [ ] Dockerfile + `results.jsonl`
- [ ] Answer §12 Q1, Q2

---

## 8. Source-of-Truth Note

This file inherits the hierarchy in `FixFlow_Idea_v2.md` §13: the official Theme 02 brief and the supplied datasets/`schema.py`/samples win over anything written here. Where this plan cites a "finding," it refers to the real-data inspection in `FixFlow_Idea_v2.md` §1.4. Work division is process direction only — it never overrides the contract.
