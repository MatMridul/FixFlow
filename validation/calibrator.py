"""Novelty N5: Evidence-Calibrated Confidence Scorer."""
from typing import Dict, Optional


def calibrate_score(
    grounding_coverage: float,
    validator_pass_rate: float,
    retrieval_margin: float = 1.0,
    path_alignment: float = 1.0,
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """
    Compute an empirical, evidence-calibrated confidence score for a Goal.

    Contract 2 Interface with Dev B (Hemish):
      - Dev A provides: grounding_coverage, validator_pass_rate
      - Dev B provides: retrieval_margin, path_alignment

    Formula:
      score = (w_ground * grounding) + (w_valid * validator) +
              (w_retriev * retrieval) + (w_path * path)

    Returns:
      float in [0.0, 1.0] rounded to 2 decimal places.
    """
    if weights is None:
        weights = {
            "grounding": 0.40,
            "validator": 0.30,
            "retrieval": 0.15,
            "path": 0.15,
        }

    # Normalize weights if sum != 1.0
    w_sum = sum(weights.values())
    w_ground = weights.get("grounding", 0.40) / w_sum
    w_valid = weights.get("validator", 0.30) / w_sum
    w_retriev = weights.get("retrieval", 0.15) / w_sum
    w_path = weights.get("path", 0.15) / w_sum

    # Clamp all inputs to [0.0, 1.0]
    g = max(0.0, min(1.0, grounding_coverage))
    v = max(0.0, min(1.0, validator_pass_rate))
    r = max(0.0, min(1.0, retrieval_margin))
    p = max(0.0, min(1.0, path_alignment))

    raw_score = (w_ground * g) + (w_valid * v) + (w_retriev * r) + (w_path * p)
    calibrated = round(max(0.0, min(1.0, raw_score)), 2)

    return calibrated
