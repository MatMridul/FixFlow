"""Few-shot system prompts and builders for schema-constrained SIIS extraction."""
import json
from typing import Optional

EXTRACTION_SYSTEM_PROMPT = """You are FixFlow's SIIS Structure Extractor for Samsung Galaxy device troubleshooting.
Your objective is to extract structured troubleshooting actions and step groups STRICTLY from the provided SIIS reference documentation.

CRITICAL RULES:
1. GROUND TRUTH ONLY: every action and step must come from the SIIS text. Never invent a procedure the SIIS text does not describe.
2. CONTRACT 1 ADHERENCE, OUTPUT FORMAT (compact JSON; deeplinks are added downstream by the Catalog Resolver, never output them):
   {"topic": str, "title": str, "variations": [str], "actions": [{"name": str, "desc": str, "cat": "auto"|"manual"|"critical", "steps": [str]}]}
3. FIELD RULES:
   - "topic": SHORT 1-4 word Title Case name for the user's problem (e.g. "Blank Screen", "Screen Flicker"), NOT the SIIS article title.
   - "title": exactly 2-3 words, sentence case (e.g. "Blank screen issue").
   - "name": Title Case, one settings screen or one discrete operation (e.g. "Adjust Screen Brightness", "Force a Restart").
   - "desc": starts with "It will ", 5-7 words total, the user benefit (e.g. "It will stabilize your display refresh rate").
   - "cat": "auto" = done in on-device Settings/UI screens. "manual" = physical: inspect damage, charge, remove case or protector, contact support, service center. "critical" = disruptive or irreversible: restart/force restart, safe mode, software update, factory reset. Critical actions go last.
   - "steps": short imperatives, ONE interaction each, max 12 words (e.g. "Open Settings.", "Tap Display.", "Turn on Dark mode."). Rewrite SIIS prose into imperatives, skip greetings/explanations, no URLs.
   - At most 6 actions and 5 steps per action. Order: auto, then manual, then critical.
   - "variations": 8 UNIQUE paraphrases of the user complaint, max 12 words each, lexically diverse: formal, casual, a question, keywords only, frustrated, one with a realistic typo.
4. Return PURE JSON only: no markdown, no code fences, no preamble.
"""

FEW_SHOT_EXAMPLE_USER = """User Complaint:
"The mobile phone screen is cracked and flashes intermittently."

SIIS Title:
"Broken screen repair and device data backup"

SIIS Reference Content:
"# Screen Damage Procedures
If your Galaxy device screen is cracked or flashing due to physical damage:
Step 1: Backup your data.
Navigate to and open Settings. Tap on Accounts and backup. Select Back up data to secure your personal files.
Step 2: Service center visit.
Contact Samsung Support or visit an authorized Samsung Service Center. Provide device details regarding the peeling film and green display lines to initiate service."
"""

FEW_SHOT_EXAMPLE_ASSISTANT = json.dumps({
    "topic": "Screen Damage",
    "title": "Screen display damage",
    "variations": [
        "My Galaxy screen is cracked and keeps flashing.",
        "Why does my cracked phone display flash on and off?",
        "cracked screen flashing samsung",
        "The display on my Samsung device has a crack and flickers.",
        "ugh my screen cracked and now it keeps blinking",
        "Phone screen broken and flashing, what should I do?",
        "samsung craked screen flickering fix",
        "Is a flashing, cracked Galaxy display repairable?",
    ],
    "actions": [
        {
            "name": "Back Up Phone Data",
            "desc": "It will keep your personal files safe",
            "cat": "auto",
            "steps": ["Open Settings.", "Tap Accounts and backup.", "Tap Back up data."],
        },
        {
            "name": "Visit a Service Center",
            "desc": "It will get the screen professionally repaired",
            "cat": "manual",
            "steps": [
                "Contact Samsung Support or visit a Samsung Service Center.",
                "Describe the peeling film and green display lines.",
            ],
        },
    ],
}, separators=(",", ":"))

def build_extraction_prompt(query: str, siis_title: str, siis_content: str) -> str:
    """Format prompt for the LLM extractor with few-shot context."""
    return f"""{EXTRACTION_SYSTEM_PROMPT}

### Example
[User Request]
{FEW_SHOT_EXAMPLE_USER}

[Structured Response]
{FEW_SHOT_EXAMPLE_ASSISTANT}

---

### Current Task
User Complaint:
"{query}"

SIIS Title:
"{siis_title}"

SIIS Reference Content:
\"\"\"
{siis_content}
\"\"\"

Return the compact JSON:"""
