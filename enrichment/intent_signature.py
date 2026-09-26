"""Lexicon-based intent signature extraction and compatibility gate (Novelty N2)."""
import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional, Tuple

DOMAIN_LEXICON = {
    "Display": {
        "screen", "display", "flicker", "flickering", "flashes", "flashing",
        "blank", "black", "white", "lines", "green", "pink", "dim", "brightness",
        "touch", "touchscreen", "refresh", "hz", "peeling", "cracked", "crack",
        "glass", "damage", "pixels", "tint", "resolution", "navigation bar",
    },
    "Battery": {
        "battery", "charge", "charging", "drain", "drains", "draining", "dies",
        "dying", "power", "charger", "cable", "percentage", "fast charge",
        "wireless charging", "overheat", "overheating", "warm", "heat",
    },
    "Performance": {
        "lag", "lagging", "slow", "sluggish", "freeze", "freezes", "freezing",
        "frozen", "hang", "hangs", "crashed", "crashes", "crashing", "stutter",
        "restart", "rebooting", "bootloop", "unresponsive", "ram", "storage",
    },
    "Connectivity": {
        "wifi", "wi-fi", "bluetooth", "network", "sim", "signal", "cellular",
        "data", "internet", "hotspot", "gps", "airplane mode", "pairing",
    },
    "Audio": {
        "speaker", "sound", "volume", "audio", "mic", "microphone", "call audio",
        "crackling", "silent", "buzzing", "distortion", "earpiece", "headphones",
    },
    "Camera": {
        "camera", "lens", "photo", "video", "blurry", "focus", "shutter", "flash",
    },
}

COMPONENT_KEYWORDS = {
    "brightness": ["brightness", "dim", "dark", "blinding"],
    "refresh_rate": ["refresh", "hz", "motion smoothness", "120hz", "60hz"],
    "charging": ["charge", "charging", "cable", "plug", "wireless charge"],
    "battery_drain": ["drain", "dies", "dying", "battery life", "consumption"],
    "touch": ["touch", "touchscreen", "tap", "responsive", "unresponsive"],
    "navigation_bar": ["navigation bar", "gestures", "buttons"],
    "screen_damage": ["cracked", "crack", "broken", "peeling", "lines", "green line"],
    "wifi": ["wifi", "wi-fi", "wireless network"],
    "bluetooth": ["bluetooth", "pair", "pairing", "headphones"],
    "audio_speaker": ["speaker", "audio", "sound", "volume"],
}

SYMPTOM_KEYWORDS = {
    "flicker": ["flicker", "flickering", "flashes", "flashing", "blink", "blinking"],
    "blank": ["blank", "black", "white", "blackout", "nothing appears"],
    "drain": ["drain", "draining", "drains", "dies fast", "depleting"],
    "freeze": ["freeze", "freezes", "freezing", "stuck", "hang", "hangs"],
    "not_charging": ["not charging", "wont charge", "refuses to charge", "slow charging", "stopped charging"],
    "overheat": ["overheat", "overheating", "hot", "warm", "heat"],
    "damage": ["cracked", "broken", "peeling", "lines"],
    "slow": ["slow", "lag", "sluggish", "stutter"],
}

NEGATION_PATTERN = re.compile(
    r"\b(not|no|cant|can't|cannot|wont|won't|unable|doesnt|doesn't|fails|failed|never|refuses|stop|stopped|without|off|disable|disabled|disabling|deactivate|deactivated|mute)\b",
    re.IGNORECASE,
)

TRIGGER_PATTERNS = [
    ("after_update", re.compile(r"\b(?:after|since|following)\s+(?:the\s+)?(?:software\s+)?update\b", re.IGNORECASE)),
    ("after_drop", re.compile(r"\b(?:after|since)\s+(?:dropping|drop|fell|water|liquid|damage)\b", re.IGNORECASE)),
    ("while_charging", re.compile(r"\b(?:while|when|during)\s+(?:charging|plugged\s+in)\b", re.IGNORECASE)),
    ("during_call", re.compile(r"\b(?:during|in|on)\s+(?:a\s+)?(?:phone\s+)?call\b", re.IGNORECASE)),
    ("on_app_open", re.compile(r"\b(?:when|whenever|after)\s+(?:opening|tapping|launching)\s+[A-Za-z0-9]+\b", re.IGNORECASE)),
]


@dataclass
class IntentSignature:
    """Discrete semantic signature for false-hit cache gating (Novelty N2)."""
    domain: str
    component: str
    symptom: str
    polarity: str  # "normal" or "negated"
    trigger: str   # "none", "after_update", etc.

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IntentSignature":
        return cls(
            domain=data.get("domain", "General"),
            component=data.get("component", "unknown"),
            symptom=data.get("symptom", "unknown"),
            polarity=data.get("polarity", "normal"),
            trigger=data.get("trigger", "none"),
        )


def extract_intent_signature(text: str) -> IntentSignature:
    """
    Fast lexicon-based signature extraction in <1ms without calling an LLM.
    Identifies domain, component, symptom, polarity, and trigger.
    """
    clean_text = text.lower()
    tokens = set(re.findall(r"\b\w+\b", clean_text))

    # 1. Domain detection
    best_domain = "General"
    max_domain_matches = 0
    for domain, keywords in DOMAIN_LEXICON.items():
        matches = len(tokens.intersection(keywords))
        if matches > max_domain_matches:
            max_domain_matches = matches
            best_domain = domain

    # Default to Display if tied with screen complaints (common in Samsung kit)
    if best_domain == "General" and any(w in clean_text for w in ["screen", "display", "flicker"]):
        best_domain = "Display"

    # 2. Component detection
    best_component = "unknown"
    for comp, kw_list in COMPONENT_KEYWORDS.items():
        if any(kw in clean_text for kw in kw_list):
            best_component = comp
            break

    # 3. Symptom detection
    best_symptom = "unknown"
    for sym, kw_list in SYMPTOM_KEYWORDS.items():
        if any(kw in clean_text for kw in kw_list):
            best_symptom = sym
            break

    # 4. Polarity detection
    # Checks for negative polarity phrases like "not charging", "won't turn on", "turn off", "disable"
    text_for_negation = re.sub(r"\bdo not disturb\b", "dnd", clean_text)
    has_negation = bool(NEGATION_PATTERN.search(text_for_negation))
    polarity = "negated" if has_negation else "normal"

    # 5. Trigger detection
    trigger = "none"
    for trigger_name, pattern in TRIGGER_PATTERNS:
        if pattern.search(clean_text):
            trigger = trigger_name
            break

    return IntentSignature(
        domain=best_domain,
        component=best_component,
        symptom=best_symptom,
        polarity=polarity,
        trigger=trigger,
    )


def signatures_compatible(sig1: IntentSignature, sig2: IntentSignature) -> Tuple[bool, str]:
    """
    Gating function: Determine if two queries are semantically compatible for cache retrieval.
    Rejects near-miss false-hits (e.g. 'battery draining' vs 'battery not charging').
    """
    # 1. Polarity match is MANDATORY
    if sig1.polarity != sig2.polarity:
        return False, f"Polarity mismatch: '{sig1.polarity}' vs '{sig2.polarity}'"

    # 2. Domain match is MANDATORY (if known)
    if sig1.domain != "General" and sig2.domain != "General":
        if sig1.domain != sig2.domain:
            return False, f"Domain mismatch: '{sig1.domain}' vs '{sig2.domain}'"

    # 3. Symptom compatibility
    # Opposing symptoms (e.g. 'drain' vs 'not_charging', 'flicker' vs 'blank') must not cross-hit
    incompatible_symptoms = {
        ("drain", "not_charging"),
        ("not_charging", "drain"),
        ("blank", "flicker"),
        ("flicker", "blank"),
        ("slow", "damage"),
        ("damage", "slow"),
    }
    if (sig1.symptom, sig2.symptom) in incompatible_symptoms:
        return False, f"Incompatible symptoms: '{sig1.symptom}' vs '{sig2.symptom}'"

    # 4. Trigger compatibility (if both have explicit triggers, they should match)
    if sig1.trigger != "none" and sig2.trigger != "none":
        if sig1.trigger != sig2.trigger:
            return False, f"Trigger mismatch: '{sig1.trigger}' vs '{sig2.trigger}'"

    return True, "Compatible"
