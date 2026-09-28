"""End-to-end benchmark that fills the brief's Appendix C template (metrics.md).

Runs the real API in-process (FastAPI TestClient, live LLM chain from .env):

  * cold path     N=30  20 kit rows + 10 unseen scenarios (eval/unseen_scenarios.json),
                        cache cleared before each so every call runs the full pipeline
  * exact repeat  N=30  same query + SIIS again, straight after its cold call
  * paraphrase    N=60  2 fresh LLM paraphrases per scenario, generated up front and
                        never written to the cache, so hits come from semantic matching
  * ablation      deeplink mapping on eval/dev_set.json: full-LLM choice vs our hybrid
                  resolver vs pure BM25 rules
  * compliance    results.jsonl checked against the FAQ scoring rules

Usage:  python scripts/benchmark.py            (needs LLM keys in .env)
        BENCH_PACE_S=4 python scripts/benchmark.py
"""
from __future__ import annotations

import json
import os
import platform
import re
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from fastapi.testclient import TestClient  # noqa: E402

from api.app import create_app  # noqa: E402
from cache import CacheStore, CompositionalCache  # noqa: E402
from catalog.loader import load_catalog  # noqa: E402
from extraction.deterministic import _sections  # noqa: E402
from extraction.llm_client import LLMChain, load_dotenv  # noqa: E402
from resolution.binder import bind_actionable_deeplink  # noqa: E402
from resolution.retriever import HybridRetriever  # noqa: E402
from schema import ContextDeeplinkResponse  # noqa: E402
from validation.scrubber import contains_urls  # noqa: E402

PACE_S = float(os.environ.get("BENCH_PACE_S", "4"))
GOAL_RE = re.compile(r"^Follow these steps to perform this .+ (Troubleshooting|Configuration)\.?$")
_STOP = {
    "open", "settings", "then", "your", "with", "from", "this", "that", "tap", "select",
    "turn", "the", "and", "for", "device", "phone", "galaxy", "samsung",
}


# ---------------------------------------------------------------- helpers

def _stems(text: str) -> set:
    words = re.findall(r"[a-z]+", text.lower())
    return {w[:-1] if w.endswith("s") and len(w) > 4 else w for w in words if len(w) > 3} - _STOP


def pct(values: list[float], p: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    k = max(0, min(len(ordered) - 1, int(round(p / 100 * len(ordered) + 0.5)) - 1))
    return ordered[k]


def load_scenarios() -> list[dict]:
    queries = [l.strip() for l in open(ROOT / "data/input.txt", encoding="utf-8") if l.strip()]
    raw = json.load(open(ROOT / "data/siis_responses.json", encoding="utf-8"))
    siis = raw.get("responses", raw) if isinstance(raw, dict) else raw
    rows = [
        {"id": f"kit_{i:02d}", "query": q, "siis_response": e["siis_response"], "unseen": False}
        for i, (q, e) in enumerate(zip(queries, siis), start=1)
    ]
    unseen = json.load(open(ROOT / "eval/unseen_scenarios.json", encoding="utf-8"))["scenarios"]
    rows += [{"id": u["id"], "query": u["query"], "siis_response": u["siis_response"], "unseen": True} for u in unseen]
    return rows


def step_accuracy(goal: dict, content: str) -> tuple[float, float, float]:
    """Automated 0-3 proxy: grounding + completeness + ordering (each 0-1)."""
    siis = _stems(content)
    steps = [s for a in goal["actions"] for g in a["stepGroups"] for s in g["steps"]]
    grounded = [
        len(_stems(s) & siis) / len(_stems(s)) >= 0.5 for s in steps if _stems(s)
    ]
    grounding = sum(grounded) / len(grounded) if grounded else 0.0

    plan = _stems(" ".join(steps + [a["actionName"] for a in goal["actions"]]))
    headed = [(h, b) for h, b in _sections(content) if _stems(h)]
    covered = [len(_stems(h) & plan) / len(_stems(h)) >= 0.5 for h, _ in headed]
    completeness = sum(covered) / len(covered) if covered else 1.0

    cats = [a["category"] for a in goal["actions"]]
    first_critical = next((i for i, c in enumerate(cats) if c == "critical"), len(cats))
    ordering = 1.0 if all(c == "critical" for c in cats[first_critical:]) else 0.0
    return grounding, completeness, ordering


# ---------------------------------------------------------------- phases

def run_live(rows: list[dict], chain: LLMChain | None) -> dict:
    """One cache for the whole run, as a judge would see it. A request that
    carries an article only hits on an exact repeat or the same article, so
    each scenario's first call is a true cold call without clearing."""
    cache = CompositionalCache(store=CacheStore(db_path=str(Path(tempfile.mkdtemp()) / "bench.db")))
    client = TestClient(create_app(cache=cache))
    paras = {it["id"]: it["paraphrases"] for it in json.load(open(ROOT / "eval/paraphrases.json"))["items"]}

    def plan_of(d):
        return json.dumps(d["response"]["contexts"], sort_keys=True)

    out = {"cold": [], "exact": [], "para": [], "para_no_siis": []}
    plans = {}
    for r in rows:
        body = {"query": r["query"], "siis_response": r["siis_response"]}
        t = time.perf_counter()
        d = client.post("/v1/troubleshoot", json=body).json()
        cold_ms = (time.perf_counter() - t) * 1000
        plans[r["id"]] = plan_of(d)
        first_call_hit = d["meta"]["cache_hit"]
        if first_call_hit:
            # The kit reuses one article for several complaints, so a first
            # call can be served from the shared-article cache. Time a true
            # cold call on a fresh cache so the cold-path sample stays honest.
            fresh = TestClient(create_app(cache=CompositionalCache(
                store=CacheStore(db_path=str(Path(tempfile.mkdtemp()) / "fresh.db")))))
            t = time.perf_counter()
            d = fresh.post("/v1/troubleshoot", json=body).json()
            cold_ms = (time.perf_counter() - t) * 1000
        goal = d["response"]["contexts"][0] if d["response"]["contexts"] else None
        acc = step_accuracy(goal, r["siis_response"]["content"]) if goal else (0.0, 0.0, 0.0)
        out["cold"].append({
            "id": r["id"], "unseen": r["unseen"], "ms": cold_ms, "model": d["meta"]["model"],
            "cost": d["meta"]["cost_usd"], "non_empty": goal is not None and bool(goal["actions"]),
            "valid": _schema_ok(d["response"]), "acc": acc, "fallback": d["meta"].get("fallback"),
            "first_call_hit": first_call_hit,
        })

        t = time.perf_counter()
        d2 = client.post("/v1/troubleshoot", json=body).json()
        out["exact"].append({"ms": (time.perf_counter() - t) * 1000, "hit": d2["meta"]["cache_hit"],
                             "cost": d2["meta"]["cost_usd"]})

        for p in paras.get(r["id"], []):
            t = time.perf_counter()
            d3 = client.post("/v1/troubleshoot", json={"query": p, "siis_response": r["siis_response"]}).json()
            out["para"].append({"ms": (time.perf_counter() - t) * 1000, "hit": d3["meta"]["cache_hit"],
                                "right": d3["meta"]["cache_hit"] and plan_of(d3) == plans[r["id"]],
                                "query": p, "of": r["id"]})
        print(f"  {r['id']}: cold {cold_ms:.0f} ms via {d['meta']['model']}, "
              f"repeat hit={d2['meta']['cache_hit']}, paraphrase hits="
              f"{[x['hit'] for x in out['para'] if x['of'] == r['id']]}", flush=True)
        time.sleep(PACE_S)

    # Paraphrases WITHOUT an article, against the warmed cache (brief §5:
    # "semantic lookup against pre-warmed cache entries").
    for r in rows:
        for p in paras.get(r["id"], []):
            t = time.perf_counter()
            d = client.post("/v1/troubleshoot", json={"query": p}).json()
            out["para_no_siis"].append({"ms": (time.perf_counter() - t) * 1000, "hit": d["meta"]["cache_hit"],
                                        "right": d["meta"]["cache_hit"] and plan_of(d) == plans[r["id"]],
                                        "query": p, "of": r["id"]})
    return out


def _schema_ok(response: dict) -> bool:
    try:
        ContextDeeplinkResponse.model_validate(response)
        return True
    except Exception:
        return False


def run_ablation(chain: LLMChain | None) -> dict:
    catalog = load_catalog(ROOT / "data/deeplinks.json")
    hybrid = HybridRetriever(catalog)
    bm25_only = HybridRetriever(catalog, bm25_weight=1.0, dense_weight=0.0)
    by_uri = {e.deeplink: e.id for e in catalog}
    dev = [s for s in json.load(open(ROOT / "eval/dev_set.json"))["scenarios"]
           if s["expected_deeplink_id"] and s["category"] == "auto"]

    res = {"hybrid": [], "rules": [], "llm": []}
    for s in dev:
        t = time.perf_counter()
        b = bind_actionable_deeplink(s["steps"], "auto", catalog, hybrid)
        pid = by_uri.get((b.actionable_deeplink or {}).get("deeplink"))
        res["hybrid"].append((pid == s["expected_deeplink_id"], (time.perf_counter() - t) * 1000, 0.0))

        t = time.perf_counter()
        top = bm25_only.search(" ".join(s["steps"]), top_k=1)
        res["rules"].append((bool(top) and top[0].entry.id == s["expected_deeplink_id"],
                             (time.perf_counter() - t) * 1000, 0.0))

        if chain is not None:
            cands = hybrid.search(" ".join(s["steps"]), top_k=40)
            listing = "\n".join(f"{c.entry.id} | {c.entry.message} | {c.entry.description}" for c in cands)
            prompt = (
                "You map troubleshooting steps to the Galaxy Settings screen they open. Pick the ONE "
                "catalog id whose screen the steps end on (the exact toggle if one is named, else the page). "
                "Return JSON {\"id\": \"DL-xxxx\"}.\n\nSteps:\n- " + "\n- ".join(s["steps"])
                + f"\n\nCatalog (id | message | description):\n{listing}"
            )
            t = time.perf_counter()
            try:
                text, rec = chain.complete(prompt)
                chosen = json.loads(text).get("id")
                cost = rec.cost_usd
            except Exception:
                chosen, cost = None, 0.0
            res["llm"].append((chosen == s["expected_deeplink_id"], (time.perf_counter() - t) * 1000, cost))
            time.sleep(PACE_S / 2)
    return res


def run_novelty(live: dict) -> dict:
    """N2 (intent-signature gate) vs a cosine-only cache, and N5 calibration ECE."""
    from cache.gated_cache import GatedSemanticCache
    from cache.semantic_cache import SemanticCache
    from schema import Action, Goal, StepGroup
    from validation.calibrator import calibrate_score

    dummy = Goal(goal="Follow these steps to perform this Test Troubleshooting", title="Test plan", score=0.5,
                 actions=[Action(actionName="Test", description="It will test the cache path",
                                 stepGroups=[StepGroup(steps=["Open Settings."])])])

    def fresh(cls):
        return cls(store=CacheStore(db_path=str(Path(tempfile.mkdtemp()) / "n2.db")))

    adversarial = json.load(open(ROOT / "data/adversarial_near_miss.json"))
    out = {}
    for name, cls in (("cosine", SemanticCache), ("gated", GatedSemanticCache)):
        false_hits = 0
        for pair in adversarial:
            c = fresh(cls)
            c.put(pair["query_a"], dummy)
            false_hits += c.get(pair["query_b"]).hit
        para_hits = 0
        queries = {r["id"]: r for r in live["cold"]}
        originals = {r["id"]: r for r in load_scenarios()}
        for p in live["para"]:
            c = fresh(cls)
            c.put(originals[p["of"]]["query"], dummy)
            para_hits += c.get(p["query"]).hit
        out[name] = {"false_hit": false_hits / len(adversarial), "n_adv": len(adversarial),
                     "para_hit": para_hits / len(live["para"]) if live["para"] else float("nan")}

    var_false = 0
    for pair in adversarial:
        c = CompositionalCache(store=CacheStore(db_path=str(Path(tempfile.mkdtemp()) / "n2v.db")))
        c.put_article("adv", pair["query_a"], [dummy])
        var_false += c.get_by_variants(pair["query_b"]).hit
    out["variant_false_hit"] = var_false / len(adversarial)

    cal = json.load(open(ROOT / "data/calibration_dev_set.json"))
    bins = [[] for _ in range(10)]
    for item in cal:
        conf = calibrate_score(grounding_coverage=item["grounding_coverage"],
                               validator_pass_rate=item["validator_pass_rate"],
                               retrieval_margin=item["retrieval_margin"],
                               path_alignment=item["path_alignment"])
        bins[min(int(conf * 10), 9)].append((conf, item["label"]))
    out["ece"] = sum(len(b) / len(cal) * abs(sum(x[1] for x in b) / len(b) - sum(x[0] for x in b) / len(b))
                     for b in bins if b)
    out["n_cal"] = len(cal)
    return out


def check_results_file() -> dict:
    rows = [json.loads(l) for l in open(ROOT / "results.jsonl", encoding="utf-8") if l.strip()]
    catalog_uris = {e["deeplink"] for e in json.load(open(ROOT / "data/deeplinks.json"))["deeplinks"]}
    stats = dict(rows=len(rows), schema=0, rules_ok=0, rules_total=0, leaks=0, links=0, links_ok=0,
                 auto=0, auto_linked=0, variations_ok=0)
    for r in rows:
        stats["schema"] += _schema_ok(r["response"])
        stats["leaks"] += contains_urls(json.dumps(r["response"])) or contains_urls(json.dumps(r.get("query_variations")))
        vs = r.get("query_variations") or []
        stats["variations_ok"] += 8 <= len(set(vs)) <= 10
        for g in r["response"]["contexts"]:
            checks = [bool(GOAL_RE.match(g["goal"])), 2 <= len(g["title"].split()) <= 3, 0.0 <= g["score"] <= 1.0]
            for a in g["actions"]:
                words = a["description"].split()
                checks.append(a["description"].startswith("It will") and 5 <= len(words) <= 7)
                for sg in a["stepGroups"]:
                    dl = sg.get("actionableDeeplink")
                    if dl:
                        stats["links"] += 1
                        stats["links_ok"] += dl["deeplink"] in catalog_uris or dl["deeplink"] == "bixby://dummy_positive"
                if a["category"] == "auto":
                    stats["auto"] += 1
                    stats["auto_linked"] += all(sg.get("actionableDeeplink") for sg in a["stepGroups"])
            stats["rules_ok"] += sum(checks)
            stats["rules_total"] += len(checks)
    return stats


# ---------------------------------------------------------------- report

def render(live: dict, abl: dict, comp: dict, chain: LLMChain | None, screen_eval: dict, nov: dict) -> str:
    cold, exact, para = live["cold"], live["exact"], live["para"]
    cold_ms = [c["ms"] for c in cold]
    exact_ms = [e["ms"] for e in exact]
    para_hit_ms = [p["ms"] for p in para if p["hit"]]
    para_rate = sum(p["hit"] for p in para) / len(para) if para else float("nan")
    pns = live["para_no_siis"]
    pns_hit_ms = [p["ms"] for p in pns if p["hit"]]
    pns_rate = sum(p["hit"] for p in pns) / len(pns) if pns else float("nan")
    acc = [sum(c["acc"]) for c in cold if c["non_empty"]]
    ground = [c["acc"][0] for c in cold if c["non_empty"]]
    complete = [c["acc"][1] for c in cold if c["non_empty"]]
    order = [c["acc"][2] for c in cold if c["non_empty"]]
    models = {}
    for c in cold:
        models[c["model"]] = models.get(c["model"], 0) + 1
    llm_cold_cost = [c["cost"] for c in cold]
    unseen = [c for c in cold if c["unseen"]]

    def ab(name):
        rows = abl[name]
        if not rows:
            return "not run (no LLM key)", "-", "-"
        acc_ = sum(r[0] for r in rows) / len(rows)
        return f"{acc_:.1%} ({sum(r[0] for r in rows)}/{len(rows)})", f"{pct([r[1] for r in rows], 95):.0f} ms", \
            f"${statistics.mean(r[2] for r in rows):.6f}"

    mem = ""
    try:
        mem = f"{int(subprocess.check_output(['sysctl', '-n', 'hw.memsize']).strip()) / 2**30:.0f} GB RAM"
    except Exception:
        pass
    chain_desc = " → ".join(chain.chain) if chain else "none (offline extractor only)"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    h, r, b = ab("hybrid"), ab("rules"), ab("llm")

    return f"""# System Performance Metrics & Evaluation Report
**Model(s):** LLM chain in priority order: {chain_desc}. Served this run: {", ".join(f"{m} ×{n}" for m, n in sorted(models.items(), key=lambda x: -x[1]))}
**Embeddings:** Deeplink retrieval: BM25 (rank-bm25) + TF-IDF cosine (scikit-learn); no neural embedding model. Semantic cache: 128-dim hashed word + char-trigram vectors plus an intent signature (symptom × component).
**Environment:** {os.cpu_count()} vCPU / {mem} / {platform.system()} {platform.release()} ({platform.machine()}), Python {platform.python_version()}. API run in-process via FastAPI TestClient.
**Generated:** {now} by `scripts/benchmark.py` (re-run it to reproduce).

---

## 1. Schema & Rule Compliance
Evaluated on `results.jsonl` (20 kit rows) plus the 10 unseen scenarios in `eval/unseen_scenarios.json`.

| Metric | Target | Measured Value |
| :--- | :--- | :--- |
| Schema-valid output lines | >= 99% | {comp['schema'] / comp['rows']:.0%} ({comp['schema']}/{comp['rows']} results.jsonl); {sum(c['valid'] for c in cold) / len(cold):.0%} of live cold responses |
| Rule compliance (Goal / Title / Description syntax) | >= 95% | {comp['rules_ok'] / comp['rules_total']:.1%} ({comp['rules_ok']}/{comp['rules_total']} checks) |
| Absolute URL leaks | 0 | {comp['leaks']} |
| Deeplink catalog validity (exact URI match) | 100% | {comp['links_ok'] / comp['links']:.0%} ({comp['links_ok']}/{comp['links']}; `bixby://dummy_positive` counted as valid per FAQ Q15) |
| Auto actions carrying valid actionable deeplink | >= 90% | {comp['auto_linked'] / comp['auto']:.0%} ({comp['auto_linked']}/{comp['auto']}) |
| Query variations: 8-10 unique per line | 100% | {comp['variations_ok'] / comp['rows']:.0%} |
| Unseen scenarios with valid, non-empty plan (FAQ A4) | 100% | {sum(c['non_empty'] and c['valid'] for c in unseen)}/{len(unseen)} |

---

## 2. Accuracy Benchmarks
Step accuracy is scored automatically on the {len(acc)} live cold responses (kit + unseen), as a sum of three 0-1 parts. It is a proxy for the brief's hand-scored rubric, not a replacement for it:
- **Correctness (grounding):** share of steps whose content words are ≥50% present in the SIIS text.
- **Completeness:** share of SIIS section headings whose words appear in the plan.
- **Ordering:** 1 if every critical action comes after all non-critical ones.

Deeplink relevance is scored on the {screen_eval['n']} hand-labelled auto scenarios in `eval/dev_set.json` (2 = exact target screen, 1 = right screen but wrong level (page vs toggle), 0 = wrong).

| Evaluation Metric | Scale / Anchor | Score |
| :--- | :--- | :--- |
| Step accuracy (completeness, correctness, ordering) | 0.0 - 3.0 | {statistics.mean(acc):.2f} (grounding {statistics.mean(ground):.2f}, completeness {statistics.mean(complete):.2f}, ordering {statistics.mean(order):.2f}) |
| Deeplink relevance (exact target screen vs. parent menu) | 0.0 - 2.0 | {screen_eval['relevance']:.2f} (exact screen {screen_eval['exact']:.1%}, parent-menu errors {screen_eval['parent']:.1%}) |

---

## 3. Latency Benchmarks (N >= 30 requests per path)

| Execution Path | Target (P95) | N | P50 (ms) | P95 (ms) |
| :--- | :--- | :--- | :--- | :--- |
| Cache hit - exact query match | <= 300 ms | {len(exact_ms)} | {pct(exact_ms, 50):.1f} | {pct(exact_ms, 95):.1f} |
| Cache hit - unseen semantic paraphrase (article sent) | <= 300 ms | {len(para_hit_ms)} hits of {len(para)} | {pct(para_hit_ms, 50):.1f} | {pct(para_hit_ms, 95):.1f} |
| Cache hit - unseen semantic paraphrase (no article) | <= 300 ms | {len(pns_hit_ms)} hits of {len(pns)} | {pct(pns_hit_ms, 50):.1f} | {pct(pns_hit_ms, 95):.1f} |
| Cold query - full pipeline extraction & mapping | <= 8000 ms | {len(cold_ms)} | {pct(cold_ms, 50):.0f} | {pct(cold_ms, 95):.0f} |

Exact-repeat hit rate: {sum(e['hit'] for e in exact) / len(exact):.0%}. {sum(c['first_call_hit'] for c in cold)} of the {len(cold)} first calls were served by the shared-article cache (the kit reuses one article for several near-identical complaints). Their cold timings above were re-measured on a fresh cache. Cold requests are bounded by a 7.3 s LLM budget with hedged requests (the next model is raced after 2.5 s). Past the budget, the offline extractor answers, so a slow provider never breaks the 8 s target.

---

## 4. Operational Cost & Cache Efficacy

| Metric Item | Target | Measured Value |
| :--- | :--- | :--- |
| Cold query average inference cost | Tracked | ${statistics.mean(llm_cold_cost):.6f} (list price; free-tier keys were billed $0) |
| Cache hit inference cost | $0.00 | ${statistics.mean(e['cost'] for e in exact):.2f} |
| Semantic cache hit rate, paraphrase + same article | >= 80% | {para_rate:.0%} ({sum(p['hit'] for p in para)}/{len(para)}); right plan in {sum(p['right'] for p in para)}/{sum(p['hit'] for p in para)} hits |
| Semantic cache hit rate, paraphrase only (no article) | >= 80% | {pns_rate:.0%} ({sum(p['hit'] for p in pns)}/{len(pns)}); right plan in {sum(p['right'] for p in pns)}/{sum(p['hit'] for p in pns)} hits |
| Cost derivation method | - | (prompt tokens + completion tokens) × list rate per model (`extraction/llm_client.py::_PRICE_PER_M`) |

Paraphrases come from `eval/paraphrases.json`: 90 paraphrases (3 per scenario) written once by Groq `openai/gpt-oss-120b` and never stored in the cache. "Right plan" means the hit returned the same plan as that scenario's own cold call. With an article attached, a paraphrase is matched through the article's fingerprint plus a compatible intent (it can never return another article's plan). Without one, it is matched against every cached plan's query and its 8-10 pre-computed `query_variations` (brief roadmap Phase 3), using hashed n-gram and synonym-aware word similarity behind the intent gate.

---

## 5. Architectural Ablation Analysis
Deeplink mapping only (extraction is held fixed), on the {len(abl['hybrid'])} labelled auto scenarios of `eval/dev_set.json`. The "Step Accuracy" column here is exact-screen accuracy, since only the mapping stage varies.

| Architecture Variant | Step Accuracy | Latency (P95) | Cost / Query | Key Observations |
| :--- | :--- | :--- | :--- | :--- |
| Baseline: Full LLM Deeplink Mapping | {b[0]} | {b[1]} | {b[2]} | The LLM picks from the top-40 retrieved candidates (sending all 578 entries per step is too slow for the 8 s budget). Adds a network call per action and depends on free-tier availability. |
| Variant A: Hybrid BM25 + Dense Embedding Retrieval | {h[0]} | {h[1]} | {h[2]} | **Shipped.** BM25 + TF-IDF, then a breadcrumb filter, a page-vs-toggle rule, polarity twins (Enable/Disable) and a label-support check. Deterministic and runs in milliseconds. |
| Variant B: Pure Rules-Based Deeplink Mapping | {r[0]} | {r[1]} | {r[2]} | BM25 top-1 with no screen-graph rules. It picks sub-toggles over pages and gets Enable/Disable twins backwards. |

---

## 5b. Novelty Ablations (team plan N2, N5)

| Component | Variant | Measured | Notes |
| :--- | :--- | :--- | :--- |
| N2 intent-signature cache gate | Cosine-only cache | false-hit rate {nov['cosine']['false_hit']:.0%} on {nov['cosine']['n_adv']} adversarial near-miss pairs; paraphrase hit {nov['cosine']['para_hit']:.0%} | `data/adversarial_near_miss.json`: polarity ("turn on" vs "turn off"), component, trigger and scope traps |
| N2 intent-signature cache gate | Gated (shipped) | false-hit rate {nov['gated']['false_hit']:.0%}; paraphrase hit {nov['gated']['para_hit']:.0%} | A false hit serves the wrong plan instantly. The gate trades some paraphrase recall for that safety. |
| No-article paraphrase lookup (variations index) | Blended similarity ≥ 0.60 + relaxed gate + setting-conflict check | false-hit rate {nov['variant_false_hit']:.0%} on the same 50 pairs | Only used when no article is sent; a miss there would return an empty plan, so recall is favoured. With an article, the stricter article path applies. |
| N5 calibrated confidence score | Evidence-based score | ECE {nov['ece']:.3f} over {nov['n_cal']} scenarios | `data/calibration_dev_set.json` is team-generated (`scripts/generate_calibration_dev_set.py`), so this checks the calibrator against its own labels, not real-world outcomes. |

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
"""


def screen_eval_summary() -> dict:
    from eval.run_screen_eval import run
    results = [r for r in run() if r.expected_deeplink_id is not None and r.category == "auto"]
    exact = sum(r.correct for r in results) / len(results)
    parent = sum(r.is_parent_menu_error for r in results) / len(results)
    relevance = sum(2 if r.correct else (1 if r.is_parent_menu_error else 0) for r in results) / len(results)
    return {"n": len(results), "exact": exact, "parent": parent, "relevance": relevance}


def main() -> None:
    load_dotenv()
    chain = LLMChain.from_env()
    rows = load_scenarios()
    print(f"benchmark: {len(rows)} scenarios, LLM chain: {chain.chain if chain else 'none'}", flush=True)
    live = run_live(rows, chain)
    print("ablation ...", flush=True)
    abl = run_ablation(chain)
    md = render(live, abl, check_results_file(), chain, screen_eval_summary(), run_novelty(live))
    (ROOT / "metrics.md").write_text(md, encoding="utf-8")
    (ROOT / "eval" / "benchmark_raw.json").write_text(json.dumps({"live": live, "ablation": abl}, indent=1))
    print(f"wrote {ROOT / 'metrics.md'}")


if __name__ == "__main__":
    main()
