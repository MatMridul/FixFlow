# FixFlow — Smart Guided Troubleshooting Engine

> **Samsung PRISM GenAI Hackathon 3.0 · Theme 02**  
> *Translating colloquial, compound device complaints into grounded, self-verifying, one-tap troubleshooting plans in ≤2 ms.*

---

## 👥 Team & Submission Information

| Detail | Official Submission Value |
|:---|:---|
| **Submission Nomenclature** | `SRM_Claude's Plan_02` *(CollegeName_TeamName_ThemeNo)* |
| **Team Name** | **Claude's Plan** |
| **College / Institution** | **SRM** *(SRM Institute of Science and Technology)* |
| **Theme Track** | **Theme 02 — Smart Guided Troubleshooting Engine** |
| **Team Lead & Primary Member** | **Hemish Jain** (`hemishjain@gmail.com` / Lead Architect & Core Systems) |
| **Team Member** | **Mridul Mathur** (`mridulmathur2004@gmail.com` / Pipeline & Intelligence Engineer) |
| **GitHub Repository** | [https://github.com/MatMridul/FixFlow](https://github.com/MatMridul/FixFlow) |
| **Official Release Tag** | [`PRISM_GENAI_HACKATHON_Y2026`](https://github.com/MatMridul/FixFlow/releases/tag/PRISM_GENAI_HACKATHON_Y2026) |

---

## 🏆 Final Submission Deliverables Checklist

All required artifacts are committed, tagged under `PRISM_GENAI_HACKATHON_Y2026`, and present in the root directory:

| Item | Hackathon Requirement | Repository Path & Verified File | Status |
|:---|:---|:---|:---:|
| **Source Code** | Complete working prototype code on public GitHub | [`api/`](api/), [`catalog/`](catalog/), [`enrichment/`](enrichment/), [`cache/`](cache/), [`extraction/`](extraction/), [`resolution/`](resolution/), [`validation/`](validation/), [`frontend/`](frontend/), [`tests/`](tests/) | **VERIFIED (168/168 Tests Pass)** |
| **Presentation Deck** | PPT or PDF following `CollegeName_TeamName_ThemeNo` | [`SRM_Claude's Plan_02.pptx`](SRM_Claude's%20Plan_02.pptx)<br>[`SRM_Claude's Plan_02.pdf`](SRM_Claude's%20Plan_02.pdf)<br>*(Safe alias: [`SRM_Claudes_Plan_02.pptx`](SRM_Claudes_Plan_02.pptx) & [`CollegeName_TeamName_Submission.pptx`](CollegeName_TeamName_Submission.pptx))* | **VERIFIED (12 Slides Complete)** |
| **Demo Video** | Max 5 minutes (YouTube, Drive, or Repo link) | [`demo-video/FixFlow_Live_Walkthrough_1080p.mp4`](demo-video/FixFlow_Live_Walkthrough_1080p.mp4) (41.4s, 1080p 60fps Full HD, H.264)<br>*(See [Video Details](#-demo-video-specifications--analysis))* | **VERIFIED (Within 5-min limit)** |
| **AI Disclosure Form** | Completed official AI usage disclosure | [`SRM_Claude's Plan_02_AI_Disclosure.docx`](SRM_Claude's%20Plan_02_AI_Disclosure.docx)<br>*(Template copy: [`LangAI3.0_AI_Disclosure.docx`](LangAI3.0_AI_Disclosure.docx))* | **VERIFIED (Signed & Completed)** |
| **Documentation & README** | Reproducible setup, Docker, and architecture | [`README.md`](README.md), [`Dockerfile`](Dockerfile), [`requirements.txt`](requirements.txt) | **VERIFIED** |
| **Test & Eval Metrics** | Full test suite, results, & ablation metrics | [`results.json`](results.json), [`results.jsonl`](results.jsonl), [`metrics.md`](metrics.md) | **VERIFIED** |
| **Git Tag** | Release tag `PRISM_GENAI_HACKATHON_Y2026` | `git checkout tags/PRISM_GENAI_HACKATHON_Y2026` | **VERIFIED** |

---

## 🎥 Demo Video Specifications & Analysis

### 1. Video Length Compliance
- **Official Guideline Rule:** *"Demo video, max 5 minutes (YouTube or Drive link)"* (PDF Guidelines, Pages 11–13).
- **Video Duration:** **41.4 seconds** (`demo-video/FixFlow_Live_Walkthrough_1080p.mp4`).
- **Compliance Verdict:** **100% Compliant**. The guidelines mandate an upper bound of 5 minutes (`max 5 minutes`) with no minimum duration requirement.

### 2. Voiceover & Content Analysis
- **Guideline Requirement:** The hackathon documentation does **not mandate voiceover**. It requires a visual demonstration of the working prototype.
- **What the 41.4s Video Demonstrates:**
  1. **Real-time Query Input:** Typing compound colloquial issue: *"Screen flickers and the battery dies fast"*.
  2. **Instant Sub-2ms Retrieval:** Execution telemetry displaying **1.85ms P95 latency** and `$0.00` API cost via the compositional cache.
  3. **Deep Pipeline Trace:** Expanding the execution trace accordion to reveal multi-clause decomposition, hybrid BM25 retrieval scores, and screen graph resolution.
  4. **Live One UI 6.1 Simulator:** The phone interface immediately loads the resolved Settings screen, highlights the targeted diagnostic control, and animates the toggle switch state change.
- **Drive / YouTube Submission Link:** If submitting via the Google Form field requesting a URL, teams can upload `demo-video/FixFlow_Live_Walkthrough_1080p.mp4` directly to Google Drive or YouTube (Unlisted) and paste the link, in addition to having it in the repository.

---

## 🚀 Application Start & Execution Guide

### 1. System Requirements
- **Python:** 3.10, 3.11, or 3.12
- **Operating System:** Windows 10/11, macOS, or Linux
- **Node.js:** **NOT required**. The One UI 6.1 interactive web simulator is built in zero-dependency vanilla ES6+ and served directly by FastAPI.

---

### 2. Local Installation (Quick Start)

```bash
# 1. Clone repository
git clone https://github.com/MatMridul/FixFlow.git
cd FixFlow

# 2. Create and activate a Python virtual environment
python -m venv venv

# On Windows PowerShell:
venv\Scripts\Activate.ps1
# On Linux / macOS:
# source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

### 3. Environment Configuration (Optional LLM Keys)

FixFlow features a **deterministic offline SIIS extraction engine**. If you do not provide any API keys, the engine automatically uses its offline knowledge base and produces **100% schema-valid, accurate troubleshooting plans**.

To optionally enable live multi-model LLM generation:
```bash
cp .env.example .env
```
Edit `.env` with your API keys:
```env
GEMINI_API_KEY=your_gemini_key_here
MISTRAL_API_KEY=your_mistral_key_here
GROQ_API_KEY=your_groq_key_here
```
> **Security Guarantee:** `.env` is strictly gitignored. FixFlow contains zero hardcoded API keys.

---

### 4. Running the Web Application & One UI Simulator

Start the FastAPI application server:
```bash
uvicorn api.app:app --port 8000 --reload
```

Once started:
- 📱 **Interactive One UI 6.1 Phone Simulator:** Open [http://localhost:8000/app/](http://localhost:8000/app/) in your browser.
- 📖 **Interactive Swagger API Docs:** Open [http://localhost:8000/docs](http://localhost:8000/docs).
- 🩺 **System Health Check:** Open [http://localhost:8000/health](http://localhost:8000/health).

---

### 5. Running via Docker

You can containerize and run FixFlow instantly using Docker:

```bash
# Build Docker image
docker build -t fixflow .

# Run Docker container on port 8000
docker run -p 8000:8000 fixflow

# Access simulator at http://localhost:8000/app/
```

---

### 6. Executing Automated Tests

FixFlow includes an exhaustive test suite covering schema compliance, compositional caching, graph reranking, validation repair, and dual-scheme negotiation:

```bash
# Run the full test suite
pytest -q
```
**Result:** **168 passed in 4.32s (100% passing)**. Tests do not call external APIs and run completely offline.

---

### 7. Generating Benchmark Metrics & Results

```bash
# Generate official benchmark output files (results.jsonl & results.json)
python scripts/generate_results.py

# Evaluate screen matching accuracy against evaluation set
python -m eval.run_screen_eval

# Run full performance benchmark report (writes metrics.md)
python scripts/benchmark.py
```

---

## 📱 Interactive One UI 6.1 Simulator Walkthrough

When you visit `http://localhost:8000/app/`:

1. **Preset Scenarios or Freeform Queries:**
   - Click any of the pre-loaded benchmark scenario chips (e.g., *"Adaptive Brightness"*, *"Battery Drain"*, *"Camera Lines"*, *"Compound Issue"*).
   - Or type **ANY custom freeform problem** in colloquial English. FixFlow's hybrid BM25 auto-retriever indexes Samsung's reference documentation and finds matching guidance on the fly.
2. **Execute Resolution:**
   - Click **"Diagnose & Fix"**.
   - If previously requested, the query hits the **Compositional Gated Cache** in **1.5ms – 1.85ms** at **$0.00 cost**.
3. **Inspect the Execution Trace Accordion:**
   - Click **"🔬 View Pipeline Execution Trace"** to view:
     - **Intent Decomposition:** Discrete clause breakdown (`Domain`, `Component`, `Symptom`, `Polarity`).
     - **Hybrid Retrieval Scores:** BM25 + TF-IDF scores over candidate articles.
     - **Screen Resolution:** Candidate screens evaluated with similarity distances and graph depths.
4. **Live Device Execution:**
   - The right side of the screen displays a virtual Galaxy S24 running One UI 6.1.
   - Clicking an action immediately opens the target Settings screen, displays the breadcrumb navigation path, highlights the active toggle, and simulates the setting change.

---

## 🔄 Dual-Scheme Engine & 25-Sep Kit Compatibility

FixFlow supports **both** deeplink specifications across the hackathon lifecycle:

| Scheme | Target Ecosystem | Prefix Example | Active By Default |
|:---|:---|:---|:---:|
| **`voiceassist://`** | **Official 25-Sep Final Evaluation Kit** (TechCorp/Nexa catalog, 578 masked links) | `voiceassist://masked/act/b3ed3ed663` | **YES** |
| **`bixby://`** | **Milestone 1 Kit** (Samsung One UI Settings catalog) | `bixby://settings/display/brightness` | Supported on demand |

### Dynamic Scheme Negotiation
FixFlow auto-detects the catalog scheme from `data/deeplinks.json`, and allows callers to switch schemes dynamically:
- **HTTP Query Parameter:** `POST /v1/troubleshoot?scheme=bixby`
- **HTTP Request Header:** `X-Deeplink-Scheme: bixby` (or `voiceassist`)
- **Environment Variable:** `FIXFLOW_DEEPLINK_SCHEME=bixby`
- Both catalog versions (`deeplinks.json` and `deeplinks_bixby.json`) are preserved in the repository.

---

## 🧠 System Architecture & Core Novelties

```
                   Colloquial User Problem Entry
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│ 0. Enrichment & Multi-Intent Segmentation (N1 + N2)          │
│    • Regex-based syntactic clause splitter                   │
│    • Intent Signature extractor: Domain, Component, Symptom, │
│      Polarity ('draining' vs 'not charging'), Trigger        │
└───────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│ 1. Compositional Gated Semantic Cache (N1 + N2)              │
│    • Sub-intents checked independently against SQLite WAL    │
│    • Exact matches return in ≤2 ms ($0.00 API cost)          │
│    • Polarity Gating blocks false hits on near-miss queries  │
└───────────────┬──────────────────────────────┬───────────────┘
                │ Full Hit                     │ Cache Miss
                ▼                              ▼
     Compose Cached Goals           ┌──────────────────────────┐
                │                   │ 2. SIIS Knowledge Auto-  │
                │                   │    Retriever             │
                │                   │    • BM25Okapi + TF-IDF  │
                │                   │      Cosine Retrieval    │
                │                   └──────────┬───────────────┘
                │                              │
                │                              ▼
                │                   ┌──────────────────────────┐
                │                   │ 3. Structure Extractor   │
                │                   │    • Schema-constrained  │
                │                   │      hedged LLM / Offline│
                │                   │    • N5 Provenance filter│
                │                   └──────────┬───────────────┘
                │                              │
                │                              ▼
                │                   ┌──────────────────────────┐
                │                   │ 4. Screen Graph Reranker │
                │                   │    • Graph traversal     │
                │                   │    • 1 Action = 1 Screen │
                │                   └──────────┬───────────────┘
                │                              │
                │                              ▼
                │                   ┌──────────────────────────┐
                │                   │ 5. Closed-Loop Validator │
                │                   │    • Binds validation link│
                │                   │    • Repair loop & score │
                │                   └──────────┬───────────────┘
                │                              │
                ▼                              ▼
         Write Cache ──────────────────────────┘
                │
                ▼
  Theme 02 Validated Response + Diagnostic Telemetry
```

### The 5 Novelties
1. **N1 — Compositional Multi-Intent Cache:** Splits compound complaints (*"screen flickers and battery dies fast"*), resolves sub-intents independently, and composes goals without LLM invocations.
2. **N2 — Intent-Signature Polarity Gating:** Extracts polarity signatures to prevent confident false-hits on semantic near-misses (*"battery draining"* vs *"battery not charging"*).
3. **N3 — Settings Screen Graph Path Reranker:** Ranks candidate settings screens using hierarchical graph shortest-paths, eliminating parent-menu collisions.
4. **N4 — Closed-Loop Self-Verifying Plans (`validationDeeplink`):** Attaches validation deeplinks with expected toggle states (`boolean`, `condition`, `value`) allowing the client to verify device state and skip satisfied actions.
5. **N5 — Step Provenance & Calibrated Scoring:** Enforces 100% factual grounding by matching steps against SIIS text sentences, rejecting ungrounded hallucinated steps.

---

## 📊 Evaluation & Benchmark Results

| Metric | Hackathon Requirement | FixFlow Performance | Verification Source |
|:---|:---|:---|:---:|
| **Cache Hit Latency (P95)** | ≤ 300 ms | **1.85 ms** | Benchmark test (30 iterations) |
| **Cold Path Latency (P95)** | Reasonable | **2,840 ms** (LLM) / **12 ms** (Offline) | Live benchmark suite |
| **Schema Compliance** | 100% Valid | **100.0%** (0 schema violations) | `pytest tests/test_validation.py` |
| **Automated Tests** | Comprehensive | **168 / 168 Passing (100%)** | `pytest -q` |
| **API Cost on Repeat Inquiries** | Cost Reduction | **$0.0000 USD** | Cache telemetry |
| **Un-Vibe Code Audit** | Production Standards | **19 / 19 Rules Satisfied** | Full error boundaries & accessibility |

---

## 📄 License & Attribution
Developed by team **Claude's Plan** (`SRM_Claude's Plan_02`) for the **Samsung PRISM GenAI Hackathon 3.0**.  
All rights reserved.
