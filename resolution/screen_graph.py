"""N3 — Path-constrained screen resolution.

Finding F (FixFlow_Idea_v3.md) is confirmed by direct inspection: the
catalog carries no `Display > Navigation bar`-style breadcrumb field, so
there is no literal graph to build offline. What the catalog *does* carry
is a clean, verified signal for distinguishing a page-level entry from a
specific in-page control:

    originalType == "onClickURL"  <=>  message starts with "View..."
    (243/243 "View"-prefixed entries have onClickURL; verified by direct
    count against data/deeplinks.json, not assumed from the brief.)

onURL/offURL/updateURL entries are specific toggles/values that live ON a
page; onClickURL entries open the page itself. That single field is a far
more reliable "is this a parent screen or a leaf control" signal than
trying to parse a navigation hierarchy out of free-text prose.

The real parent-menu failure mode we measured (not hypothesized) is
subtler than "always prefer the deepest step": when a step group performs
MULTIPLE distinct actions on one page (e.g. "select nav type" AND "toggle
gesture hint" — the brief's own worked example), naive hybrid retrieval
latches onto whichever single sub-toggle has the strongest keyword overlap
with ONE of the two clauses, and misses that the correct target is the
shared parent page. Confirmed with data/deeplinks.json DL-0169 vs DL-0171 /
DL-0137 using the brief's Appendix-B example steps.

Resolution rule:
1. Split steps into navigation steps ("Tap on X.", "Navigate to X.",
   "Open X.") and action steps (everything else).
2. Take the deepest (last) navigation phrase as the breadcrumb anchor and
   filter retrieval candidates to those whose description/message contain
   it verbatim. Fall back to the unfiltered pool if that yields nothing
   (the doc's own documented fallback for when path parsing fails).
3. If there is exactly one action step AND it names something specific
   enough to match a non-page-level (onURL/offURL/updateURL) candidate on
   the filtered pool, prefer that leaf control.
4. Otherwise (zero, or more than one, distinct action step) prefer the
   page-level (onClickURL) candidate — the step group is configuring the
   page as a whole, not one control on it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from catalog.models import CatalogEntry
from resolution.retriever import HybridRetriever, RetrievalResult

_NAV_STEP_RE = re.compile(
    r"^(?:navigate to(?: and open)?|tap on|open)\s+(.+?)\.?\s*$", re.IGNORECASE
)
_GENERIC_BREADCRUMB_TERMS = {"settings", "settings menu", "the settings app"}


@dataclass
class ScreenResolution:
    status: str  # "matched" | "no_candidates"
    entry: Optional[CatalogEntry]
    is_page_level: bool
    breadcrumb: Optional[str]
    parent_menu_guard_applied: bool
    score: float


def split_steps(steps: list[str]) -> tuple[list[str], list[str]]:
    """Returns (navigation_steps_raw_phrases, action_steps)."""
    nav_phrases: list[str] = []
    action_steps: list[str] = []
    for step in steps:
        m = _NAV_STEP_RE.match(step.strip())
        if m:
            phrase = m.group(1).strip()
            if phrase.lower() not in _GENERIC_BREADCRUMB_TERMS:
                nav_phrases.append(phrase)
        else:
            action_steps.append(step)
    return nav_phrases, action_steps


def resolve_screen(
    retriever: HybridRetriever,
    steps: list[str],
    pool_size: int = 15,
) -> ScreenResolution:
    query = " ".join(steps)
    pool = retriever.search(query, top_k=pool_size)
    if not pool:
        return ScreenResolution("no_candidates", None, False, None, False, 0.0)

    nav_phrases, action_steps = split_steps(steps)
    breadcrumb = nav_phrases[-1] if nav_phrases else None

    on_path = pool
    if breadcrumb:
        needle = breadcrumb.lower()
        filtered = [
            r for r in pool
            if needle in r.entry.description.lower() or needle in r.entry.message.lower()
        ]
        if filtered:
            on_path = filtered
        # else: fall back to full pool — path parsing yielded no match (doc's
        # own documented fallback for when the breadcrumb doesn't resolve).

    page_level = [r for r in on_path if r.entry.originalType == "onClickURL"]
    leaf_level = [r for r in on_path if r.entry.originalType != "onClickURL"]

    guard_applied = False
    if len(action_steps) == 1 and leaf_level:
        # Exactly one specific action -> prefer the best-matching leaf
        # control over the page, provided one actually stands out on this
        # step's own text (not just the shared breadcrumb).
        action_query = action_steps[0]
        leaf_pool_scores = [
            (r, _term_overlap(action_query, r.entry)) for r in leaf_level
        ]
        # Stable sort on overlap alone: `leaf_level` already carries the
        # retriever's polarity-aware ordering (retriever.search() promotes
        # the query-matching Enable/Disable twin to the front of the list,
        # not by rewriting .score). Breaking ties on raw .score here would
        # silently undo that promotion, since the promoted item's stored
        # score doesn't change — only its list position does.
        leaf_pool_scores.sort(key=lambda pair: -pair[1])
        best_leaf, overlap = leaf_pool_scores[0]
        if overlap > 0:
            return ScreenResolution(
                "matched", best_leaf.entry, False, breadcrumb, guard_applied, best_leaf.score
            )

    if page_level:
        guard_applied = len(action_steps) != 1
        # Among page-level (onClickURL) candidates sharing the breadcrumb,
        # more than one can legitimately match it (e.g. "View Navigation
        # bar" and "View Show input method button on navigation bar" both
        # contain "navigation bar"). Prefer the one closest to the
        # breadcrumb itself — fewest EXTRA qualifier words beyond it — over
        # a more specific sub-page, since a multi-part step group targets
        # the general page, not a narrower one. Confirmed against the
        # brief's own worked example: DL-0169 ("View Navigation bar", 0
        # extra words) over DL-0527 ("View Show input method button on
        # navigation bar", 5 extra words).
        best_page = min(
            page_level,
            key=lambda r: (_extra_words_beyond_breadcrumb(r.entry, breadcrumb), -r.score),
        )
        return ScreenResolution(
            "matched", best_page.entry, True, breadcrumb, guard_applied, best_page.score
        )

    # No page-level candidate on this path at all — fall back to plain
    # top-1 hybrid result.
    best = on_path[0]
    return ScreenResolution(
        "matched",
        best.entry,
        best.entry.originalType == "onClickURL",
        breadcrumb,
        False,
        best.score,
    )


def _extra_words_beyond_breadcrumb(entry: CatalogEntry, breadcrumb: Optional[str]) -> int:
    """Word count in entry.message (minus a leading 'View ') that isn't
    already part of the breadcrumb phrase. Lower = closer to a pure page
    match for the breadcrumb; higher = a narrower sub-page."""
    message = entry.message
    if message.lower().startswith("view "):
        message = message[5:]
    msg_words = set(re.findall(r"[a-z]+", message.lower()))
    breadcrumb_words = set(re.findall(r"[a-z]+", (breadcrumb or "").lower()))
    return len(msg_words - breadcrumb_words)


def _term_overlap(action_text: str, entry: CatalogEntry) -> int:
    """Count of distinctive (len > 3) words shared between the action step
    text and the entry's own metadata, beyond generic filler."""
    stop = {"tap", "open", "turn", "select", "your", "that", "this", "with", "from"}
    action_words = {w for w in re.findall(r"[a-z]+", action_text.lower()) if len(w) > 3 and w not in stop}
    entry_words = {w for w in re.findall(r"[a-z]+", entry.searchable_text().lower()) if len(w) > 3 and w not in stop}
    return len(action_words & entry_words)


def merge_same_screen_actions(actions: list[dict]) -> list[dict]:
    """One Action = One Screen: merge consecutive actions whose resolved
    stepGroups all point at the same catalog deeplink into a single action.
    Actions are expected as dicts with 'stepGroups': [{'steps': [...],
    'actionableDeeplink': {'deeplink': str, ...} | None}, ...].
    Non-consecutive matches are intentionally NOT merged — merging distant
    actions in the plan would scramble ordering (safe-first, critical-last)
    for no benefit.
    """
    if not actions:
        return []

    def screen_key(action: dict) -> Optional[str]:
        links = {
            sg["actionableDeeplink"]["deeplink"]
            for sg in action.get("stepGroups", [])
            if sg.get("actionableDeeplink")
        }
        if len(links) == 1:
            return next(iter(links))
        return None  # mixed or unresolved screens -> never merge

    merged: list[dict] = [dict(actions[0])]
    merged[-1]["stepGroups"] = list(actions[0]["stepGroups"])

    for action in actions[1:]:
        prev_key = screen_key(merged[-1])
        cur_key = screen_key(action)
        if prev_key is not None and prev_key == cur_key:
            merged[-1]["stepGroups"].extend(action["stepGroups"])
        else:
            new_action = dict(action)
            new_action["stepGroups"] = list(action["stepGroups"])
            merged.append(new_action)

    return merged
