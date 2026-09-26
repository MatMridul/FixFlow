"""Contract 1 (FixFlow_TwoDev_Plan.md §4): Dev A hands Dev B a Goal object
whose stepGroups have step text but empty deeplink fields. This module fills
`actionableDeeplink` (and as much of `validationDeeplink` as the catalog
itself supplies).

Matching is delegated to resolution.screen_graph.resolve_screen (N3), which
applies the parent-menu guard rather than raw top-1 hybrid score.

Rules enforced here (brief §4.1/§4.2, FixFlow_Idea_v3.md findings E/G):
- `manual` actions never get an actionableDeeplink.
- A deeplink is only bound when retrieval confidence clears `threshold`.
  Below threshold, we do NOT guess `bixby://dummy_positive` — authoring the
  placeholder's description/message text is a generative task (finding G)
  that belongs upstream in extraction, not in blind retrieval. We surface
  the best candidate for that decision instead of hiding it.

CORRECTION to finding E (verify on real data, not the doc's prose): finding E
claimed the catalog's `validation` object is *always* `{deeplink, key}` only.
Re-checked directly against data/deeplinks.json — that is only true for
432/570 entries. The other 138/570 (24%) carry a FULL validation object with
`resultType`/`condition`/`value` already populated (e.g. DL-0542, the exact
entry the official sample_output.json resolves to). Where the catalog
provides the full object we copy it verbatim — no derivation needed. Only
the 432 partial entries still require deriving resultType/condition/value
from SIIS text, which stays N4 work on the extraction side.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from catalog.loader import Catalog
from catalog.models import CatalogEntry
from resolution.retriever import HybridRetriever
from resolution.screen_graph import resolve_screen
from resolution.validation_inference import infer_validation_ref

DEFAULT_THRESHOLD = 0.12


@dataclass
class BindResult:
    status: str  # "matched" | "manual_no_deeplink" | "below_threshold" | "no_catalog_entries"
    actionable_deeplink: Optional[dict]
    validation_ref: Optional[dict]
    top_score: float
    candidate: Optional[CatalogEntry]  # best guess even when below threshold, for human/LLM review
    is_page_level: bool = False
    parent_menu_guard_applied: bool = False


def _to_actionable_deeplink(entry: CatalogEntry) -> dict:
    return {
        "deeplink": entry.deeplink,
        "description": entry.description,
        "message": entry.message,
        "originalType": entry.originalType,
    }


def _to_validation_ref(entry: CatalogEntry) -> Optional[dict]:
    """Verbatim copy where the catalog supplies the full object (138/570),
    catalog-derivable inference by originalType symmetry where safe
    (offURL, see resolution.validation_inference), and None where filling
    it in would require reading SIIS text (updateURL) or doesn't apply
    (onClickURL page-opens)."""
    return infer_validation_ref(entry)


def bind_actionable_deeplink(
    steps: list[str],
    category: str,
    catalog: Catalog,
    retriever: HybridRetriever,
    threshold: float = DEFAULT_THRESHOLD,
) -> BindResult:
    category = getattr(category, "value", category)

    if category == "manual":
        return BindResult(
            status="manual_no_deeplink",
            actionable_deeplink=None,
            validation_ref=None,
            top_score=0.0,
            candidate=None,
        )

    if len(catalog.resolvable_entries()) == 0:
        return BindResult(
            status="no_catalog_entries",
            actionable_deeplink=None,
            validation_ref=None,
            top_score=0.0,
            candidate=None,
        )

    resolution = resolve_screen(retriever, steps)
    if resolution.status != "matched":
        return BindResult(
            status="below_threshold",
            actionable_deeplink=None,
            validation_ref=None,
            top_score=0.0,
            candidate=None,
        )

    if resolution.score >= threshold:
        return BindResult(
            status="matched",
            actionable_deeplink=_to_actionable_deeplink(resolution.entry),
            validation_ref=_to_validation_ref(resolution.entry),
            top_score=resolution.score,
            candidate=resolution.entry,
            is_page_level=resolution.is_page_level,
            parent_menu_guard_applied=resolution.parent_menu_guard_applied,
        )

    return BindResult(
        status="below_threshold",
        actionable_deeplink=None,
        validation_ref=None,
        top_score=resolution.score,
        candidate=resolution.entry,
    )


def resolve_goal_deeplinks(
    goal: Any,
    catalog: Optional[Catalog] = None,
    retriever: Optional[HybridRetriever] = None,
    threshold: float = DEFAULT_THRESHOLD,
) -> Any:
    """
    Contract 1 & Novelty N3/N4: Resolve and bind actionableDeeplink and validationDeeplink
    to each StepGroup within the Goal's actions, and order actions safe-first.
    """
    from resolution.ordering import order_actions
    from schema import Deeplink, ValidationDeepLink

    if catalog is None:
        from catalog.loader import load_catalog
        catalog = load_catalog()
    if retriever is None:
        retriever = HybridRetriever(catalog)

    for action in getattr(goal, "actions", []):
        category_str = action.category.value if hasattr(action.category, "value") else str(action.category or "manual")
        for sg in getattr(action, "stepGroups", []):
            bind_res = bind_actionable_deeplink(
                steps=sg.steps,
                category=category_str,
                catalog=catalog,
                retriever=retriever,
                threshold=threshold,
            )
            if bind_res.status == "matched":
                if bind_res.actionable_deeplink:
                    sg.actionableDeeplink = Deeplink.model_validate(bind_res.actionable_deeplink)
                if bind_res.validation_ref:
                    v_dict = {k: v for k, v in bind_res.validation_ref.items() if k != "inferred"}
                    sg.validationDeeplink = ValidationDeepLink.model_validate(v_dict)

    if hasattr(goal, "actions") and goal.actions:
        goal.actions = order_actions(goal.actions)

    return goal
