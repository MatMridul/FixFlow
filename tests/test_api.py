"""Integration and unit tests for FixFlow FastAPI orchestrator endpoints."""
import shutil
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from cache import CacheStore, SemanticCache
from extraction import StructureExtractor


@pytest.fixture
def test_client():
    temp_dir = tempfile.mkdtemp()
    db_path = str(Path(temp_dir) / "api_test_cache.db")
    store = CacheStore(db_path=db_path)
    cache = SemanticCache(store=store)
    extractor = StructureExtractor()

    app = create_app(cache=cache, extractor=extractor)
    client = TestClient(app)

    yield client

    shutil.rmtree(temp_dir, ignore_errors=True)


class TestApiEndpoints:
    def test_health_endpoint(self, test_client):
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"  # FAQ gate G2
        assert data["service"] == "FixFlow"
        assert data["model_readiness"] is True
        assert data["cache_entries"] == 0

    def test_troubleshoot_cold_path_and_then_cache_hit(self, test_client):
        payload = {
            "query": "My Galaxy screen flickers and dims randomly",
            "siis_response": {
                "title": "Screen flicker and brightness issues",
                "content": (
                    "# Screen Brightness Troubleshooting\n"
                    "Step 1: Adjust Brightness\n"
                    "Navigate to and open Settings. Tap on Display. Adjust the brightness slider.\n"
                    "Step 2: Restart Device\n"
                    "Press and hold the Power key. Tap Restart to reboot the device."
                ),
            },
        }

        # 1. Cold Path Call
        resp1 = test_client.post("/v1/troubleshoot", json=payload)
        assert resp1.status_code == 200
        data1 = resp1.json()

        assert data1["query"] == payload["query"]
        assert len(data1["response"]["contexts"]) == 1
        assert data1["meta"]["cache_hit"] is False
        assert data1["meta"]["fallback"] is None
        # No LLM key in tests -> deterministic path, which genuinely costs $0
        # (the old hardcoded 0.001 was a placeholder, not a real cost).
        assert not data1["meta"]["model"].startswith("cache-")
        assert data1["meta"]["cost_usd"] >= 0.0
        assert 8 <= len(data1["query_variations"]) <= 10  # FAQ A5

        # Health endpoint should now report 1 cached item
        health_resp = test_client.get("/health")
        assert health_resp.json()["cache_entries"] == 1

        # 2. Fast Path / Cache Hit Call (same query)
        resp2 = test_client.post("/v1/troubleshoot", json={"query": payload["query"]})
        assert resp2.status_code == 200
        data2 = resp2.json()

        assert data2["query"] == payload["query"]
        assert len(data2["response"]["contexts"]) == 1
        assert data2["meta"]["cache_hit"] is True
        assert data2["meta"]["cost_usd"] == 0.0
        assert "cache-" in data2["meta"]["model"]
        assert data2["meta"]["fallback"] is None

    def test_troubleshoot_cache_miss_without_siis_returns_fallback(self, test_client):
        # Query not in cache and no SIIS provided
        payload = {"query": "Completely unseen complaint about camera"}
        response = test_client.post("/v1/troubleshoot", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert len(data["response"]["contexts"]) == 0
        assert data["meta"]["cache_hit"] is False
        assert data["meta"]["fallback"] == "no_siis_context"

    def test_troubleshoot_missing_required_query_field(self, test_client):
        response = test_client.post("/v1/troubleshoot", json={})
        assert response.status_code == 422

    def test_troubleshoot_unsupported_issue_empty_actions_fallback(self, test_client):
        # SIIS contains no actionable content -> extractor returns None -> fallback no_match
        payload = {
            "query": "My phone fell in liquid nitrogen and shattered",
            "siis_response": {
                "title": "Cryogenic hazard notice",
                "content": "   ",
            },
        }
        response = test_client.post("/v1/troubleshoot", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data["response"]["contexts"]) == 0
        assert data["meta"]["cache_hit"] is False
        assert data["meta"]["fallback"] == "no_match"

    def test_troubleshoot_hallucinated_steps_filtered_to_fallback(self, test_client, monkeypatch):
        from schema import Action, Goal, StepGroup
        unrelated_goal = Goal(
            goal="Follow these steps to perform Spacecraft Troubleshooting",
            title="Spacecraft issue",
            description="It will guide through spaceship navigation",
            actions=[
                Action(
                    actionName="Engage Warp Drive",
                    description="It will engage hyperdrive engine",
                    stepGroups=[StepGroup(steps=["Press hyperdrive button three times in cockpit"])],
                )
            ],
            score=0.9,
        )
        class MockExtractor:
            def extract(self, *args, **kwargs):
                return unrelated_goal

        monkeypatch.setattr(test_client.app.state, "extractor", MockExtractor())

        payload = {
            "query": "Spaceship engine broken",
            "siis_response": {
                "title": "Mobile network guide",
                "content": "Check your SIM card and APN settings for 5G connectivity.",
            },
        }
        response = test_client.post("/v1/troubleshoot", json=payload)
        assert response.status_code == 200
        data = response.json()
        # FAQ A4 requires non-empty responses when SIIS is present, so fully
        # ungrounded (hallucinated) LLM output is replaced by the SIIS-grounded
        # deterministic plan rather than returning an empty answer.
        contexts = data["response"]["contexts"]
        assert len(contexts) == 1
        dumped = str(contexts[0])
        assert "Warp Drive" not in dumped and "hyperdrive" not in dumped
        assert "SIM card" in dumped

    def test_troubleshoot_low_calibrated_confidence_fallback(self, test_client, monkeypatch):
        # Force low calibrated score below 0.25 threshold
        import api.routes as routes
        monkeypatch.setattr(routes, "calibrate_score", lambda **kwargs: 0.15)

        payload = {
            "query": "Phone screen flickers slightly",
            "siis_response": {
                "title": "Screen brightness guide",
                "content": "Step 1: Adjust Brightness in Settings Display.",
            },
        }
        response = test_client.post("/v1/troubleshoot", json=payload)
        assert response.status_code == 200
        data = response.json()
        # Low confidence is flagged, not turned into an empty answer (FAQ A4).
        assert len(data["response"]["contexts"]) == 1
        assert data["meta"]["cache_hit"] is False
        assert data["meta"]["fallback"] == "low_confidence"

    def test_troubleshoot_end_to_end_binds_real_deeplinks(self, test_client):
        # Full cold-path: Query -> SIIS -> Extract -> Resolution Screen Graph -> Deeplink Binding -> Schema Valid
        payload = {
            "query": "How to back up my phone data to Samsung Cloud?",
            "siis_response": {
                "title": "Back Up Phone Data",
                "content": (
                    "Step 1: Open Settings.\n"
                    "Navigate to and open Settings. Tap on Accounts and backup.\n"
                    "Step 2: Select Back Up Data.\n"
                    "Select Back up data to secure your personal files."
                ),
            },
        }
        response = test_client.post("/v1/troubleshoot", json=payload)
        assert response.status_code == 200
        data = response.json()

        contexts = data["response"]["contexts"]
        assert len(contexts) >= 1
        goal = contexts[0]
        assert len(goal["actions"]) >= 1

        # Check that actionableDeeplink has been resolved to a valid bixby:// URI
        found_deeplink = False
        for action in goal["actions"]:
            for sg in action["stepGroups"]:
                if sg.get("actionableDeeplink") and sg["actionableDeeplink"]["deeplink"].startswith("bixby://"):
                    found_deeplink = True
                    break

        assert found_deeplink, "Expected at least one stepGroup with a bound bixby:// deeplink"
