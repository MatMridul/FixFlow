"""Tests for Novelty N1: Clause Splitter and Compositional Multi-Intent Cache."""
import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from cache.compositional import (
    CompositionalCache,
    deduplicate_critical_actions,
)
from cache.store import CacheStore
from enrichment.clause_splitter import decompose_query_intents, split_raw_clauses
from schema import Action, Goal, StepGroup, actionCategory


def test_split_raw_clauses():
    text1 = "Screen flickers and the battery dies fast"
    clauses1 = split_raw_clauses(text1)
    assert len(clauses1) == 2
    assert "Screen flickers" in clauses1[0]
    assert "battery dies fast" in clauses1[1]

    text2 = "Display is dark; phone gets very hot"
    clauses2 = split_raw_clauses(text2)
    assert len(clauses2) == 2

    text3 = "Single query without conjunction"
    clauses3 = split_raw_clauses(text3)
    assert len(clauses3) == 1


def test_decompose_query_intents_over_splitting_protection():
    # Multi-domain split
    compound = "Screen flickers and battery draining fast"
    intents = decompose_query_intents(compound)
    assert len(intents) == 2
    assert intents[0][1].domain == "Display"
    assert intents[1][1].domain == "Battery"

    # Over-splitting protection: redundant clauses in same domain & symptom merged
    redundant = "Phone is lagging and very slow"
    merged_intents = decompose_query_intents(redundant)
    assert len(merged_intents) == 1
    assert "lagging and very slow" in merged_intents[0][0]


def test_deduplicate_critical_actions():
    action_auto1 = Action(
        actionName="Adjust Brightness",
        description="It will adjust brightness properly",
        category=actionCategory.auto,
        stepGroups=[StepGroup(steps=["Step 1"])]
    )
    action_crit1 = Action(
        actionName="Restart Device",
        description="It will restart the phone completely",
        category=actionCategory.critical,
        stepGroups=[StepGroup(steps=["Reboot phone"])]
    )
    goal1 = Goal(
        goal="Follow these steps to perform this Display Troubleshooting",
        title="Display fault",
        score=0.9,
        actions=[action_auto1, action_crit1]
    )

    action_auto2 = Action(
        actionName="Turn On Battery Saver",
        description="It will enable battery saver mode",
        category=actionCategory.auto,
        stepGroups=[StepGroup(steps=["Step 2"])]
    )
    action_crit2 = Action(
        actionName="Restart Device",
        description="It will restart the phone completely",
        category=actionCategory.critical,
        stepGroups=[StepGroup(steps=["Reboot phone"])]
    )
    goal2 = Goal(
        goal="Follow these steps to perform this Battery Troubleshooting",
        title="Battery drain",
        score=0.9,
        actions=[action_auto2, action_crit2]
    )

    deduped = deduplicate_critical_actions([goal1, goal2])
    assert len(deduped) == 2

    # Goal 1 has the restart action
    crit_count1 = sum(1 for a in deduped[0].actions if a.category == actionCategory.critical)
    # Goal 2 has its duplicate restart action pruned
    crit_count2 = sum(1 for a in deduped[1].actions if a.category == actionCategory.critical)

    assert crit_count1 == 1
    assert crit_count2 == 0


def test_compositional_cache_full_hit(tmp_path):
    db_path = str(tmp_path / "comp_cache_test.db")
    cache = CompositionalCache(store=CacheStore(db_path=db_path))

    goal_display = Goal(
        goal="Follow these steps to perform this Display Troubleshooting",
        title="Screen flicker",
        score=0.92,
        actions=[
            Action(
                actionName="Adjust Refresh Rate",
                description="It will change motion smoothness setting",
                category=actionCategory.auto,
                stepGroups=[StepGroup(steps=["Open Settings.", "Tap Display."])]
            )
        ]
    )

    goal_battery = Goal(
        goal="Follow these steps to perform this Battery Troubleshooting",
        title="Battery drain",
        score=0.88,
        actions=[
            Action(
                actionName="Enable Power Saving",
                description="It will extend your battery duration",
                category=actionCategory.auto,
                stepGroups=[StepGroup(steps=["Open Settings.", "Tap Battery."])]
            )
        ]
    )

    # Pre-warm individual clauses in cache
    cache.put("Screen flickers", goal_display)
    cache.put("battery dies fast", goal_battery)

    # Query compound complaint
    compound_query = "Screen flickers and battery dies fast"
    res = cache.get_compound(compound_query)

    assert res.hit is True
    assert res.partial_hit is False
    assert res.hit_type == "full_compositional"
    assert len(res.goals) == 2
    assert res.goals[0].title == "Screen flicker"
    assert res.goals[1].title == "Battery drain"
    assert res.latency_ms < 150.0


def test_compositional_cache_partial_hit_and_miss(tmp_path):
    db_path = str(tmp_path / "comp_cache_partial.db")
    cache = CompositionalCache(store=CacheStore(db_path=db_path))

    goal_display = Goal(
        goal="Follow these steps to perform this Display Troubleshooting",
        title="Screen flicker",
        score=0.92,
        actions=[
            Action(
                actionName="Adjust Refresh Rate",
                description="It will change motion smoothness setting",
                category=actionCategory.auto,
                stepGroups=[StepGroup(steps=["Open Settings."])]
            )
        ]
    )
    cache.put("Screen flickers", goal_display)

    # Query with 1 known and 1 unknown clause
    partial_query = "Screen flickers and camera is blurry"
    res = cache.get_compound(partial_query)

    assert res.hit is False
    assert res.partial_hit is True
    assert res.hit_type == "partial_compositional"
    assert len(res.goals) == 1
    assert len(res.missing_clauses) == 1
    assert "camera is blurry" in res.missing_clauses[0][0]


def test_api_e2e_compositional_hit(tmp_path):
    db_path = str(tmp_path / "api_comp_cache.db")
    cache = CompositionalCache(store=CacheStore(db_path=db_path))

    goal1 = Goal(
        goal="Follow these steps to perform this Display Troubleshooting",
        title="Screen flicker",
        score=0.95,
        actions=[
            Action(
                actionName="Adjust Display Settings",
                description="It will stabilize display screen brightness",
                category=actionCategory.auto,
                stepGroups=[StepGroup(steps=["Open Settings.", "Tap Display."])]
            )
        ]
    )
    goal2 = Goal(
        goal="Follow these steps to perform this Battery Troubleshooting",
        title="Battery drain",
        score=0.91,
        actions=[
            Action(
                actionName="Inspect Battery Usage",
                description="It will identify heavy battery apps",
                category=actionCategory.auto,
                stepGroups=[StepGroup(steps=["Open Settings.", "Tap Battery."])]
            )
        ]
    )

    cache.put("screen flickers", goal1)
    cache.put("battery draining fast", goal2)

    app = create_app(cache=cache)
    client = TestClient(app)

    # Compound query matching both pre-warmed sub-intents
    res = client.post("/v1/troubleshoot", json={"query": "screen flickers and battery draining fast"})
    assert res.status_code == 200
    data = res.json()

    assert data["meta"]["cache_hit"] is True
    assert "compositional" in data["meta"]["model"]
    assert data["meta"]["cost_usd"] == 0.0
    assert len(data["response"]["contexts"]) == 2
    assert data["response"]["contexts"][0]["title"] == "Screen flicker"
    assert data["response"]["contexts"][1]["title"] == "Battery drain"
