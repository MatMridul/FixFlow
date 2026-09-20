# Samsung PRISM GenAI Hackathon --- Idea Source of Truth

## Working Title

# ATLAS Device Intelligence

### Product: FixFlow

**One-line pitch:**\
\> A world-model-powered troubleshooting engine that turns vague device
complaints into grounded, validated, executable fixes.

**Hackathon Track:** Theme 02 --- Smart Guided Troubleshooting Engine

**Status:** Working concept / source of truth for team ideation\
**Important:** "ATLAS-class system" is **our architectural philosophy**,
not an official Samsung PRISM term.

------------------------------------------------------------------------

# 1. Why We Are Choosing Theme 02

The Samsung PRISM GenAI Hackathon has five themes:

1.  Agentic Code Intelligence
2.  Smart Guided Troubleshooting
3.  Teachable Voice Automation
4.  Streaming Live RAG
5.  Interruptible Real-Time Agents

We recommend **Theme 02: Smart Guided Troubleshooting Engine**.

The official problem asks us to turn vague device complaints into
technical queries, produce ordered troubleshooting actions as structured
JSON, map actions to exact in-app Settings deeplinks, support a reusable
mapping for 10k+ scenarios, and provide a fast-path cache targeting
sub-300 ms responses.

The track is a particularly strong fit because it lets us demonstrate:

-   LLM-based language understanding
-   retrieval
-   structured reasoning
-   knowledge/world modeling
-   deterministic validation
-   action/deeplink grounding
-   caching and latency optimization
-   REST API engineering
-   measurable accuracy and cost
-   a polished interactive demo

The goal is **not** to build another generic chatbot.

The goal is to build an actual **device intelligence system**.

------------------------------------------------------------------------

# 2. Product Concept --- FixFlow

## The user experience

A user says something vague such as:

> "My phone gets really hot, the battery dies quickly, and I think some
> app is running in the background."

Instead of making the user search support articles or manually navigate
Settings, FixFlow:

1.  Understands the complaint.
2.  Converts it into a technical representation.
3.  Identifies symptoms, possible causes, and relevant evidence.
4.  Retrieves supported troubleshooting actions.
5.  Reasons over those candidate actions.
6.  Validates the proposed actions against a trusted action catalog.
7.  Sequences them into a safe troubleshooting plan.
8.  Returns the exact supported Settings deeplinks.
9.  Presents the result as one-tap actions.

Example:

``` text
User complaint
    ↓
"Battery drains fast + phone gets hot"
    ↓
Technical interpretation
    ↓
Possible background activity
    ↓
Retrieve supported actions
    ↓
Rank / reason / validate
    ↓
1. Check Battery Usage
2. Check Background Usage
3. Restrict offending application
    ↓
Exact Settings deeplink
    ↓
ONE-TAP FIX
```

------------------------------------------------------------------------

# 3. The ATLAS-Class Philosophy

## What does "ATLAS-class" mean here?

This is our internal architectural concept.

The existing ATLAS project philosophy is based on the idea that an
intelligent system should not merely retrieve isolated answers. It
should maintain a **structured model of the world**, including entities,
relationships, dependencies, constraints, and state, and reason over
that structure.

For this hackathon, we translate that philosophy from a financial world
into a **device world**.

### Traditional AI troubleshooting

``` text
Complaint
    ↓
LLM
    ↓
Instructions
```

### ATLAS-class troubleshooting

``` text
Complaint
    ↓
Understand
    ↓
Ground in Device World Model
    ↓
Retrieve evidence / candidate actions
    ↓
Reason over relationships
    ↓
Validate against trusted catalog
    ↓
Generate executable troubleshooting plan
    ↓
Exact Settings action
```

The important idea is:

> **Do not ask the LLM to memorize how the device works. Give it a
> structured model of the device and let it reason over that model.**

------------------------------------------------------------------------

# 4. ATLAS Does NOT Mean "Add a Giant Knowledge Graph"

This is a critical engineering principle.

We should **not** add a graph simply because it sounds sophisticated.

The question must always be:

> **Why does this architecture improve the result?**

If a simple combination of:

-   embeddings
-   BM25
-   metadata
-   reranking
-   deterministic validation

performs equally well, then the graph/world-model layer should be
simplified.

Therefore we should experimentally compare:

### Baseline A

Embedding retrieval

### Baseline B

BM25 + embeddings + Reciprocal Rank Fusion

### ATLAS version

Hybrid retrieval + structured device relationships + LLM reasoning +
deterministic validation

Keep the world-model components that demonstrate measurable value.

This is especially important because the hackathon rewards working
functionality and technical feasibility, not architectural complexity
for its own sake.

------------------------------------------------------------------------

# 5. Device World Model

The core conceptual layer is a **Device World Model**.

It should represent more than documents.

## Entities

Potential entity types:

``` text
Device
Subsystem
Symptom
Condition
Cause
Diagnostic
Evidence
Action
Setting
Prerequisite
Risk
```

## Relationships

Potential relationships:

``` text
SYMPTOM
    └── indicates ──> CONDITION

CONDITION
    └── possibly_caused_by ──> CAUSE

CAUSE
    └── diagnosed_by ──> DIAGNOSTIC

DIAGNOSTIC
    └── requires ──> ACTION

ACTION
    └── opens ──> SETTING

ACTION
    └── requires ──> PREREQUISITE

ACTION
    └── has_risk ──> RISK
```

Example:

``` text
"Battery drains quickly"
        │
        ├── indicates → Excessive Power Consumption
        │
        ├── may be caused by → Background Activity
        │
        ├── may be caused by → Display Usage
        │
        └── may be caused by → Network Activity

Background Activity
        │
        └── diagnosed_by → Battery Usage

Battery Usage
        │
        └── leads_to → App Battery Settings
                            │
                            └── exact Settings deeplink
```

The graph is useful because it allows the system to reason about
relationships rather than simply retrieving semantically similar text.

------------------------------------------------------------------------

# 6. The Most Important Design Principle

# LLM proposes. Catalog disposes.

The LLM is responsible for:

-   understanding natural language
-   normalization
-   query expansion
-   identifying symptoms/entities
-   reasoning over retrieved candidates
-   selecting appropriate action IDs
-   producing structured plans

The LLM is **not** the source of truth for executable actions or
deeplinks.

The trusted catalog is responsible for:

-   valid action IDs
-   descriptions
-   categories
-   supported deeplinks
-   action hierarchy
-   sequencing constraints
-   manual vs actionable classification

Example:

``` text
LLM
 ↓
"I think the user should inspect battery usage."
 ↓
ACTION_BATTERY_USAGE
 ↓
Trusted Action Catalog
 ↓
Exact validated deeplink
```

If the LLM invents an action:

``` text
"Clear hidden system cache"
```

but that action does not exist in the catalog:

``` text
REJECT
```

Do not allow hallucinated actions to reach the user.

------------------------------------------------------------------------

# 7. Why This Architecture Is Strong

It separates:

### Language intelligence

"What does the user mean?"

from:

### World knowledge

"What does this device support?"

from:

### Execution truth

"What action can actually be performed?"

This produces a system that is more:

-   grounded
-   explainable
-   deterministic
-   testable
-   scalable
-   defensible to an engineering jury

------------------------------------------------------------------------

# 8. Proposed System Architecture

``` text
                         USER
                           │
                           ▼
                ┌────────────────────┐
                │ Query Enrichment   │
                │                    │
                │ Complaint →        │
                │ technical query    │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │ Hybrid Retrieval   │
                │                    │
                │ Dense + BM25       │
                │ + metadata         │
                └─────────┬──────────┘
                          │
                       Top-K
                          │
                          ▼
                ┌────────────────────┐
                │ Device World Model │
                │                    │
                │ Symptoms           │
                │ Causes             │
                │ Evidence           │
                │ Actions            │
                │ Constraints        │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │ LLM Planner        │
                │                    │
                │ Select ACTION IDs  │
                │ + reasoning        │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │ Deterministic      │
                │ Validator          │
                │                    │
                │ existence          │
                │ category           │
                │ sequence           │
                │ deeplink           │
                │ hallucination      │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │ Action Catalog     │
                │                    │
                │ Exact validated    │
                │ Settings mapping   │
                └─────────┬──────────┘
                          │
                          ▼
                    ONE-TAP FIX
```

------------------------------------------------------------------------

# 9. Pipeline in Detail

## Stage 0 --- Catalog Compiler

The supplied Theme 02 starter assets include structured inputs such as:

-   `queries.json`
-   `sis_responses.json`
-   `deeplinks.json`
-   `bixby` placeholder/action handling
-   `samples/`
-   `schema.py`

The first implementation task should be to inspect the real files and
build a normalized internal action catalog.

Potential normalized schema:

``` json
{
  "action_id": "BATTERY_USAGE",
  "topic": "Battery",
  "title": "Check Battery Usage",
  "description": "...",
  "category": "standard",
  "parent_action": "...",
  "deeplink": "...",
  "prerequisites": [],
  "keywords": [],
  "embedding": "..."
}
```

The actual fields must follow the supplied Theme 02 schema. Do not
invent or violate required fields.

------------------------------------------------------------------------

# 10. Stage 1 --- Query Enrichment

Input:

> "My phone gets hot and battery disappears really fast."

Possible normalized representation:

``` json
{
  "device": "smartphone",
  "topic": "battery",
  "symptoms": [
    "rapid battery drain",
    "device overheating"
  ],
  "entities": [],
  "technical_query": "investigate excessive battery consumption and background activity",
  "query_variations": [
    "battery draining quickly",
    "rapid battery drain",
    "phone battery dies fast",
    "background battery usage"
  ]
}
```

This is a retrieval representation, not the final answer.

The purpose is to bridge the gap between colloquial complaints and
technical catalog language.

------------------------------------------------------------------------

# 11. Stage 2 --- Hybrid Retrieval

Use two complementary retrieval signals:

## Dense retrieval

Captures semantic similarity.

Example:

``` text
"battery disappears insanely quickly"
```

can match:

``` text
"rapid battery drain"
```

## Sparse retrieval / BM25

Captures exact technical terms and keyword overlap.

Then combine them with Reciprocal Rank Fusion or another simple
rank-fusion method.

``` text
                 Query
                   │
          ┌────────┴────────┐
          ↓                 ↓
       Dense              BM25
          │                 │
          └────────┬────────┘
                   ↓
              Rank Fusion
                   ↓
                Top-K
```

This should be benchmarked against simpler baselines.

------------------------------------------------------------------------

# 12. Stage 3 --- World-Model Grounding

Retrieved candidates are connected to the relevant device concepts.

Example:

``` text
Symptom:
Battery drain

Potential causes:
- Background activity
- Display usage
- Network activity

Candidate diagnostics:
- Battery usage
- Background usage

Candidate actions:
- Inspect battery usage
- Restrict background activity
```

The world model lets us reason about why an action is relevant rather
than simply whether its text is similar.

------------------------------------------------------------------------

# 13. Stage 4 --- LLM Structured Planner

The planner receives:

-   normalized user intent
-   relevant world-model context
-   top retrieved actions
-   action constraints

It outputs **action IDs**, not URLs.

Example:

``` json
{
  "goal": "Battery Troubleshooting",
  "actions": [
    {
      "action_id": "BATTERY_USAGE",
      "reason": "Identify applications consuming excessive battery."
    },
    {
      "action_id": "BACKGROUND_USAGE",
      "reason": "Investigate unrestricted background activity."
    }
  ]
}
```

The planner should be forced into a strict schema.

------------------------------------------------------------------------

# 14. Stage 5 --- Deterministic Validation

This layer is mandatory.

Validate:

### 1. Action existence

Does every action ID exist?

### 2. Schema compliance

Does the response satisfy the required output contract?

### 3. Category rules

Respect the catalog's distinction between:

-   standard
-   critical
-   manual

### 4. Sequence rules

Actions should follow valid troubleshooting hierarchy.

### 5. Deeplink integrity

The URL/deeplink must come from the trusted catalog.

### 6. Hallucination protection

Any unsupported action is rejected.

### 7. Manual intervention

If an issue requires physical intervention, do not fabricate an in-app
action.

Example:

``` text
User:
"My battery is physically swollen."

System:
This requires physical intervention.
No in-app action is available.
Please seek appropriate service.
```

------------------------------------------------------------------------

# 15. Stage 6 --- Fast Path

The official Theme 02 requirements call for a fast-path cache with a
target of under 300 ms.

Proposed architecture:

``` text
Request
   │
   ▼
Query fingerprint
   │
   ▼
Cache lookup
   │
   ├── HIT ──→ validated plan → response
   │
   └── MISS
          │
          ▼
      full pipeline
          │
          ▼
    validate result
          │
          ▼
      cache result
```

The cache should preferably operate on normalized/semantic queries
rather than only exact strings.

Potentially:

``` text
"battery dying quickly"

≈

"battery drains really fast"

≈

"phone battery doesn't last"
```

But semantic-cache behavior must be validated carefully to avoid
returning an inappropriate plan.

------------------------------------------------------------------------

# 16. Session State

The world model can also maintain **session-scoped troubleshooting
state**.

Example:

### Turn 1

User:

> "My battery is draining fast."

State:

``` text
Battery drain: HIGH
Suspected causes:
- background activity
- display usage
- network activity
```

### Turn 2

User:

> "It started after I installed Instagram."

Update:

``` text
Recent installation:
Instagram

Suspected cause:
Instagram background activity ↑
```

### Turn 3

User:

> "It also gets hot when I'm not using it."

Update:

``` text
Battery drain: HIGH
Overheating: HIGH
Idle activity: HIGH
Recent installation: Instagram

Priority hypothesis:
Background application activity
```

The system should refine the existing state instead of treating every
turn as an unrelated question.

The state should remain session-scoped, consistent with the track
constraints.

------------------------------------------------------------------------

# 17. Product / Demo Experience

The demo should not look like:

``` text
POST /troubleshoot
200 OK
{
   ...
}
```

We should build a polished interactive interface.

## Proposed UI

### Left --- Conversation

``` text
User

"My phone gets really hot and
the battery dies in a few hours."
```

### Center --- ATLAS Device World Model

``` text
          BATTERY DRAIN
               │
       ┌───────┴────────┐
       ↓                ↓
 Background          Display
 Activity             Usage
       │
       ↓
 Recent App
       │
       ↓
 High background
 consumption
```

As new user information arrives, the graph/state should visually update.

### Right --- Recommended Fix

``` text
BATTERY HEALTH

01  Check Battery Usage
    Identify high-consumption apps

    [ OPEN SETTINGS → ]

02  Check Background Usage
    Find unrestricted background activity

    [ OPEN SETTINGS → ]

03  Restrict App
    Reduce unnecessary background usage

    [ OPEN SETTINGS → ]
```

This turns the architecture into a visible product story.

------------------------------------------------------------------------

# 18. Demo Story

The ideal demo should show the entire chain:

``` text
Vague complaint
       ↓
AI understanding
       ↓
Technical query
       ↓
Retrieved candidates
       ↓
World-model reasoning
       ↓
Validated action plan
       ↓
Exact Settings action
```

Then show a second case where the system refuses to invent an
unsupported action.

This demonstrates both **capability and safety/grounding**.

------------------------------------------------------------------------

# 19. What We Should NOT Build

Avoid unnecessary complexity:

-   multi-agent swarm
-   LangGraph everywhere
-   many LLM calls without measurable benefit
-   Kubernetes
-   unnecessary microservices
-   autonomous browser automation
-   huge cloud architecture
-   elaborate infrastructure that does not improve evaluation
-   fake "AI reasoning" animations with no underlying computation

The architecture should remain explainable.

Every component should answer:

> **Why does this exist, and what measurable problem does it solve?**

------------------------------------------------------------------------

# 20. Evaluation Strategy

We need measurable evidence.

At minimum compare:

  System                Retrieval   Step Accuracy   Latency    Cost
  --------------------- ----------- --------------- ---------- ----------
  Embedding baseline    baseline    baseline        baseline   baseline
  BM25 + Dense          measure     measure         measure    measure
  \+ Query Enrichment   measure     measure         measure    measure
  \+ World Model        measure     measure         measure    measure
  \+ Validator          measure     measure         measure    measure
  Fast Path             N/A         N/A             measure    measure

Potential metrics:

-   retrieval accuracy
-   Recall@K
-   NDCG / MRR if applicable to the evaluation setup
-   correct action selection
-   step/sequence accuracy
-   invalid-action rate
-   hallucinated-action rate
-   cache hit rate
-   P50 latency
-   P95 latency
-   cost/query

Do not invent numbers for the PPT. All final metrics must come from
actual experiments.

------------------------------------------------------------------------

# 21. Key Innovation

The strongest innovation story is:

## "From RAG to Reasoning"

### Conventional troubleshooting

``` text
Complaint
   ↓
Retrieve article
   ↓
Generate instructions
```

### ATLAS Device Intelligence

``` text
Complaint
   ↓
Semantic representation
   ↓
Device World Model
   ↓
Hybrid retrieval
   ↓
Relationship-aware reasoning
   ↓
Action selection
   ↓
Deterministic validation
   ↓
Exact executable fix
```

Core statement:

> **The LLM reasons about the device. The world model and action catalog
> constrain what is actually possible.**

------------------------------------------------------------------------

# 22. Three-Layer Truth Model

This should be a recurring architectural concept.

``` text
┌─────────────────────────────┐
│ LLM                         │
│ Language + reasoning        │
└──────────────┬──────────────┘
               │ proposes
               ▼
┌─────────────────────────────┐
│ DEVICE WORLD MODEL          │
│ Relationships + evidence    │
└──────────────┬──────────────┘
               │ grounds
               ▼
┌─────────────────────────────┐
│ ACTION CATALOG               │
│ Executable truth             │
└─────────────────────────────┘
```

In simple terms:

> **LLM proposes. World Model explains. Catalog decides.**

------------------------------------------------------------------------

# 23. PPT Plan

The supplied Samsung PRISM submission template suggests the following
sections:

1.  Theme
2.  Existing Solutions & Gaps
3.  Our Solution & Architecture Diagram
4.  Demo & Product Walkthrough
5.  Tools and Tech Stack
6.  Impact & Use Case
7.  Innovation, Results and Limitations
8.  What's Next
9.  Brownie Points / Differentiation
10. Submission Checklist
11. Thank You

Our intended deck:

## Slide 1 --- FixFlow

**ATLAS Device Intelligence**

From vague complaint → validated one-tap fix

## Slide 2 --- The Problem

Vague complaints → manual interpretation → user hunts through Settings.

## Slide 3 --- Existing Solutions & Gap

Chatbot vs Search vs Rule Engine.

Then:

**FixFlow = Language Intelligence + World Model + Action Grounding**

## Slide 4 --- Solution

``` text
Understand → Retrieve → Reason → Validate → Execute
```

## Slide 5 --- Architecture

Full technical pipeline.

Highlight:

> **LLM proposes. World Model explains. Catalog decides.**

## Slide 6 --- Demo

Product screenshots / live workflow.

## Slide 7 --- Tech Stack

LLM, embeddings, BM25, vector retrieval, FastAPI, database, cache,
Docker, telemetry.

## Slide 8 --- Results

Only actual measured numbers.

## Slide 9 --- Innovation

Semantic Complaint Compiler\
Device World Model\
Deterministic Guardrail\
Semantic Fast Path

## Slide 10 --- Limitations

Be honest about corpus coverage, exact Settings mappings, ambiguity, and
physical issues.

## Slide 11 --- What's Next

10k+ scenarios → richer device context → multimodal troubleshooting →
on-device inference → proactive diagnostics.

## Slide 12 --- Differentiation

``` text
RAG:
"What documents are similar?"

ATLAS Device Intelligence:
"What is happening, what could cause it,
what can we safely do, and which exact
device action performs it?"
```

------------------------------------------------------------------------

# 24. Implementation Plan

We have a short hackathon window, so prioritize working functionality.

## Phase 1 --- Data + Baseline

-   inspect supplied Theme 02 assets
-   build normalized catalog
-   implement basic retrieval
-   expose baseline REST endpoint
-   create evaluation harness

## Phase 2 --- Intelligence

-   query enrichment
-   query variations
-   hybrid retrieval
-   reranking
-   structured planner

## Phase 3 --- ATLAS Layer

-   device entities
-   relationships
-   world-model lookup
-   relationship-aware candidate reasoning
-   session state

## Phase 4 --- Grounding

-   deterministic validation
-   schema validation
-   deeplink validation
-   action sequencing
-   hallucination rejection

## Phase 5 --- Performance

-   semantic/normalized cache
-   latency instrumentation
-   P50/P95 metrics
-   cost measurement

## Phase 6 --- Product

-   polished frontend
-   animated world-model visualization
-   troubleshooting result cards
-   simulated Settings experience if appropriate

## Phase 7 --- Submission

-   benchmark
-   harden edge cases
-   README
-   Docker
-   PPT
-   demo video
-   AI disclosure
-   final repository

------------------------------------------------------------------------

# 25. Proposed Repository

``` text
atlas-device-intelligence/
│
├── README.md
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── catalog/
│
├── src/
│   ├── api/
│   ├── enrichment/
│   ├── retrieval/
│   ├── world_model/
│   ├── planner/
│   ├── validator/
│   ├── cache/
│   ├── telemetry/
│   └── schemas/
│
├── evaluation/
│   ├── baselines/
│   ├── benchmarks/
│   └── reports/
│
├── frontend/
│
├── tests/
│
├── prompts/
│
└── docs/
    ├── architecture.md
    ├── evaluation.md
    └── demo-script.md
```

This is a starting point, not a mandate. Simplify it if implementation
proves that a smaller structure is better.

------------------------------------------------------------------------

# 26. API Concept

Potential API:

``` http
POST /v1/troubleshoot
```

Input:

``` json
{
  "query": "My phone gets hot and battery dies quickly"
}
```

Output should follow the **official Theme 02 schema exactly**.

Conceptually:

``` json
{
  "goal": "...",
  "title": "...",
  "score": 0.0,
  "actions": [
    {
      "actionName": "...",
      "description": "...",
      "stepGroups": [],
      "category": "...",
      "actionableDeeplink": "..."
    }
  ],
  "query_variations": []
}
```

Do not use this conceptual example as a substitute for the official
schema. The real supplied schema must be treated as authoritative.

------------------------------------------------------------------------

# 27. Constraints We Must Respect

From the Theme 02 brief/material:

-   REST API output
-   structured JSON
-   exact schema compliance
-   actions + steps + associated deeplinks
-   reusable mapping aimed at 10k+ scenarios
-   exact/valid deeplink resolution
-   no hallucinated URLs
-   catalog integrity
-   correct action hierarchy
-   fast-path caching
-   report accuracy, latency and cost

The system should be built around the actual supplied datasets and
schema rather than a fabricated demo dataset.

------------------------------------------------------------------------

# 28. Demo Failure Cases We Should Intentionally Test

A serious system should handle:

### Unknown issue

> "My phone randomly smells like burning plastic."

Should not fabricate a Settings solution.

### Manual intervention

> "My battery is swollen."

Should classify it as requiring physical/service intervention where the
catalog says so.

### Ambiguous issue

> "My phone is slow."

May require clarification or return the most defensible supported
troubleshooting sequence.

### Unsupported action

If the LLM proposes an action not in the catalog:

``` text
REJECT
```

### Invalid deeplink

If a generated result does not correspond to a catalog entry:

``` text
REJECT
```

### Conflicting symptoms

The system should prefer evidence-supported actions rather than blindly
following the first semantic match.

------------------------------------------------------------------------

# 29. What Success Looks Like

A successful submission should make a Samsung R&D engineer think:

> "This isn't just an LLM wrapped around a support database."

Instead:

> "They built a structured device intelligence layer that separates
> language reasoning from executable device truth."

The ideal demo should prove:

1.  The system understands vague language.
2.  Retrieval finds relevant actions.
3.  The world model adds useful structure.
4.  The LLM produces a coherent plan.
5.  Invalid/hallucinated actions are rejected.
6.  Every executable action maps to a trusted deeplink.
7.  Cached common queries are fast.
8.  The architecture scales beyond a handful of demo cases.
9.  The metrics support the engineering claims.

------------------------------------------------------------------------

# 30. Critical Engineering Principle

# Complexity must earn its place.

We should continuously ask:

> **Why?**

Why a graph?

Why an LLM?

Why hybrid retrieval?

Why reranking?

Why semantic caching?

Why another service?

If the answer is not measurable value, remove it.

The strongest submission is not the one with the most components.

It is the one where every component exists for a reason and the team can
defend every architectural decision.

------------------------------------------------------------------------

# 31. Source-of-Truth Hierarchy

When future ideation or implementation decisions conflict, use this
order:

### 1. Samsung PRISM official Theme 02 requirements

These are non-negotiable.

### 2. Actual supplied Theme 02 datasets and schema

These define the data and output contract.

### 3. Evaluation results

Measured behavior beats assumptions.

### 4. This Idea.md

Defines our product/architecture direction.

### 5. Team brainstorming

Ideas are welcome, but they must not silently override the above.

------------------------------------------------------------------------

# 32. Important Distinction for Teammates / Future ChatGPT Sessions

When discussing this project, understand the terminology correctly:

**ATLAS is not a Samsung requirement.**

ATLAS-class is **our internal engineering philosophy**:

> Build a structured world model, represent
> relationships/dependencies/state explicitly, use AI to reason over
> that model, and keep executable truth deterministic.

**FixFlow is the product.**

**ATLAS Device Intelligence is the underlying architecture.**

The Samsung submission should primarily be presented in Samsung's Theme
02 terminology. We should not force the word "ATLAS" into the submission
if it confuses the judges.

------------------------------------------------------------------------

# 33. Final Concept in One Diagram

``` text
                         FIXFLOW
              ATLAS DEVICE INTELLIGENCE
                         │
                         ▼
              ┌─────────────────────┐
              │  VAGUE COMPLAINT    │
              └──────────┬──────────┘
                         ↓
              ┌─────────────────────┐
              │ QUERY ENRICHMENT    │
              └──────────┬──────────┘
                         ↓
              ┌─────────────────────┐
              │ HYBRID RETRIEVAL    │
              │ Dense + BM25        │
              └──────────┬──────────┘
                         ↓
              ┌─────────────────────┐
              │ DEVICE WORLD MODEL  │
              │                     │
              │ symptoms            │
              │ causes              │
              │ evidence            │
              │ actions             │
              │ constraints         │
              └──────────┬──────────┘
                         ↓
              ┌─────────────────────┐
              │ LLM PLANNER         │
              │ ACTION IDs ONLY     │
              └──────────┬──────────┘
                         ↓
              ┌─────────────────────┐
              │ DETERMINISTIC       │
              │ VALIDATOR           │
              └──────────┬──────────┘
                         ↓
              ┌─────────────────────┐
              │ TRUSTED ACTION      │
              │ CATALOG             │
              └──────────┬──────────┘
                         ↓
              ┌─────────────────────┐
              │ EXACT SETTINGS      │
              │ DEEPLINK            │
              └──────────┬──────────┘
                         ↓
                    ONE-TAP FIX
```

# The thesis

> **Move troubleshooting from "retrieve an answer" to "reason over a
> model of the device and execute only what the device actually
> supports."**

That is the core idea we should preserve while exploring further
variations.
