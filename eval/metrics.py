"""Pure metric functions over resolution results, decoupled from the harness
that produces them so they can be unit-tested independently and reused once
Dev A's extraction pipeline supplies real (not hand-constructed) scenarios.

These implement the two N3-specific rows from FixFlow_Idea_v3.md §7.2:
"Parent-menu error rate; screen accuracy vs plain hybrid."
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ScenarioResult:
    scenario_id: str
    category: str
    expected_deeplink_id: Optional[str]
    predicted_deeplink_id: Optional[str]
    expected_is_page_level: Optional[bool]
    predicted_is_page_level: Optional[bool]

    @property
    def correct(self) -> bool:
        return self.predicted_deeplink_id == self.expected_deeplink_id

    @property
    def is_parent_menu_error(self) -> bool:
        """A specific failure mode, not just any wrong answer: predicted
        the wrong screen AND got the page-vs-leaf level wrong too. A wrong
        answer that's still leaf-vs-leaf (picked the wrong toggle on the
        right page) is a different failure and shouldn't inflate this
        number."""
        if self.correct:
            return False
        if self.expected_is_page_level is None or self.predicted_is_page_level is None:
            return False
        return self.expected_is_page_level != self.predicted_is_page_level


def screen_resolution_accuracy(results: list[ScenarioResult]) -> float:
    scored = [r for r in results if r.expected_deeplink_id is not None]
    if not scored:
        return 0.0
    return sum(1 for r in scored if r.correct) / len(scored)


def parent_menu_error_rate(results: list[ScenarioResult]) -> float:
    scored = [r for r in results if r.expected_deeplink_id is not None]
    if not scored:
        return 0.0
    return sum(1 for r in scored if r.is_parent_menu_error) / len(scored)


def manual_no_deeplink_compliance(results: list[ScenarioResult]) -> float:
    """Fraction of manual-category scenarios that correctly got no
    deeplink at all (brief §4.1 rule)."""
    manual = [r for r in results if r.category == "manual"]
    if not manual:
        return 1.0
    return sum(1 for r in manual if r.predicted_deeplink_id is None) / len(manual)
