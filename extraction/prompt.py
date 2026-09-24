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
   - 'goal': MUST match the exact syntax: "Follow these steps to perform this <Topic> Troubleshooting" (or "Configuration").
   - 'title': Exactly 2-3 words in sentence case (first letter capitalized, all following words lowercase unless common acronyms like Wi-Fi/GPS).
   - 'score': Float between 0.85 and 0.95 reflecting baseline extraction grounding.
   - 'actionName': Title Case, represents a single settings screen or discrete operation (e.g. "Adjust Screen Brightness", "Restart Device", "Wipe Cache Partition").
   - 'description': Must start with "It will " and concisely explain the user benefit (e.g. "It will stabilize your display refresh rate").
   - 'category': "auto" (settings / on-device UI), "critical" (destructive/irreversible actions like Factory Data Reset, wipe cache; MUST be placed last), or "manual" (physical inspection, authorized service center visit).
   - 'steps': Clear, imperative sentences (e.g. "Open Settings.", "Tap on Display.", "Turn on Dark mode."). ZERO external web URLs (no http/https).
4. RETURN FORMAT:
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
    "goal": "Follow these steps to perform this Screen Damage Troubleshooting",
    "title": "Screen display damage",
    "score": 0.95,
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

Extract the intermediate Goal JSON adhering to all constraints:"""
