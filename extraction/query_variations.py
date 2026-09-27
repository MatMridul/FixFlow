"""Query paraphrases for the results file's `query_variations` field.

FAQ Q16: each results.jsonl line needs 8-10 unique paraphrases of the query,
diverse in vocabulary, structure and formality — the scorer measures lexical
diversity. The LLM path generates these in the same call as extraction; this
module is the deterministic fallback (and pads an LLM answer that comes back
short), spreading one complaint across registers: formal, casual, question,
keyword-only, frustrated, and typo-inclusive.
"""
from __future__ import annotations

import re
from typing import List, Optional

MIN_VARIATIONS = 8
MAX_VARIATIONS = 10

_CLAUSE_CUT_RE = re.compile(
    r"[,;:—\"]|\.\s|\s(?:so|and then|whenever|when|after|because|while|which|that)\s", re.I
)

# Tokens that name the device model rather than the problem ("Galaxy Z Flip 7").
_MODEL_WORDS = {
    "my", "new", "samsung", "galaxy", "z", "flip", "fold", "ultra", "plus", "fe", "pro",
    "note", "tab", "edge", "lite", "s", "a", "m",
}
_SUBJECT_NOUNS = {
    "screen", "display", "touchscreen", "phone", "tablet", "device", "inner", "main",
    "outer", "cover", "phone's", "tablet's", "device's",
}
_DANGLING_TAIL = {"it", "where", "the", "and", "or", "a", "an", "of", "to", "my", "right", "again", "with", "tiny", "in"}

_TYPOS = {
    "screen": "scren", "black": "blak", "blank": "blnak", "phone": "phnoe",
    "display": "dispaly", "flickers": "flikers", "cracked": "craked",
    "touch": "tuch", "working": "workin", "tablet": "tabelt", "turn": "trun",
}

_FRUSTRATED_OPENERS = ["Ugh, ", "Seriously, ", "This is so annoying — "]


def _subject_predicate(query: str) -> tuple[str, str]:
    """Split "My Galaxy Z Flip 7 inner screen stopped working by itself; ..."
    into ("inner screen", "stopped working by itself"). Templates only ever
    use "<subject> <predicate>" with the predicate's own verb form, so they
    stay grammatical ("my screen turns blank", never "why does ... turns")."""
    q = re.sub(r"^\W*\d+\.\s*", "", query.strip()).strip().strip('"').strip()
    tokens = q.split()
    i = 0
    while i < len(tokens) and (
        tokens[i].lower().strip(",") in _MODEL_WORDS or re.search(r"\d|\*|/", tokens[i])
    ):
        i += 1
    subj = []
    while i < len(tokens) and tokens[i].lower().strip(",") in _SUBJECT_NOUNS:
        subj.append(tokens[i].lower().strip(","))
        i += 1
    subject = " ".join(subj) or "phone"
    subject = subject.replace("phone's ", "").replace("tablet's ", "").replace("device's ", "")
    rest = " ".join(tokens[i:])
    predicate = _CLAUSE_CUT_RE.split(rest, maxsplit=1)[0].strip().rstrip(".").strip('"')
    words = predicate.split()[:9]
    while words and words[-1].lower() in _DANGLING_TAIL:
        words.pop()
    predicate = " ".join(words) or "is not working properly"
    return subject, predicate[0].lower() + predicate[1:]


def _core_problem(query: str) -> str:
    subject, predicate = _subject_predicate(query)
    return f"{subject} {predicate}"


def _typo(text: str) -> str:
    out = text
    for good, bad in _TYPOS.items():
        new = re.sub(rf"\b{good}\b", bad, out, count=1, flags=re.I)
        if new != out:
            return new
    return out.replace("e", "", 1)


def generate_query_variations(query: str, topic: Optional[str] = None) -> List[str]:
    subject, predicate = _subject_predicate(query)
    topic_l = (topic or "screen problem").lower()
    opener = _FRUSTRATED_OPENERS[len(query) % len(_FRUSTRATED_OPENERS)]

    candidates = [
        f"The {subject} on my Samsung Galaxy {predicate}.",
        f"My Galaxy {subject} {predicate} — how do I fix this?",
        f"Hey, my {subject} {predicate}, any idea what to do?",
        f"{topic_l} galaxy fix",
        f"{opener}my {subject} {predicate} again and nothing helps.",
        f"How can I troubleshoot a {topic_l} problem on a Samsung phone?",
        _typo(f"samsung {subject} {predicate} pls help"),
        f"Samsung {topic_l} - which settings should I check?",
        f"{subject.capitalize()} {predicate} on Galaxy: steps to resolve",
        f"Is it a hardware fault when the {subject} {predicate}?",
        f"{topic_l} samsung not fixed after restart",
    ]

    seen, out = set(), []
    for c in candidates:
        c = re.sub(r"\s+", " ", c).strip()
        key = c.lower()
        if key not in seen and key != query.strip().lower():
            seen.add(key)
            out.append(c)
        if len(out) >= MAX_VARIATIONS:
            break
    return out


def merge_variations(llm_variations: Optional[List[str]], query: str, topic: Optional[str] = None) -> List[str]:
    """Keep the LLM's paraphrases, dedupe, pad from the deterministic set up
    to the 8 minimum, cap at 10."""
    out, seen = [], {query.strip().lower()}
    for v in (llm_variations or []) + generate_query_variations(query, topic):
        if not isinstance(v, str):
            continue
        v = v.strip()
        if v and v.lower() not in seen and "http" not in v.lower():
            seen.add(v.lower())
            out.append(v)
        if len(out) >= MAX_VARIATIONS:
            break
    return out
