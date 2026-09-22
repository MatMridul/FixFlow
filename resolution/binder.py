"""Contract 1 (FixFlow_TwoDev_Plan.md §4): Dev A hands Dev B a Goal object
whose stepGroups have step text but empty deeplink fields. This module fills
`actionableDeeplink` (and as much of `validationDeeplink` as the catalog
itself supplies).

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
from typing import Optional

from catalog.loader import Catalog
from catalog.models import CatalogEntry
from resolution.retriever import HybridRetriever

DEFAULT_THRESHOLD = 0.12


@dataclass
class BindResult:
    status: str  # "matched" | "manual_no_deeplink" | "below_threshold" | "no_catalog_entries"
    actionable_deeplink: Optional[dict]
    validation_ref: Optional[dict]
    top_score: float
    candidate: Optional[CatalogEntry]  # best guess even when below threshold, for human/LLM review


def _to_actionable_deeplink(entry: CatalogEntry) -> dict:
    return {
        "deeplink": entry.deeplink,
        "description": entry.description,
        "message": entry.message,
        "originalType": entry.originalType,
    }


def _to_validation_ref(entry: CatalogEntry) -> Optional[dict]:
    """Copy whatever the catalog supplies verbatim. For the ~24% of entries
    with a full validation object, this fully satisfies N4 with no
    derivation. For the rest (deeplink+key only), resultType/condition/value
    stay None here — Dev A's extraction layer derives them from SIIS text."""
    if entry.validation is None:
        return None
    ref = {"deeplink": entry.validation.deeplink, "key": entry.validation.key}
    if entry.validation.resultType is not None:
        ref["resultType"] = entry.validation.resultType
        ref["condition"] = entry.validation.condition
        ref["value"] = entry.validation.value
    return ref


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

    query = " ".join(steps)
    results = retriever.search(query, top_k=1)
    if not results:
        return BindResult(
            status="below_threshold",
            actionable_deeplink=None,
            validation_ref=None,
            top_score=0.0,
            candidate=None,
        )

    best = results[0]
    if best.score >= threshold:
        return BindResult(
            status="matched",
            actionable_deeplink=_to_actionable_deeplink(best.entry),
            validation_ref=_to_validation_ref(best.entry),
            top_score=best.score,
            candidate=best.entry,
        )

    return BindResult(
        status="below_threshold",
        actionable_deeplink=None,
        validation_ref=None,
        top_score=best.score,
        candidate=best.entry,
    )
