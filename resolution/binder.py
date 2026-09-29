"""Contract 1 (FixFlow_TwoDev_Plan.md §4): Dev A hands Dev B a Goal object
whose stepGroups have step text but empty deeplink fields. This module fills
`actionableDeeplink` and `validationDeeplink`, and reports the Contract 2
signals (`retrieval_margin`, `path_alignment`) that feed the N5 calibrator.

Matching is delegated to resolution.screen_graph.resolve_screen (N3), which
applies the parent-menu guard rather than raw top-1 hybrid score.

Deeplink rules, from the hackathon FAQ (Q5, Q7, Q15) — these supersede the
earlier idea-doc reading:
- `auto` actions MUST carry an actionableDeeplink ("missing deeplinks on auto
  actions lose points"). When nothing in the catalog matches, use
  `bixby://dummy_positive` with our own 5-7 word description and message
  naming the concrete Settings screen — never leave it empty.
- `manual` and `critical` deeplinks are optional. We keep manual ones off (a
  physical step like "inspect the cable" has no Settings screen), and bind
  critical ones only when the steps really navigate to a Settings screen —
  "Force a Restart" via hardware buttons would otherwise get a junk link.
- validationDeeplink is copied from the catalog entry's `validation` object
  (verbatim where full; see resolution.validation_inference for the rest).

Confidence gate: `resolve_screen` scores are min-max normalized per query, so
the top candidate always looks like ~1.0 — even "Bake a chocolate cake"
matched "Enable Slow Keys" at 0.80. The gate therefore uses `raw_cosine`, the
absolute TF-IDF relevance, which is 0.0 for that nonsense query.
"""
from __future__ import annotations

import re
import threading
from dataclasses import dataclass, field
from typing import Any, Optional, Tuple

from catalog.loader import Catalog
from catalog.models import CatalogEntry
from resolution.retriever import HybridRetriever
from resolution.screen_graph import _LEAF_STOPWORDS, _stems, merge_same_screen_actions, resolve_screen, split_steps
from resolution.validation_inference import infer_validation_ref

# Absolute relevance floor (raw TF-IDF cosine). Measured: the official
# sample's correct match scores 0.133 and unrelated text scores 0.000, so the
# floor has to be low — it is a garbage gate, not a quality ranker. Physical
# steps are kept away from Settings links by category (manual), not by this.
DEFAULT_THRESHOLD = 0.05
_CRITICAL_MIN_RAW = 0.10
_STRONG_RAW = 0.30  # raw cosine at/above which retrieval confidence counts as full

DUMMY_POSITIVE_URI = "bixby://dummy_positive"


@dataclass
class BindResult:
    status: str  # "matched" | "dummy_positive" | "manual_no_deeplink" | "critical_no_screen" | "below_threshold" | "no_catalog_entries"
    actionable_deeplink: Optional[dict]
    validation_ref: Optional[dict]
    top_score: float
    candidate: Optional[CatalogEntry]  # best guess even when below threshold, for human/LLM review
    is_page_level: bool = False
    parent_menu_guard_applied: bool = False
    raw_cosine: float = 0.0
    path_alignment: float = 0.0
    breadcrumb: Optional[str] = None


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


def _fit_words(text: str, lo: int = 5, hi: int = 7) -> str:
    words = text.split()[:hi]
    filler = ["on", "your", "device"]
    while len(words) < lo and filler:
        words.append(filler.pop(0))
    return " ".join(words)


def _dummy_positive_deeplink(
    steps: list[str],
    action_name: Optional[str],
    fallback_uri: Optional[str] = None,
) -> dict:
    """FAQ Q15: dummy_positive needs our own 5-7 word description and a
    message naming the concrete Settings screen from the steps."""
    labels, _ = split_steps(steps)
    screen = labels[-1] if labels else re.sub(r"^(?:Adjust|Check|Review|Change|Turn|Use|Set)\s+", "", action_name or "Settings")
    screen = screen.strip() or "Settings"
    uri = fallback_uri or DUMMY_POSITIVE_URI
    return {
        "deeplink": uri,
        "description": _fit_words(f"Opens the {screen} screen in Settings"),
        "message": _fit_words(f"Open {screen} in device Settings"),
        "originalType": "placeholder",
    }


def _path_alignment(entry: CatalogEntry, breadcrumb: Optional[str]) -> float:
    """Contract 2 signal: does the chosen screen sit on the path the steps
    navigate? 1.0 = the entry names the breadcrumb screen, 0.6 = no
    breadcrumb to check (no evidence either way), 0.3 = it doesn't."""
    if not breadcrumb:
        return 0.6
    needle = breadcrumb.lower()
    return 1.0 if needle in entry.description.lower() or needle in entry.message.lower() else 0.3


# Gesture/navigation verbs appear in almost every step list ("Swipe down to
# open Quick settings"), so they can't show that a label is really present.
_GESTURE_WORDS = {"swipe", "tap", "open", "select", "touch", "hold", "press", "more", "options"}


def _label_supported(entry: CatalogEntry, steps: list[str], action_name: Optional[str] = None) -> bool:
    """At least two distinctive label words (or all, if the label has one) must
    appear in the steps/action name. A label with nothing distinctive left
    ("Enable Swipe for pop-up view") can't vouch for the match."""
    label = _stems(entry.message) - _LEAF_STOPWORDS - _GESTURE_WORDS
    if not label:
        return False
    shared = label & _stems(" ".join(steps) + " " + (action_name or ""))
    return len(shared) >= min(2, len(label))


def _confident(resolution, steps: list[str], action_name: Optional[str], threshold: float) -> bool:
    """A screen match needs strong lexical overlap, or the screen's own label
    must show up in the steps. LLM-written steps exposed weak matches that
    cleared the 0.05 garbage gate: "Tap Clear cache" -> Storage Share (raw
    0.12), "Tap Smart View" -> Swipe for pop-up view (0.19). The official
    sample's backup step (raw 0.13, label "Back up data" in the steps) passes."""
    if threshold <= 0.0:
        return True  # callers asking for "any match" (tests, eval sweeps)
    if resolution.raw_cosine >= _STRONG_RAW:
        return True
    return _label_supported(resolution.entry, steps, action_name)


def _label_covered(entry: CatalogEntry, steps: list[str], action_name: Optional[str]) -> bool:
    """Disruptive actions only link to a screen whose whole label is in the
    steps: "Factory data reset" must not open "Auto factory reset"."""
    label = _stems(entry.message) - _LEAF_STOPWORDS
    return bool(label) and label <= _stems(" ".join(steps) + " " + (action_name or ""))


def _mentions_settings(steps: list[str]) -> bool:
    return bool(re.search(r"\bsettings?\b", " ".join(steps), re.I))


def bind_actionable_deeplink(
    steps: list[str],
    category: str,
    catalog: Catalog,
    retriever: HybridRetriever,
    threshold: float = DEFAULT_THRESHOLD,
    action_name: Optional[str] = None,
) -> BindResult:
    category = getattr(category, "value", category)

    if category == "manual":
        return BindResult("manual_no_deeplink", None, None, 0.0, None)

    if len(catalog.resolvable_entries()) == 0:
        return BindResult("no_catalog_entries", None, None, 0.0, None)

    resolution = resolve_screen(retriever, steps)
    matched = resolution.status == "matched" and resolution.raw_cosine >= threshold
    if matched and not _confident(resolution, steps, action_name, threshold):
        matched = False

    if category == "critical":
        # Optional per FAQ Q7 — only link when the steps really go through
        # Settings and the screen match is solid.
        if (
            matched
            and _mentions_settings(steps)
            and resolution.raw_cosine >= _CRITICAL_MIN_RAW
            and _label_covered(resolution.entry, steps, action_name)
        ):
            return BindResult(
                "matched",
                _to_actionable_deeplink(resolution.entry),
                _to_validation_ref(resolution.entry),
                resolution.score,
                resolution.entry,
                resolution.is_page_level,
                resolution.parent_menu_guard_applied,
                resolution.raw_cosine,
                _path_alignment(resolution.entry, resolution.breadcrumb),
                resolution.breadcrumb,
            )
        return BindResult(
            "critical_no_screen", None, None, resolution.score, resolution.entry,
            raw_cosine=resolution.raw_cosine, breadcrumb=resolution.breadcrumb,
        )

    if matched:
        return BindResult(
            "matched",
            _to_actionable_deeplink(resolution.entry),
            _to_validation_ref(resolution.entry),
            resolution.score,
            resolution.entry,
            resolution.is_page_level,
            resolution.parent_menu_guard_applied,
            resolution.raw_cosine,
            _path_alignment(resolution.entry, resolution.breadcrumb),
            resolution.breadcrumb,
        )

    # auto + no confident catalog match -> dummy_positive, never empty (FAQ Q15).
    dummy_uri = getattr(catalog, "dummy_positive_uri", DUMMY_POSITIVE_URI)
    return BindResult(
        "dummy_positive",
        _dummy_positive_deeplink(steps, action_name, fallback_uri=dummy_uri),
        None,
        resolution.score,
        resolution.entry,
        raw_cosine=resolution.raw_cosine,
        path_alignment=0.5,
        breadcrumb=resolution.breadcrumb,
    )


_shared: dict = {}
_shared_lock = threading.Lock()


def _shared_catalog_and_retriever() -> Tuple[Catalog, HybridRetriever]:
    """Build the catalog + BM25/TF-IDF index once per process. The previous
    default rebuilt both on every request, adding avoidable latency to every
    cold call (brief target: cold P95 <= 8 s)."""
    with _shared_lock:
        if "retriever" not in _shared:
            from catalog.loader import load_catalog

            catalog = load_catalog()
            _shared["catalog"] = catalog
            _shared["retriever"] = HybridRetriever(catalog)
        return _shared["catalog"], _shared["retriever"]


@dataclass
class ResolutionStats:
    """Contract 2 output (Dev B -> Dev A's calibrate())."""
    retrieval_margin: float = 1.0
    path_alignment: float = 1.0
    bound: int = 0
    dummy_positive: int = 0
    unresolved: int = 0
    details: list = field(default_factory=list)


def resolve_goal_deeplinks_with_stats(
    goal: Any,
    catalog: Optional[Catalog] = None,
    retriever: Optional[HybridRetriever] = None,
    threshold: float = DEFAULT_THRESHOLD,
) -> Tuple[Any, ResolutionStats]:
    """Contract 1 & Novelty N3/N4: bind deeplinks on every StepGroup, merge
    consecutive actions that land on the same screen (One Action = One
    Screen), order safe-first, and return the Contract 2 signals."""
    from resolution.ordering import order_actions
    from schema import Action, Deeplink, ValidationDeepLink

    if catalog is None or retriever is None:
        shared_catalog, shared_retriever = _shared_catalog_and_retriever()
        catalog = catalog or shared_catalog
        retriever = retriever or shared_retriever

    stats = ResolutionStats()
    margins, alignments = [], []

    for action in getattr(goal, "actions", []):
        category_str = action.category.value if hasattr(action.category, "value") else str(action.category or "manual")
        for sg in getattr(action, "stepGroups", []):
            res = bind_actionable_deeplink(
                steps=sg.steps,
                category=category_str,
                catalog=catalog,
                retriever=retriever,
                threshold=threshold,
                action_name=action.actionName,
            )
            if res.actionable_deeplink:
                sg.actionableDeeplink = Deeplink.model_validate(res.actionable_deeplink)
            if res.validation_ref:
                sg.validationDeeplink = ValidationDeepLink.model_validate(
                    {k: v for k, v in res.validation_ref.items() if k != "inferred"}
                )
            if res.status == "matched":
                stats.bound += 1
                margins.append(min(1.0, res.raw_cosine / _STRONG_RAW))
                alignments.append(res.path_alignment)
            elif res.status == "dummy_positive":
                stats.dummy_positive += 1
                margins.append(min(1.0, res.raw_cosine / _STRONG_RAW) * 0.5)
                alignments.append(res.path_alignment)
            elif res.status in ("below_threshold", "no_catalog_entries"):
                stats.unresolved += 1
            stats.details.append({
                "action": action.actionName,
                "status": res.status,
                "entry": res.candidate.id if res.candidate else None,
                "raw_cosine": round(res.raw_cosine, 3),
                "breadcrumb": res.breadcrumb,
            })

    if margins:
        stats.retrieval_margin = round(sum(margins) / len(margins), 3)
        stats.path_alignment = round(sum(alignments) / len(alignments), 3)
    # else: a manual/critical-only plan never depended on retrieval — neutral 1.0.

    if getattr(goal, "actions", None):
        merged = merge_same_screen_actions([a.model_dump() for a in goal.actions])
        goal.actions = order_actions([Action.model_validate(a) for a in merged])

    return goal, stats


def resolve_goal_deeplinks(
    goal: Any,
    catalog: Optional[Catalog] = None,
    retriever: Optional[HybridRetriever] = None,
    threshold: float = DEFAULT_THRESHOLD,
) -> Any:
    """Goal-only wrapper kept for callers that don't consume Contract 2."""
    return resolve_goal_deeplinks_with_stats(goal, catalog, retriever, threshold)[0]
