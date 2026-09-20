# Google Jules — Autonomous CI, Testing & QA Strategy

**Project:** FixFlow (Samsung PRISM GenAI Hackathon · Theme 02)  
**Developers:** Mridul (Dev A) & Hemish (Dev B)  
**Autonomous Worker:** Google Jules (Google AI Pro Plan · 100 Tasks/Day Quota)

---

## 1. Overview & Purpose

**Google Jules** is an asynchronous cloud AI coding agent that interfaces directly with our GitHub repository ([`MatMridul/FixFlow`](https://github.com/MatMridul/FixFlow)). 

### Core Operating Principle
> **Mridul & Hemish + Antigravity architect and build the platform. Jules absorbs the repetitive engineering toil (test suites, regression fixes, CI/CD automation, and linting/formatting).**

---

## 2. Activation Trigger Points (When to Prompt & Activate)

Antigravity will proactively prompt **Mridul** (*"Mridul, it is time to set up Jules"*) when the following milestones are reached:

1. **Milestone 1 — P0 Modules Ready for Testing:**
   * When `validation/rules.py` and `catalog/compiler.py` baseline implementations are committed.
   * *Trigger for Jules:* Generate full `pytest` unit test suites and edge-case mocks.
2. **Milestone 2 — Repository CI/CD Setup:**
   * When core dependencies and project structure are frozen.
   * *Trigger for Jules:* Set up `.github/workflows/ci.yml` (test runner, linter, schema validator on every PR/push).
3. **Milestone 3 — Evaluation Dataset Fuzzing & Regression:**
   * When the evaluation harness (`eval/`) starts running against test queries.
   * *Trigger for Jules:* Triage and patch validator edge-case failures across failing query samples.
4. **Milestone 4 — Containerization & Production Build:**
   * When the FastAPI backend and React frontend are ready for demo packaging.
   * *Trigger for Jules:* Multi-stage `Dockerfile` optimization and `docker-compose.yml`.

---

## 3. Quota Optimization Guidelines (Stay within 20–35 Tasks/Day)

To ensure we never burn through the 100 tasks/day quota during rapid development:

1. **Batch Macro-Tasks:** Never dispatch single-function tests or one-line fixes. Dispatch 1 task per complete module or test suite (e.g. 20+ tests in one task).
2. **Feature-Complete Branches:** Only assign tasks on stable interfaces and pushed commits.
3. **Structured Prompts:** Always provide context, explicit file paths, constraints, and measurable acceptance criteria.

---

## 4. Ready-to-Use Prompt Templates for Jules

### Template A: Unit & Integration Test Suite Generation
```markdown
### Context
We are building FixFlow for Samsung PRISM Hackathon (Theme 02). See docs/FixFlow_Idea_v3.md.

### Task
Implement a comprehensive pytest suite in `tests/test_<module_name>.py` for `<module_path>`.

### Requirements & Constraints
1. Cover all core functions, branch conditions, and edge cases.
2. Add parameterised tests for boundary cases (malformed input, nulls, unexpected types).
3. Ensure no modifications are made to schema.py or data/.
4. Target >90% code coverage.

### Acceptance Criteria
- Run `pytest tests/test_<module_name>.py` and ensure all tests pass.
```

### Template B: CI/CD Pipeline Configuration
```markdown
### Context
FixFlow backend is built on Python 3.10+, FastAPI, and Pydantic.

### Task
Create `.github/workflows/ci.yml` to automate tests and code health.

### Requirements & Constraints
1. Set up Python 3.10 and 3.11 matrices.
2. Cache pip/uv dependencies.
3. Run `pytest tests/` on all push and pull_request events to `main`.
4. Run `ruff check .` for linting.
5. Verify schema validation passes on sample outputs.
```

### Template C: Edge-Case Bug Fixing from Evaluation Trace
```markdown
### Context
FixFlow's evaluation harness caught a validation failure on specific queries.

### Failing Trace
<Paste traceback and input query>

### Task
Patch the validator in `validation/rules.py` to correctly handle this edge case without breaking existing tests.

### Acceptance Criteria
- Add regression test case in `tests/test_validation_rules.py`.
- Run full pytest suite and verify all tests pass.
```

---

## 5. Workflow Summary

```
   MRIDUL & HEMISH + ANTIGRAVITY                     GOOGLE JULES
┌─────────────────────────────────┐         ┌───────────────────────────────┐
│ • Draft novelties (N1-N5)       │         │ • Generates full test suites  │
│ • Write core algorithms         │ ──────► │ • Fixes failing edge cases    │
│ • Review & merge PRs            │ ◄────── │ • Manages CI/CD & Docker      │
└─────────────────────────────────┘ (GitHub)└───────────────────────────────┘
```
