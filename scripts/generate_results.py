"""Generate and rigorously validate results.jsonl and results.json for hackathon submission."""
import json
from pathlib import Path
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from api.app import create_app
from api.models import TroubleshootResponse
from schema import Goal


def generate_and_validate():
    print("=" * 70)
    print("GENERATING & VALIDATING FIXFLOW HACKATHON RESULTS")
    print("=" * 70)

    app = create_app()
    client = TestClient(app)

    data_dir = Path("data")
    input_lines = [line.strip() for line in open(data_dir / "input.txt", encoding="utf-8") if line.strip()]
    raw_siis = json.load(open(data_dir / "siis_responses.json", encoding="utf-8"))
    siis_list = raw_siis.get("responses", raw_siis) if isinstance(raw_siis, dict) else raw_siis

    assert len(input_lines) == len(siis_list) == 20, "Input rows must match SIIS rows (20)"

    catalog_raw = json.load(open(data_dir / "deeplinks.json", encoding="utf-8"))["deeplinks"]
    valid_deeplink_uris = {e["deeplink"] for e in catalog_raw}

    results = []
    total_actions = 0
    total_deeplinks = 0
    total_validations = 0

    for idx, (query, siis_entry) in enumerate(zip(input_lines, siis_list), start=1):
        payload = {
            "query": query,
            "siis_response": {
                "title": siis_entry["siis_response"]["title"],
                "content": siis_entry["siis_response"]["content"],
            },
        }

        resp = client.post("/v1/troubleshoot", json=payload)
        assert resp.status_code == 200, f"Row {idx} failed HTTP 200"
        data = resp.json()

        # 1. Validate full TroubleshootResponse envelope
        validated_response = TroubleshootResponse.model_validate(data)

        # 2. Validate contexts against Goal schema
        contexts = validated_response.response.contexts
        assert len(contexts) >= 1, f"Row {idx} returned 0 contexts"
        goal = contexts[0]

        # 3. Rule validations on Goal
        assert goal.goal and len(goal.goal) > 5, f"Row {idx} goal syntax empty"
        assert goal.title and len(goal.title) > 2, f"Row {idx} goal title empty"

        for action in goal.actions:
            total_actions += 1
            cat = action.category.value if hasattr(action.category, "value") else str(action.category)

            # Rule: Description starts with 'It will'
            assert action.description.startswith("It will"), (
                f"Row {idx} action '{action.actionName}' description does not start with 'It will': {action.description}"
            )

            for sg in action.stepGroups:
                # Rule: Manual actions must NEVER have actionableDeeplink
                if cat == "manual":
                    assert sg.actionableDeeplink is None, (
                        f"Row {idx} manual action '{action.actionName}' has actionableDeeplink!"
                    )

                # Rule: Actionable deeplinks must exist in official catalog
                if sg.actionableDeeplink:
                    total_deeplinks += 1
                    uri = sg.actionableDeeplink.deeplink
                    assert uri in valid_deeplink_uris, (
                        f"Row {idx} invented non-catalog URI: {uri}"
                    )

                if sg.validationDeeplink:
                    total_validations += 1

        results.append(data)
        print(f"Row {idx:02d}: [VALID] Actions: {len(goal.actions)} | Score: {goal.score:.2f} | Latency: {data['meta']['latency_ms']:.1f}ms")

    # Write results.jsonl (one JSON line per query)
    jsonl_path = Path("results.jsonl")
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for item in results:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"\nWritten {len(results)} rows to {jsonl_path.resolve()}")

    # Write results.json (pretty formatted array)
    json_path = Path("results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Written {len(results)} rows to {json_path.resolve()}")

    # Verification of written files
    assert jsonl_path.exists() and jsonl_path.stat().st_size > 0
    assert json_path.exists() and json_path.stat().st_size > 0

    with open(jsonl_path, "r", encoding="utf-8") as f:
        jsonl_lines = [json.loads(line) for line in f if line.strip()]
    assert len(jsonl_lines) == 20

    with open(json_path, "r", encoding="utf-8") as f:
        json_array = json.load(f)
    assert len(json_array) == 20

    print("\n" + "=" * 70)
    print("EXHAUSTIVE RESULTS VALIDATION SUMMARY")
    print("=" * 70)
    print(f"Total Rows Verified:                20/20 (100% Valid)")
    print(f"Total Actions Verified:             {total_actions}")
    print(f"Total Authentic Deeplinks Bound:    {total_deeplinks}")
    print(f"Total Validation Deeplinks Bound:   {total_validations}")
    print(f"Catalog Integrity Violations:       0 (100% Verbatim Match)")
    print(f"Category Constraint Violations:     0 (Manual actions strictly link-free)")
    print(f"Schema Rule Violations:             0 (100% 'It will' compliant)")
    print("=" * 70)


if __name__ == "__main__":
    generate_and_validate()
