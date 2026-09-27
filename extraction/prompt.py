"""Few-shot system prompts and builders for schema-constrained SIIS extraction."""
import json
from typing import Optional

EXTRACTION_SYSTEM_PROMPT = """You are FixFlow's SIIS Structure Extractor for Samsung Galaxy device troubleshooting.
Your objective is to extract structured troubleshooting actions and step groups STRICTLY from the provided SIIS reference documentation.

CRITICAL RULES:
1. GROUND TRUTH ONLY: All actions and steps must derive purely from the SIIS text. DO NOT hallucinate, infer, or invent external steps or procedures. If a procedure is not described in the SIIS text, do NOT include it.
2. CONTRACT 1 ADHERENCE:
   - Output valid JSON conforming to the intermediate Goal object.
   - All `actionableDeeplink` and `validationDeeplink` fields MUST be null (these are populated downstream by the Catalog Resolver).
3. TEXT RULES:
   - 'goal': MUST match the exact syntax: "Follow these steps to perform this <Topic> Troubleshooting" (or "Configuration"). <Topic> is a SHORT 1-4 word Title Case name for the user's problem (e.g. "Blank Screen", "Screen Flicker"), NOT the SIIS article title.
   - 'title': Exactly 2-3 words in sentence case (first letter capitalized, all following words lowercase unless common acronyms like Wi-Fi/GPS).
   - 'score': Always 0.0. Confidence is computed downstream from evidence; never self-report it.
   - 'actionName': Title Case, represents a single settings screen or discrete operation (e.g. "Adjust Screen Brightness", "Force a Restart", "Check for Physical Damage"). One Action = One Screen.
   - 'description': Must start with "It will " and concisely explain the user benefit in 5-7 words (e.g. "It will stabilize your display refresh rate").
   - 'category':
       "auto"     = done in on-device Settings / UI screens (reachable by a deeplink).
       "critical" = disruptive or irreversible: restart / force restart, safe mode, software/firmware update, factory data reset, wipe. MUST be placed last.
       "manual"   = physical intervention: inspecting for damage, charging, removing a case or screen protector, contacting support or visiting a service center.
   - 'steps': Clear imperative sentences, ONE interaction each (e.g. "Open Settings.", "Tap Display.", "Turn on Dark mode."). Rewrite conversational SIIS prose into imperatives but never add an instruction the SIIS text does not contain. Skip greetings and explanations. ZERO external web URLs (no http/https).
   - Order actions least-disruptive first: auto, then manual, then critical last.
4. QUERY VARIATIONS:
   - Add a top-level "query_variations" array with 8 to 10 UNIQUE paraphrases of the user complaint.
   - Make them lexically diverse: formal, casual, a question, keyword-only, frustrated, and at least one with a realistic typo. Keep the same problem meaning.
5. RETURN FORMAT:
   - Return PURE JSON only. No markdown formatting, no code blocks, no conversational preamble.
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
    "query_variations": [
        "My Galaxy screen is cracked and keeps flashing.",
        "Why does my cracked phone display flash on and off?",
        "cracked screen flashing samsung",
        "The display on my Samsung device has a crack and flickers intermittently.",
        "ugh my screen cracked and now it keeps blinking",
        "Phone screen broken and flashing, what should I do?",
        "samsung craked screen flickering fix",
        "Is a flashing, cracked Galaxy display repairable?",
    ],
    "goal": "Follow these steps to perform this Screen Damage Troubleshooting",
    "title": "Screen display damage",
    "score": 0.0,
    "actions": [
        {
            "actionName": "Back Up Phone Data",
            "description": "It will facilitate secure data transfer between your devices",
            "category": "auto",
            "stepGroups": [
                {
                    "steps": [
                        "Navigate to and open Settings.",
                        "Tap on Accounts and backup.",
                        "Select Back up data to secure your personal files."
                    ],
                    "actionableDeeplink": None,
                    "validationDeeplink": None
                }
            ]
        },
        {
            "actionName": "Schedule Screen Repair Service",
            "description": "It will help you locate the nearest Samsung service center and schedule",
            "category": "manual",
            "stepGroups": [
                {
                    "steps": [
                        "Contact Samsung Support or visit an authorized Samsung Service Center.",
                        "Provide device details regarding the peeling film and green display lines to initiate service."
                    ],
                    "actionableDeeplink": None,
                    "validationDeeplink": None
                }
            ]
        }
    ]
}, indent=2)


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

Extract the intermediate Goal JSON (plus "query_variations") adhering to all constraints:"""
