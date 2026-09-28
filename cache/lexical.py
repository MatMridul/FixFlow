"""Synonym-aware lexical similarity for paraphrase matching when a request
carries no SIIS article (brief §5: "semantic lookup against pre-warmed cache
entries").

The hashed char-trigram embedding scores most real paraphrases below its 0.82
threshold (median 0.76 on eval/paraphrases.json). This module adds a second,
word-level view: content words are canonicalised through a small complaint
synonym map (blank/black/dead, flicker/flash, lag/slow, ...), weighted by IDF
over the indexed queries, and compared by cosine. The cache blends both views.

It also exposes `setting_conflict`: two complaints that each name a Settings
feature the other lacks ("screen timeout" vs "brightness") are different
questions however similar the rest of the wording is. The feature vocabulary
comes from the deeplink catalog's labels.
"""
from __future__ import annotations

import json
import math
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Set

_SYNONYMS = [
    ("black", "blank", "dark", "dead", "nothing", "blackout"),
    ("flicker", "flash", "blink", "flickering", "flashing", "flickers", "flashes", "strobe", "glitch"),
    ("crack", "cracked", "shatter", "shattered", "broken", "smashed"),
    ("lag", "laggy", "slow", "delay", "delayed", "sluggish"),
    ("screen", "display", "panel"),
    ("phone", "device", "galaxy", "samsung", "tablet", "mobile"),
    ("crash", "crashes", "crashing", "closes", "stops", "stopped"),
    ("charge", "charging", "charger"),
    ("drain", "drains", "dies", "dying", "loses", "drop", "drops"),
]
_CANON: Dict[str, str] = {}
for _group in _SYNONYMS:
    for _w in _group:
        _CANON.setdefault(_w, _group[0])

_STOP = set(
    "a an the my i me is it its and or to of on in at for with when while after before just then "
    "but so this that be been being am are was were do does did have has had can cant wont not no any "
    "some every all very really super like how what why fix help please get keeps keep still also now "
    "again even only there their they you your our we us from into out up down about would could should".split()
)
_MODEL_RE = re.compile(r"\b[A-Za-z]{0,2}\d+[A-Za-z0-9+/]*\b")  # model numbers: A115G, S24, 120Hz


def tokens(text: str) -> List[str]:
    text = _MODEL_RE.sub(" ", text)
    out = []
    for w in re.findall(r"[a-z']+", text.lower()):
        w = w.strip("'")
        if w in _STOP or len(w) < 3:
            continue
        w = _CANON.get(w, w[:-1] if w.endswith("s") and len(w) > 4 else w)
        out.append(_CANON.get(w, w))
    return out


def idf_table(documents: Iterable[Iterable[str]]) -> Dict[str, float]:
    """IDF over *plans*, each document being one plan's query + variations.
    Counting per key instead gave the words every variation shares ("tablet",
    "screen", "black") near-zero weight. +1 keeps weights positive when only
    one or two plans are cached."""
    docs = [set(w for t in doc for w in tokens(t)) for doc in documents]
    df: Dict[str, int] = {}
    for d in docs:
        for w in d:
            df[w] = df.get(w, 0) + 1
    n = len(docs)
    return {w: math.log((n + 1) / (c + 0.5)) + 1.0 for w, c in df.items()}


def vector(text: str, idf: Dict[str, float]) -> Dict[str, float]:
    v: Dict[str, float] = {}
    for w in tokens(text):
        v[w] = v.get(w, 0.0) + idf.get(w, 1.0)
    norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
    return {k: x / norm for k, x in v.items()}


def cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
    return sum(x * b.get(k, 0.0) for k, x in a.items())


_GENERIC = set(
    "enable disable view check adjust open opens enables disables updates specified value settings "
    "setting device page screen mode show turn off with from your the and for use using when default "
    "auto automatic more other options option all app apps phone galaxy samsung display black".split()
)


@lru_cache(maxsize=1)
def _setting_vocabulary() -> Set[str]:
    path = Path(__file__).resolve().parent.parent / "data" / "deeplinks.json"
    try:
        catalog = json.loads(path.read_text(encoding="utf-8"))["deeplinks"]
    except Exception:
        return set()
    vocab: Set[str] = set()
    for entry in catalog:
        vocab.update(w for w in tokens(entry.get("message", "")) if w not in _GENERIC and len(w) > 3)
    return vocab


def setting_conflict(a: str, b: str) -> bool:
    vocab = _setting_vocabulary()
    sa = {w for w in tokens(a) if w in vocab}
    sb = {w for w in tokens(b) if w in vocab}
    return bool(sa - sb) and bool(sb - sa)
