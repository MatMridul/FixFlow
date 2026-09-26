"""Unit tests for Task A.2.2: Calibration Dev-Set Ground Truth and ECE Metrics."""
import json
from pathlib import Path
import pytest

from validation.calibrator import calibrate_score


@pytest.fixture
def calibration_dataset():
    data_path = Path(__file__).resolve().parent.parent / "data" / "calibration_dev_set.json"
    assert data_path.exists(), f"Missing dataset at {data_path}"
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def test_calibration_dataset_structure(calibration_dataset):
    assert len(calibration_dataset) == 80, f"Expected 80 scenarios, got {len(calibration_dataset)}"

    domain_counts = {}
    for item in calibration_dataset:
        assert "id" in item
        assert "domain" in item
        assert "query" in item and len(item["query"]) > 5
        assert "ground_truth_actions" in item and len(item["ground_truth_actions"]) > 0
        assert 0.0 <= item["grounding_coverage"] <= 1.0
        assert 0.0 <= item["validator_pass_rate"] <= 1.0
        assert 0.0 <= item["retrieval_margin"] <= 1.0
        assert 0.0 <= item["path_alignment"] <= 1.0
        assert 0.0 <= item["expected_calibrated_score"] <= 1.0
        assert item["label"] in (0, 1)

        domain = item["domain"]
        domain_counts[domain] = domain_counts.get(domain, 0) + 1

    assert domain_counts == {
        "display": 20,
        "battery": 20,
        "connectivity": 20,
        "sound_system": 20,
    }


def test_calibration_score_fidelity(calibration_dataset):
    for item in calibration_dataset:
        recomputed = calibrate_score(
            grounding_coverage=item["grounding_coverage"],
            validator_pass_rate=item["validator_pass_rate"],
            retrieval_margin=item["retrieval_margin"],
            path_alignment=item["path_alignment"],
        )
        assert abs(recomputed - item["expected_calibrated_score"]) < 1e-4, (
            f"Score mismatch for {item['id']}: expected {item['expected_calibrated_score']}, got {recomputed}"
        )


def test_expected_calibration_error(calibration_dataset):
    """
    Compute Expected Calibration Error (ECE) across M=10 confidence bins.
    ECE = sum_m (|B_m| / N) * |acc(B_m) - conf(B_m)|
    A well-calibrated engine should have ECE < 0.15 on the dev set.
    """
    num_bins = 10
    bin_boundaries = [i / num_bins for i in range(num_bins + 1)]
    bins = [[] for _ in range(num_bins)]

    for item in calibration_dataset:
        conf = item["expected_calibrated_score"]
        label = item["label"]
        # Find bin
        bin_idx = min(int(conf * num_bins), num_bins - 1)
        bins[bin_idx].append((conf, label))

    total_samples = len(calibration_dataset)
    ece = 0.0

    for b in bins:
        if not b:
            continue
        bin_size = len(b)
        avg_conf = sum(x[0] for x in b) / bin_size
        avg_acc = sum(x[1] for x in b) / bin_size
        ece += (bin_size / total_samples) * abs(avg_acc - avg_conf)

    print(f"\nEmpirical Dev-Set ECE: {ece:.4f}")
    assert ece < 0.15, f"Calibration error too high: {ece:.4f} >= 0.15"
