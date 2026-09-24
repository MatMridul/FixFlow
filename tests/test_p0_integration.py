"""P0 Integration Checkpoint: End-to-end verification over all 20 rows of official dataset."""
import json
import shutil
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from cache import CacheStore, SemanticCache
from extraction import StructureExtractor
from validation import validate_goal

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class TestP0CheckpointIntegration:
    @pytest.fixture
    def client_and_cache(self):
        temp_dir = tempfile.mkdtemp()
        db_path = str(Path(temp_dir) / "checkpoint0_cache.db")
        store = CacheStore(db_path=db_path)
        cache = SemanticCache(store=store)
        extractor = StructureExtractor()

        app = create_app(cache=cache, extractor=extractor)
        client = TestClient(app)

        yield client, cache

        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_all_20_rows_cold_path_and_cache_warmup(self, client_and_cache):
        client, cache = client_and_cache

        siis_path = DATA_DIR / "siis_responses.json"
        assert siis_path.exists(), "data/siis_responses.json must exist"

        with open(siis_path, "r", encoding="utf-8") as f:
            siis_data = json.load(f)

        responses = siis_data["responses"]
        assert len(responses) == 20, f"Expected 20 responses, found {len(responses)}"

        # Phase 1: Cold Path Run on all 20 rows
        for row in responses:
            row_id = row["id"]
            query = row["original_query"]
            siis_title = row["siis_response"]["title"]
            siis_content = row["siis_response"]["content"]

            payload = {
                "query": query,
                "siis_response": {
                    "title": siis_title,
                    "content": siis_content,
                },
            }

            resp = client.post("/v1/troubleshoot", json=payload)
            assert resp.status_code == 200, f"Failed on row {row_id}: {resp.text}"
            data = resp.json()

            # Verify response schema structure
            assert data["query"] == query
            assert len(data["response"]["contexts"]) == 1, f"No context produced for row {row_id}"

            goal_dict = data["response"]["contexts"][0]
            # Deep rule validation
            from schema import Goal
            goal_obj = Goal.model_validate(goal_dict)
            report = validate_goal(goal_obj)
            assert report.is_valid, f"Validation failure on row {row_id}: {report.errors}"

            assert data["meta"]["cache_hit"] is False
            assert data["meta"]["fallback"] is None
            assert data["meta"]["cost_usd"] > 0.0

        # Health endpoint should now report all 20 items in cache
        health_resp = client.get("/health")
        assert health_resp.json()["cache_entries"] == 20

        # Phase 2: Fast Path Cache Hit Run on all 20 rows
        for row in responses:
            row_id = row["id"]
            query = row["original_query"]

            # Query without SIIS context (cache-only lookup)
            resp = client.post("/v1/troubleshoot", json={"query": query})
            assert resp.status_code == 200, f"Cache lookup failed on row {row_id}"
            data = resp.json()

            assert len(data["response"]["contexts"]) == 1
            assert data["meta"]["cache_hit"] is True
            assert data["meta"]["cost_usd"] == 0.0
            assert data["meta"]["latency_ms"] < 100.0  # Fast path under 100ms
