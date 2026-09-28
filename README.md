# FixFlow — Smart Guided Troubleshooting Engine

> **Samsung PRISM GenAI Hackathon · Theme 02**  
> *Turning vague, compound device complaints into grounded, self-verifying, one-tap troubleshooting plans.*

---

## 🚀 Overview

**FixFlow** is an intelligent device troubleshooting engine designed to bridge the gap between colloquial, vague user complaints and exact, executable device actions. Built strictly against the Samsung PRISM Theme 02 specification, FixFlow extracts structured troubleshooting goals and step groups from reference technical documentation (SIIS) and maps every action deterministically to verified in-app Settings deeplinks.

### Core Philosophy
> **"SIIS text decides *what* to do. The catalog decides *where* it happens. The LLM only translates between them."**

---

## 🧠 Key Novelties & Architecture

```
POST /v1/troubleshoot  { query, siis_response? }
          │
          ▼
┌──────────────────────────────┐
│ 0. Enrichment                │  • Clause segmentation (N1)
│                              │  • Intent signature per clause (N2)
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐   Full Hit  ──► Compose Goals ──► Response (≤300ms)
│ 1. Compositional Gated Cache │   Partial   ──► Cold path for missing clauses only
│    (N1 + N2)                 │   Miss + No SIIS ──► Fallback: "no_siis_context"
└──────────────┬───────────────┘
               ▼  (Cold path, grounded in SIIS text)
┌──────────────────────────────┐
│ 2. Structure Extraction      │  • LLM with schema-constrained output
│                              │  • Step ↔ SIIS provenance filter (N5)
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ 3. Screen Resolution         │  • Hybrid retrieval over catalog metadata
│    (N3)                      │  • Settings Screen Graph path reranking
│                              │  • One Action = One Screen deduplication
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ 4. Verification Binding (N4) │  • Attach `validationDeeplink` from catalog
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ 5. Validator + Repair Loop   │  • Strict schema, word counts, casing, goal syntax
│                              │  • Regex URL scrubbing & catalog whitelist
│                              │  • Ordering: auto → critical (last), manual (no deeplink)
│                              │  • Calibrated score & `no_match` gate (N5)
└──────────────┬───────────────┘
               ▼
       Write Cache ──► Final Response + Meta Block
```

### 🌟 Differentiators

1. **N1 — Compositional Multi-Intent Cache:** Splits compound complaints (e.g. *"Screen flickers and battery dies fast"*), looks up sub-intents independently, and composes cached goals without calling LLMs.
2. **N2 — Intent-Signature Gated Cache:** Extracts discrete intent signatures (domain, component, symptom, polarity, trigger) to prevent confident false-hits on near-miss queries (*"battery draining"* vs *"battery not charging"*).
3. **N3 — Path-Constrained Screen Resolution:** Employs a Settings Screen Graph constructed from catalog hierarchy to eliminate parent-menu matching errors.
4. **N4 — Self-Verifying Plans (`validationDeeplink`):** Attaches validation rules and expected target states to turn instructions into a closed-loop execution model capable of auto-skipping already-satisfied settings.
5. **N5 — Calibrated Scoring & Step Provenance:** Programmatically aligns extracted steps to reference sentences to eliminate hallucinations and produces evidence-calibrated confidence scores.

---

## 📁 Repository Structure

```text
FixFlow/
├── api/            # FastAPI service exposing /v1/troubleshoot and /health
├── catalog/        # Deeplink compiler & Settings Screen Graph (N3)
├── enrichment/     # Clause splitter (N1) & Intent signature extractor (N2)
├── cache/          # Gated and compositional semantic cache
├── extraction/     # Schema-constrained LLM extractor & provenance filter (N5)
├── resolution/     # Hybrid retriever (BM25 + Dense) & path reranker (N3)
├── validation/     # Programmatic validators, repair loop, and scoring
├── eval/           # Test sets, evaluation harness & benchmark runners
├── frontend/       # Interactive demo interface
├── data/           # Supplied starter assets (queries, deeplinks, SIIS responses)
├── docs/           # Specifications, idea documents, and architecture notes
├── results.jsonl   # Benchmark outputs
├── metrics.md      # Performance & ablation report
├── Dockerfile      # Containerization definition
└── README.md       # Project overview & documentation
```

---

## 📋 API Contract

Requests and responses strictly conform to the Theme 02 schema:

```json
{
  "query": "Screen flickers and the battery dies fast",
  "query_variations": ["...8 to 10 paraphrases..."],
  "response": {
    "contexts": [
      {
        "goal": "Follow these steps to perform this Display Troubleshooting",
        "title": "Screen flicker",
        "score": 0.94,
        "actions": [
          {
            "actionName": "Adjust Screen Brightness",
            "description": "It will stabilise your display brightness",
            "category": "auto",
            "stepGroups": [
              {
                "steps": ["Open Settings.", "Tap on Display.", "Adjust Brightness."],
                "actionableDeeplink": {
                  "deeplink": "intent:#Intent;action=android.settings.DISPLAY_SETTINGS;end",
                  "description": "Display Settings",
                  "message": "Open Display Settings"
                },
                "validationDeeplink": {
                  "deeplink": "intent:#Intent;action=android.settings.DISPLAY_SETTINGS;end",
                  "key": "screen_brightness_mode",
                  "resultType": "boolean",
                  "condition": "equal",
                  "value": "true"
                }
              }
            ]
          }
        ]
      }
    ]
  },
  "meta": {
    "latency_ms": 14,
    "cache_hit": true,
    "model": "cache-compositional-v1",
    "cost_usd": 0.0
  }
}
```

---

## 🛠️ Quick Start

### Prerequisites
- Python 3.10+ (no Node needed: the demo UI is plain HTML/JS served by the API)

### Installation
```bash
git clone https://github.com/MatMridul/FixFlow.git
cd FixFlow
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### LLM keys (optional)
```bash
cp .env.example .env              # then fill GEMINI_API_KEY, MISTRAL_API_KEY and/or GROQ_API_KEY
```
`.env` is gitignored; never commit keys. Models are tried in order
gemini-2.5-flash (thinking off) → mistral-small-latest → ministral-8b-latest → Groq gpt-oss-120b,
with a 7.3 s total budget (cold-path gate is 8 s). Override with `LLM_CHAIN`. A model that hits its quota is skipped for 15 minutes.
With no keys, FixFlow uses its offline SIIS extractor, and every response stays schema-valid.

### Run
```bash
uvicorn api.app:app --port 8000
# Demo UI:      http://localhost:8000/app/
# Health:       GET  /health
# Troubleshoot: POST /v1/troubleshoot   (add ?debug=true for the pipeline trace)
# Scenarios:    GET  /v1/scenarios
```

### Docker
```bash
docker build -t fixflow .
docker run --env-file .env -p 8000:8000 fixflow
```

### Tests, results, eval
```bash
pytest -q                               # LLM disabled in tests
python scripts/generate_results.py      # writes results.jsonl / results.json
python -m eval.run_screen_eval          # deeplink screen accuracy -> metrics.md
```

---

## 📄 License
This project is developed for the **Samsung PRISM GenAI Hackathon**.
