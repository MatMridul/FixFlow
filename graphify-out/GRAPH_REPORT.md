# Graph Report - FixFlow  (2026-09-20)

## Corpus Check
- Corpus is ~12,300 words - fits in a single context window. You may not need a graph.

## Summary
- 15 nodes · 15 edges · 4 communities (3 shown, 1 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.85)
- Token cost: 1,200 input · 800 output

## Community Hubs (Navigation)
- Core Novelties & Architecture
- Core Novelties & Architecture
- Core Novelties & Architecture
- Graphify Knowledge Rules

## God Nodes (most connected - your core abstractions)
1. `FixFlow Troubleshooting Engine` - 6 edges
2. `N1 Compositional Multi-Intent Cache` - 3 edges
3. `N3 Path-Constrained Screen Resolution` - 3 edges
4. `N4 Self-Verifying Plans (validationDeeplink)` - 3 edges
5. `N2 Intent-Signature Gated Cache` - 2 edges
6. `N5 Evidence-Calibrated Score & Provenance` - 2 edges
7. `Hybrid Screen Resolution & Reranker` - 2 edges
8. `Deterministic Validator & Repair Loop` - 2 edges
9. `SIIS Reference Text Grounding` - 1 edges
10. `Query Enrichment & Clause Splitter` - 1 edges

## Surprising Connections (you probably didn't know these)
- `FixFlow Troubleshooting Engine` --implements--> `N5 Evidence-Calibrated Score & Provenance`  [EXTRACTED]
  README.md → docs/FixFlow_Idea_v3.md
- `FixFlow Troubleshooting Engine` --implements--> `N2 Intent-Signature Gated Cache`  [EXTRACTED]
  README.md → docs/FixFlow_Idea_v3.md
- `FixFlow Troubleshooting Engine` --implements--> `N3 Path-Constrained Screen Resolution`  [EXTRACTED]
  README.md → docs/FixFlow_Idea_v3.md
- `FixFlow Troubleshooting Engine` --implements--> `N4 Self-Verifying Plans (validationDeeplink)`  [EXTRACTED]
  README.md → docs/FixFlow_Idea_v3.md
- `FixFlow Troubleshooting Engine` --implements--> `N1 Compositional Multi-Intent Cache`  [EXTRACTED]
  README.md → docs/FixFlow_Idea_v3.md

## Hyperedges (group relationships)
- **FixFlow Core Novelty Suite (N1-N5)** — docs_fixflow_idea_v3_n1_compositional_cache, docs_fixflow_idea_v3_n2_intent_signature_gate, docs_fixflow_idea_v3_n3_settings_screen_graph, docs_fixflow_idea_v3_n4_self_verifying_plans, docs_fixflow_idea_v3_n5_calibrated_scoring [EXTRACTED 1.00]
- **FixFlow Inference Pipeline Execution Stages** — docs_fixflow_idea_v3_enrichment, docs_fixflow_idea_v3_n1_compositional_cache, docs_fixflow_idea_v3_resolution, docs_fixflow_idea_v3_validation_loop [EXTRACTED 1.00]

## Communities (4 total, 1 thin omitted)

### Community 0 - "Core Novelties & Architecture"
Cohesion: 0.50
Nodes (5): Query Enrichment & Clause Splitter, N1 Compositional Multi-Intent Cache, N2 Intent-Signature Gated Cache, FixFlow Troubleshooting Engine, SIIS Reference Text Grounding

### Community 1 - "Core Novelties & Architecture"
Cohesion: 0.40
Nodes (5): N3 Path-Constrained Screen Resolution, N4 Self-Verifying Plans (validationDeeplink), Hybrid Screen Resolution & Reranker, Student Kit Inspection Findings, Device World Model Philosophy

### Community 2 - "Core Novelties & Architecture"
Cohesion: 0.67
Nodes (3): Theme 02 API Schema Contract, N5 Evidence-Calibrated Score & Provenance, Deterministic Validator & Repair Loop

## Knowledge Gaps
- **5 isolated node(s):** `Query Enrichment & Clause Splitter`, `Theme 02 API Schema Contract`, `Student Kit Inspection Findings`, `Graphify Knowledge Graph Architecture Rule`, `Graphify Traversal Workflow`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 7 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `FixFlow Troubleshooting Engine` connect `Core Novelties & Architecture` to `Core Novelties & Architecture`, `Core Novelties & Architecture`?**
  _High betweenness centrality (0.571) - this node is a cross-community bridge._
- **Why does `N5 Evidence-Calibrated Score & Provenance` connect `Core Novelties & Architecture` to `Core Novelties & Architecture`?**
  _High betweenness centrality (0.220) - this node is a cross-community bridge._
- **Why does `N3 Path-Constrained Screen Resolution` connect `Core Novelties & Architecture` to `Core Novelties & Architecture`?**
  _High betweenness centrality (0.165) - this node is a cross-community bridge._
- **What connects `Query Enrichment & Clause Splitter`, `Theme 02 API Schema Contract`, `Student Kit Inspection Findings` to the rest of the system?**
  _5 weakly-connected nodes found - possible documentation gaps or missing edges._