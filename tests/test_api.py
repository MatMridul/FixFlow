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
        assert data["status"] == "healthy"
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
        assert data1["meta"]["cost_usd"] > 0.0

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
