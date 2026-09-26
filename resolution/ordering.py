"""Safe-first, critical-last action ordering (brief: "least disruptive
troubleshooting steps first; destructive/critical operations last").

`manual` actions (physical interventions like visiting a service center) are
ordered after `auto` but before `critical` — confirmed by the official
sample_output.json, whose only two actions are auto (backup) then manual
(schedule repair): the destructive end of the scale is reserved for
`critical` alone.
"""
from __future__ import annotations

from typing import Sequence, TypeVar

_CATEGORY_WEIGHT = {"auto": 0, "manual": 1, "critical": 2}


class _HasCategory:
    category: str | None


T = TypeVar("T", bound=_HasCategory)


def _weight(action) -> int:
    category = getattr(action, "category", None) or "manual"
    category = getattr(category, "value", category)  # unwrap enum if needed
    return _CATEGORY_WEIGHT.get(category, _CATEGORY_WEIGHT["manual"])


def order_actions(actions: Sequence[T]) -> list[T]:
    """Stable sort: auto -> manual -> critical. Preserves relative order of
    actions within the same category (extraction order reflects the SIIS
    text's own sequencing, which we should not scramble)."""
    return sorted(actions, key=_weight)
