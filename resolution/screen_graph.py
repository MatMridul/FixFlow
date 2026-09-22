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
_FILTER_DISTRUST_MARGIN = 0.3


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
            # Trust the filter only if it isn't discarding a much stronger
            # unfiltered match. Found this failing on a real case: querying
            # for the "Date and time" screen, DL-0001's own description
            # never says "date and time" (it's phrased "24-hour time format
            # settings page"), so the breadcrumb filter wrongly dropped the
            # correct top-scoring candidate (1.0) in favour of a filtered
            # candidate scoring 0.33. The filter helps when candidates are
            # close (the navigation-bar case) but actively hurts when the
            # true answer just doesn't echo the UI's own nav-menu wording.
            best_unfiltered = pool[0].score
            best_filtered = max(r.score for r in filtered)
            if best_unfiltered - best_filtered > _FILTER_DISTRUST_MARGIN:
                on_path = pool
            else:
                on_path = filtered
        # else: fall back to full pool — path parsing yielded no match (doc's
        # own documented fallback for when the breadcrumb doesn't resolve).

    page_level = [r for r in on_path if r.entry.originalType == "onClickURL"]
    leaf_level = [r for r in on_path if r.entry.originalType != "onClickURL"]

    # leaf_level/page_level preserve on_path's order, which already carries
    # the retriever's polarity-aware promotion (search() reorders the list
    # without rewriting .score) — take [0], never re-sort by raw .score,
    # or the promotion (Enable/Disable twin fix) gets silently undone.
    best_leaf = leaf_level[0] if leaf_level else None
    best_page = _best_page_candidate(page_level, breadcrumb) if page_level else None

    guard_applied = False
    if len(action_steps) > 1 and best_page is not None:
        # Multi-part step group (>=2 distinct action clauses) -> the group
        # is configuring the page as a whole, not one control on it. This
        # bias is intentionally stronger than a plain score comparison —
        # it's what fixes the brief's own worked example, where the
        # correct page (DL-0169) scores LOWER than either single-clause
        # sub-toggle match (DL-0171, DL-0527) on raw hybrid score alone.
        guard_applied = True
        return ScreenResolution(
            "matched", best_page.entry, True, breadcrumb, guard_applied, best_page.score
        )

    if best_leaf is not None and (best_page is None or best_leaf.score >= best_page.score):
        # Zero or one action clause: trust whichever candidate the
        # retriever itself scored higher. Do NOT gate this on "does the
        # leaf share any word with the action step" — that let a page-only
        # feature (DL-0001, "Switch Time Format", no separate toggle
        # exists) get overridden by an unrelated but keyword-adjacent leaf
        # toggle ("Enable Auto Time") every time a plausible leaf existed
        # at all, regardless of how much stronger the page's own score was.
        return ScreenResolution(
            "matched", best_leaf.entry, False, breadcrumb, guard_applied, best_leaf.score
        )

    if best_page is not None:
        return ScreenResolution(
            "matched", best_page.entry, True, breadcrumb, guard_applied, best_page.score
        )

    best = on_path[0]
    return ScreenResolution(
        "matched",
        best.entry,
        best.entry.originalType == "onClickURL",
        breadcrumb,
        False,
        best.score,
    )


_PAGE_TIE_MARGIN = 0.05


def _best_page_candidate(
    page_level: list[RetrievalResult], breadcrumb: Optional[str]
) -> RetrievalResult:
    """Pick the best page-level (onClickURL) candidate. The extra-words
    tie-break (fewest qualifier words beyond the breadcrumb — prefers "View
    Navigation bar" over "View Show input method button on navigation bar")
    is only trustworthy among candidates that are ALREADY close in raw
    retrieval score. Found this the hard way: when page_level contains
    unrelated low-score entries with coincidentally short messages (e.g.
    "View Format", about screenshots, scoring 0.25 on a "date and time"
    query), applying the tie-break as the PRIMARY sort key picked that
    irrelevant short entry over the correct high-score one (DL-0001,
    score 1.0). Gate the tie-break to near-top-score candidates only.
    """
    top_score = max(r.score for r in page_level)
    near_top = [r for r in page_level if top_score - r.score <= _PAGE_TIE_MARGIN]
    return min(near_top, key=lambda r: _extra_words_beyond_breadcrumb(r.entry, breadcrumb))


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
