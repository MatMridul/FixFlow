"""Deterministic (no-LLM) SIIS -> Goal extraction.

Used when no LLM key is configured or every provider in the chain fails, so
the API still returns a schema-valid, grounded plan during judging.

The previous fallback emitted each SIIS section's raw prose as "steps"
("I understand you're having trouble...") and tagged nearly everything
`auto`. Inspecting all 20 SIIS docs shows a consistent shape to exploit:

    "<category prefix> <title> (<categories>): # Doc title
     conversational intro
     ## / ### [Step N: | N.] Section heading
     conversational prose with imperative instructions embedded in it"

So: split on headings, turn each section's instruction sentences into
imperative steps (strip "please", "let's", "First,", "you can"...), drop
chatter, and categorize by what the steps actually make the user do —
following the brief's definitions: `critical` = disruptive/irreversible
(restart, reset, safe mode, software update), `manual` = physical
intervention (inspect, charge, remove a case, service centre), `auto` =
on-device Settings UI.

Every step is a cleaned-up SIIS sentence, never invented text, so the N5
provenance filter still grounds it.
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

from schema import Action, Goal, StepGroup, actionCategory

MAX_ACTIONS = 8
MAX_STEPS_PER_ACTION = 6
MAX_STEP_WORDS = 40

# Conversational filler that survives softener-stripping as a pseudo-instruction
# ("Let's go through some steps together to see if we can resolve this.").
_CHATTER_RE = re.compile(
    r"\b(?:go through (?:some|these|the following)|see if we can|help resolve this|"
    r"help you resolve|walk you through|we can resolve)\b",
    re.I,
)

_HEADING_RE = re.compile(r"^(#{1,4})\s+(.+?)\s*$", re.M)
_STEP_PREFIX_RE = re.compile(r"^(?:step\s*\d+\s*[:.\-]?|\d+\s*[.)])\s*", re.I)
_PREFIX_RE = re.compile(r"^.*?\):\s*", re.S)  # "<categories> <title> ( <categories> ): "

_DISCOURSE_RE = re.compile(
    r"^(?:first|firstly|next|then|now|also|finally|lastly|additionally|afterwards|"
    r"after that|after charging|once (?:done|complete|completed)|alternatively|"
    r"to do this|to check this|in this case|simply|instead|otherwise)\s*,?\s+",
    re.I,
)
_SOFTENER_RE = re.compile(
    r"^(?:please\s+|let'?s\s+|kindly\s+|you (?:can|could|may|might|should|will need to|need to|may need to|can also|could also)\s+(?:also\s+)?|"
    r"we recommend (?:that you )?|it(?:'s| is) (?:recommended|best) to\s+|be sure to\s+|make sure to\s+)",
    re.I,
)

# First words that make a sentence an actionable instruction.
_IMPERATIVE_VERBS = {
    "access", "adjust", "allow", "back", "check", "choose", "clean", "clear", "close",
    "confirm", "connect", "contact", "create", "customize", "delete", "disable",
    "disconnect", "download", "drag", "eject", "enable", "ensure", "enter", "examine",
    "exit", "follow", "force", "go", "hold", "insert", "inspect", "install", "launch",
    "leave", "let", "locate", "log", "make", "move", "navigate", "open", "perform",
    "place", "plug", "power", "press", "reinsert", "remove", "rename", "reopen", "replace",
    "reset", "restart", "restore", "review", "run", "schedule", "scroll", "select",
    "send", "set", "shine", "sign", "slide", "start", "swipe", "switch", "take", "tap",
    "touch", "try", "turn", "uninstall", "unplug", "update", "use", "verify", "visit",
    "wait", "wipe",
}

_CRITICAL_TERMS = (
    "factory data reset", "factory reset", "reset your", "reset the", "wipe", "erase",
    "force a restart", "force restart", "forcing a restart", "restart", "reboot",
    "safe mode", "software update", "software updates", "update the software", "firmware", "recovery mode",
)
_MANUAL_TERMS = (
    "inspect", "examine", "liquid", "physical damage", "charger", "charging port",
    "usb cable", "cable", "charge", "screen protector", "protective film", "case",
    "sim", "tray", "ejector", "flashlight", "remove the battery", "battery for",
    "service center", "service centre", "repair", "contact", "samsung support",
    "visit", "walk-in", "mail-in", "premium care", "on a pc", "computer",
    "usb mouse", "keyboard", "monitor", "adapter",
)
_AUTO_TERMS = (
    "settings", "tap", "swipe", "toggle", "turn on", "turn off",
    "enable", "disable", "quick settings", "menu", "select", "edge panel",
    "navigation bar", "display", "accessibility", "icon", "app", "window",
    "drag", "home screen",
)


def _count_terms(text: str, terms) -> int:
    """Whole-word/phrase matches only — plain substring matching made
    "swipe" match "wipe" (-> critical) and "similar" match "sim" (-> manual)."""
    return sum(bool(re.search(rf"\b{re.escape(t.strip())}\b", text)) for t in terms)

_INFORMATIONAL_HEADINGS = re.compile(
    r"^(?:understanding|factors|about|overview|introduction|useful|why|what is|"
    r"troubleshoot(?:ing)?(?: steps)?(?: for)?|service options)\b",
    re.I,
)

# (topic, title) keyed by intent-signature symptom, then component.
_SYMPTOM_TOPIC = {
    "flicker": ("Screen Flicker", "Screen flicker issue"),
    "blank": ("Blank Screen", "Blank screen issue"),
    "damage": ("Cracked Screen", "Cracked screen repair"),
    "slow": ("Touch Responsiveness", "Slow touch response"),
    "freeze": ("Frozen Screen", "Frozen screen issue"),
    "drain": ("Battery Drain", "Battery drain issue"),
    "overheat": ("Device Overheating", "Device overheating issue"),
}
_COMPONENT_TOPIC = {
    "touch": ("Touchscreen", "Unresponsive touchscreen"),
    "brightness": ("Display Brightness", "Display brightness issue"),
    "charging": ("Charging", "Charging issue"),
    "screen_damage": ("Cracked Screen", "Cracked screen repair"),
    "wifi": ("Wi-Fi Connection", "Wi-Fi connection issue"),
    "bluetooth": ("Bluetooth Connection", "Bluetooth connection issue"),
}

_DESCRIPTION_RULES: List[Tuple[Tuple[str, ...], str]] = [
    (("factory data reset", "factory reset"), "It will restore factory default settings"),
    (("safe mode",), "It will isolate problems from downloaded apps"),
    (("software update", "update the software", "firmware", "updates"), "It will install the latest software fixes"),
    (("restart", "reboot"), "It will clear temporary glitches by restarting"),
    (("liquid", "physical damage", "inspect", "examine"), "It will rule out physical damage"),
    (("charge", "charger", "charging"), "It will restore battery power to start"),
    (("screen protector", "protective film", "case"), "It will remove accessories blocking touch input"),
    (("service center", "repair", "support", "premium care", "further assistance"), "It will connect you with Samsung repair"),
    (("back up", "backup", "smart switch", "transfer"), "It will keep your personal data safe"),
    (("touch sensitivity",), "It will improve touch response with protectors"),
    (("gesture", "navigation"), "It will adjust how screen gestures behave"),
    (("rotate", "rotation"), "It will control automatic screen rotation"),
    (("brightness", "dark mode", "display"), "It will adjust display settings for clarity"),
    (("wi-fi", "wifi", "connection", "network", "mobile data"), "It will verify your network connection works"),
    (("email", "account"), "It will reconnect your email account"),
    (("multi window", "pop-up", "app pair", "edge panel"), "It will manage split screen app windows"),
    (("mouse", "keyboard", "monitor"), "It will let you control it externally"),
    (("power on", "power button", "turn it on"), "It will check whether the device starts"),
]


def _title_case(text: str) -> str:
    minor = {"a", "an", "the", "and", "but", "or", "for", "nor", "on", "at", "to", "from", "by", "with", "in", "of"}
    words = re.sub(r"[^\w\s/-]", "", text).split()
    out = []
    for i, w in enumerate(words):
        if w.isupper() and len(w) > 1:  # keep acronyms (USB, SIM, PIN)
            out.append(w)
        elif i > 0 and w.lower() in minor:
            out.append(w.lower())
        else:
            out.append(w[:1].upper() + w[1:])
    return " ".join(out)


def _split_sentences(text: str) -> List[str]:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"([a-z)])\.(?=[A-Z])", r"\1. ", text)  # "view.When" -> "view. When"
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip() for p in parts if p.strip()]


def _to_imperative(sentence: str) -> Optional[str]:
    """Return an imperative step derived from `sentence`, or None if the
    sentence isn't an instruction (chatter, explanation, expected outcome)."""
    s = sentence.strip().rstrip(":")
    if not s or "http" in s.lower() or "www." in s.lower() or _CHATTER_RE.search(s):
        return None
    # "Close app: Close the current pop-up view window." -> keep the instruction.
    label = re.match(r"^[^:]{2,40}:\s+(.+)$", s)
    if label and label.group(1).split()[0].lower() in _IMPERATIVE_VERBS:
        s = label.group(1)
    if re.match(r"^(?:i |we |here'?s|this |these |that |it |there |your |the |an? |normal |note\b)", s, re.I):
        return None
    for _ in range(3):
        before = s
        s = _DISCOURSE_RE.sub("", s)
        s = _SOFTENER_RE.sub("", s)
        if s == before:
            break
    s = re.sub(r"\bplease\s+", "", s, flags=re.I)
    s = re.sub(r"^try\s+to\s+", "", s, flags=re.I)

    # "If X, <instruction>" -> keep the condition only when a clause after it
    # is an instruction. Try every comma, not just the first: "For fast,
    # quality repairs you can trust, visit a local service center."
    if re.match(r"^(?:if|when|once|after|for|to|before|while)\b", s, re.I):
        for m in re.finditer(r",\s*", s):
            tail = _SOFTENER_RE.sub("", s[m.end():].strip())
            tail = re.sub(r"\bplease\s+", "", tail, flags=re.I)
            if tail and tail.split()[0].lower().strip(",") in _IMPERATIVE_VERBS:
                s = s[: m.end()] + tail
                break
        else:
            return None
    elif s.split()[0].lower().strip(",") not in _IMPERATIVE_VERBS:
        return None

    words = s.split()
    if len(words) < 3 or len(words) > MAX_STEP_WORDS:
        return None
    s = s[0].upper() + s[1:]
    if not s.endswith((".", "!", "?")):
        s += "."
    return s


def _categorize(heading: str, steps: List[str]) -> actionCategory:
    head = heading.lower()
    body = " ".join(steps).lower()
    if _count_terms(head, _CRITICAL_TERMS) or _count_terms(
        body, ("factory data reset", "factory reset", "safe mode", "software update", "force a restart", "forcing a restart")
    ):
        return actionCategory.critical
    head_manual = _count_terms(head, _MANUAL_TERMS)
    body_auto = _count_terms(body, _AUTO_TERMS)
    body_manual = _count_terms(body, _MANUAL_TERMS)
    if head_manual or body_manual > body_auto:
        return actionCategory.manual
    if body_auto:
        return actionCategory.auto
    return actionCategory.manual


_HEADING_VERBS = {
    "review", "remove", "disconnect", "check", "reset", "restart", "update", "clear", "turn",
    "adjust", "change", "enable", "disable", "connect", "reconnect", "install", "uninstall",
    "charge", "inspect", "clean", "back", "contact", "use", "set", "open", "close", "test",
    "customize", "manage", "delete", "sign", "reinstall", "free", "force", "boot", "try",
}


def _describe(heading: str, steps: List[str]) -> str:
    text = f"{heading} {' '.join(steps)}".lower()
    head = heading.lower()
    for keys, desc in _DESCRIPTION_RULES:
        if any(k in head for k in keys):
            return desc
    for keys, desc in _DESCRIPTION_RULES:
        if any(k in text for k in keys):
            return desc
    words = re.sub(r"^(troubleshooting|troubleshoot|fixing|how to)\s+", "", heading.lower()).split()
    if words and words[0] in _HEADING_VERBS:
        # "Review device settings" -> "It will review device settings"
        return f"It will {' '.join(words[:5])}"
    return f"It will fix {' '.join(words[:4]) or 'this issue'}"


def _clean_heading(raw: str) -> str:
    h = _STEP_PREFIX_RE.sub("", raw.strip()).strip(" :-")
    return h


def _action_name(heading: str, category: actionCategory) -> str:
    name = _title_case(heading)
    words = name.split()
    if len(words) > 7:
        name = " ".join(words[:7])
    return name or ("Contact Samsung Support" if category == actionCategory.manual else "Review Device Settings")


def _sections(content: str) -> List[Tuple[str, str]]:
    """Split SIIS content into (heading, body) sections. Content before the
    first heading, and docs with no headings at all, are split per paragraph
    with an empty heading so the caller derives a name from the steps."""
    body = _PREFIX_RE.sub("", content, count=1)
    matches = list(_HEADING_RE.finditer(body))
    sections: List[Tuple[str, str]] = []

    lead = body[: matches[0].start()] if matches else body
    for para in [p for p in re.split(r"\n\s*\n|\n", lead) if p.strip()]:
        sections.append(("", para))

    for i, m in enumerate(matches):
        level = len(m.group(1))
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        text = body[m.end(): end]
        if level == 1:
            # Document title — its body is intro chatter, not an action.
            sections.append(("", text))
            continue
        sections.append((_clean_heading(m.group(2)), text))
    return sections


def _heading_from_steps(steps: List[str]) -> str:
    text = " ".join(steps).lower()
    for keys, name in (
        (("screen protector",), "Remove the Screen Protector"),
        (("force", "restart"), "Force a Restart"),
        (("charge",), "Charge the Device"),
        (("inspect", "damage"), "Check for Physical Damage"),
        (("mouse", "keyboard"), "Connect a USB Mouse and Keyboard"),
        (("service", "support", "repair"), "Contact Samsung Support"),
        (("settings",), "Review Device Settings"),
    ):
        if all(k in text for k in keys) or (len(keys) == 1 and keys[0] in text):
            return name
    return ""


def topic_and_title(query: str, siis_title: str) -> Tuple[str, str]:
    """Goal topic (Title Case) and 2-3 word sentence-case title, from the
    user's own complaint first (intent signature), SIIS title second."""
    try:
        from enrichment.intent_signature import extract_intent_signature

        sig = extract_intent_signature(query)
        if sig.symptom in _SYMPTOM_TOPIC:
            return _SYMPTOM_TOPIC[sig.symptom]
        if sig.component in _COMPONENT_TOPIC:
            return _COMPONENT_TOPIC[sig.component]
    except Exception:
        pass

    t = re.sub(r"\bon (?:a |an |your )?(?:samsung |galaxy )*(?:phone or tablet|phone|tablet)\b", "", siis_title, flags=re.I)
    t = re.sub(r"\b(?:samsung|galaxy)\b", "", t, flags=re.I)
    t = re.sub(r"^(?:use|how to|some things to check first)\b", "", t, flags=re.I)
    t = re.sub(r"\s+", " ", t).strip(" -:")
    words = t.split()
    if not words or len(words) > 5:
        return ("Display", "Display issue")
    topic = _title_case(t)
    title_words = [w.lower() for w in words[:2]]
    title = " ".join(title_words + ["issue"])
    title = title[0].upper() + title[1:]
    return topic, title


def extract_goal_deterministic(query: str, siis_title: str, siis_content: str) -> Goal:
    actions: List[Action] = []
    seen_steps = set()

    for heading, text in _sections(siis_content):
        # Informational sections are still mined ("Factors Affecting
        # Touchscreen Performance" hides "remove the screen protector"); they
        # just don't lend their heading as the action name.
        steps: List[str] = []
        for sentence in _split_sentences(text):
            step = _to_imperative(sentence)
            if step and step.lower() not in seen_steps:
                seen_steps.add(step.lower())
                steps.append(step)
            if len(steps) >= MAX_STEPS_PER_ACTION:
                break
        if not steps:
            continue

        name_source = heading if heading and not _INFORMATIONAL_HEADINGS.match(heading) else _heading_from_steps(steps)
        if not name_source:
            name_source = heading or "Review Device Settings"
        category = _categorize(name_source, steps)
        actions.append(
            Action(
                actionName=_action_name(name_source, category),
                description=_describe(name_source, steps),
                category=category,
                stepGroups=[StepGroup(steps=steps, actionableDeeplink=None, validationDeeplink=None)],
            )
        )
        if len(actions) >= MAX_ACTIONS:
            break

    topic, title = topic_and_title(query, siis_title)
    return Goal(
        goal=f"Follow these steps to perform this {topic} Troubleshooting",
        title=title,
        actions=actions,
        score=0.0,  # computed downstream by the N5 calibrator, never self-reported
    )
