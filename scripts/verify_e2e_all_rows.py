"""Comprehensive end-to-end audit script across all 20 rows of the official Samsung starter dataset."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from api.app import create_app
from schema import Goal

def run_audit():
    print("=" * 70)
    print("FIXFLOW INTEGRITY & END-TO-END PIPELINE AUDIT")
    print("=" * 70)

    import tempfile
    import shutil
    from cache import CacheStore, CompositionalCache

    # Audit each row with isolated cache to rigorously verify both cold-path extraction
    # and second-pass fast-path replay for every single input scenario.

    data_dir = Path("data")
    input_lines = [line.strip() for line in open(data_dir / "input.txt", encoding="utf-8") if line.strip()]
    raw_siis = json.load(open(data_dir / "siis_responses.json", encoding="utf-8"))
    siis_list = raw_siis.get("responses", raw_siis) if isinstance(raw_siis, dict) else raw_siis

    print(f"Dataset Size: {len(input_lines)} input queries, {len(siis_list)} SIIS rows.")
    assert len(input_lines) == len(siis_list) == 20

    total_actions = 0
    total_bound_deeplinks = 0
    total_validations = 0
    manual_actions_count = 0
    manual_with_deeplink_count = 0
    low_confidence_count = 0
    repair_violations = []

    for idx, (query, siis_entry) in enumerate(zip(input_lines, siis_list), start=1):
        temp_dir = tempfile.mkdtemp()
        db_path = str(Path(temp_dir) / f"audit_cache_{idx}.db")
        cache = CompositionalCache(store=CacheStore(db_path=db_path))
        app = create_app(cache=cache)
        client = TestClient(app)

        payload = {
            "query": query,
            "siis_response": {
                "title": siis_entry["siis_response"]["title"],
                "content": siis_entry["siis_response"]["content"],
            },
        }

        # 1. Cold Path Call
        resp = client.post("/v1/troubleshoot", json=payload)
        assert resp.status_code == 200, f"Row {idx} failed with {resp.status_code}: {resp.text}"
        data = resp.json()
        assert not data["meta"]["cache_hit"], f"Row {idx} should be a cold path call"
        assert len(data["response"]["contexts"]) >= 1, f"Row {idx} yielded empty contexts"

        goal_dict = data["response"]["contexts"][0]
        # Validate Pydantic Goal model
        goal = Goal.model_validate(goal_dict)

        # 2. Fast Path / Cache Hit Call (testing cache persistence)
        cache_resp = client.post("/v1/troubleshoot", json={"query": query})
        assert cache_resp.status_code == 200
        cache_data = cache_resp.json()
        assert cache_data["meta"]["cache_hit"], f"Row {idx} failed second-pass cache hit"
        assert cache_data["meta"]["cost_usd"] == 0.0

        # Audit actions and deeplinks
        for action in goal.actions:
            total_actions += 1
            cat = action.category.value if hasattr(action.category, "value") else str(action.category)
            
            # Check description starts with 'It will'
            if not action.description.startswith("It will"):
                repair_violations.append((idx, action.actionName, f"Description does not start with 'It will': {action.description}"))

            for sg in action.stepGroups:
                if sg.actionableDeeplink:
                    total_bound_deeplinks += 1
                    # Verify verbatim URI format
                    assert sg.actionableDeeplink.deeplink.startswith(("bixby://", "voiceassist://")), (
                        f"Row {idx} bound invalid deeplink: {sg.actionableDeeplink.deeplink}"
                    )
                    if cat == "manual":
                        manual_with_deeplink_count += 1
                elif cat == "manual":
                    manual_actions_count += 1

                if sg.validationDeeplink:
                    total_validations += 1

        if goal.score < 0.25:
            low_confidence_count += 1

        print(f"Row {idx:02d}: [Passed] | Actions: {len(goal.actions)} | Calibrated Score: {goal.score:.2f} | Cold Latency: {data['meta']['latency_ms']:.1f}ms | Cache Latency: {cache_data['meta']['latency_ms']:.1f}ms")

    print("\n" + "=" * 70)
    print("AUDIT SUMMARY & INTEGRITY CHECK")
    print("=" * 70)
    print(f"Total Rows Processed: 20/20 (100% Success)")
    print(f"Total Actions Generated: {total_actions}")
    print(f"Total Actionable Deeplinks Bound: {total_bound_deeplinks}")
    print(f"Total Validation Deeplinks Bound: {total_validations}")
    print(f"Manual Actions Correctly Without Deeplinks: {manual_actions_count}")
    print(f"Manual Actions With Deeplink Violations: {manual_with_deeplink_count}")
    print(f"Description Format Violations: {len(repair_violations)}")
    print(f"Low Confidence Drops: {low_confidence_count}")
    print("=" * 70)

    assert manual_with_deeplink_count == 0, "Manual actions must NEVER have actionableDeeplink"
    assert len(repair_violations) == 0, f"Formatting violations detected: {repair_violations}"

if __name__ == "__main__":
    run_audit()
