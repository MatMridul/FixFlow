"""Schema-constrained LLM extractor for converting SIIS text into intermediate Goal structures."""
import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional

from extraction.deterministic import extract_goal_deterministic, guard_category, known_description, topic_and_title
from extraction.prompt import build_extraction_prompt
from extraction.query_variations import merge_variations
from schema import Goal
from validation import (
    programmatic_repair_goal,
    repair_goal_or_json,
    validate_goal,
)

DETERMINISTIC_MODEL_ID = "fixflow-deterministic-v2"


@dataclass
class ExtractionOutcome:
    goal: Optional[Goal]
    query_variations: List[str] = field(default_factory=list)
    model: str = DETERMINISTIC_MODEL_ID
    cost_usd: float = 0.0
    llm_used: bool = False


def clean_llm_json(raw_text: str) -> str:
    """Strip markdown code fences and extraneous text from LLM response."""
    text = raw_text.strip()
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    match = re.search(r'(\{.*\})', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


_CATEGORIES = {"auto", "manual", "critical"}


def _expand_compact(parsed: Any) -> Any:
    """The prompt asks for a compact shape ({topic,title,variations,actions:[{name,
    desc,cat,steps}]}) because output tokens dominate latency: the full Goal JSON
    was 1.1-1.5k tokens (6-7.5 s on gemini-2.5-flash). Expand it to the Goal
    schema here. Full-Goal payloads pass through unchanged."""
    if not isinstance(parsed, dict) or "goal" in parsed or "topic" not in parsed:
        return parsed
    actions = []
    for a in parsed.get("actions") or []:
        if not isinstance(a, dict):
            continue
        steps = [s for s in (a.get("steps") or []) if isinstance(s, str) and s.strip()]
        if not steps:
            continue
        cat = str(a.get("cat", "manual")).lower()
        actions.append({
            "actionName": str(a.get("name", "")).strip() or "Follow These Steps",
            "description": str(a.get("desc", "")).strip() or "It will help resolve this issue",
            "category": cat if cat in _CATEGORIES else "manual",
            "stepGroups": [{"steps": steps, "actionableDeeplink": None, "validationDeeplink": None}],
        })
    topic = re.sub(r"\s+(troubleshooting|configuration)$", "", str(parsed.get("topic", "")).strip(), flags=re.I) or "Device"
    return {
        "goal": f"Follow these steps to perform this {topic} Troubleshooting",
        "title": str(parsed.get("title", "")).strip() or f"{topic} issue",
        "score": 0.0,
        "actions": actions,
        "query_variations": parsed.get("variations") or parsed.get("query_variations"),
    }


class StructureExtractor:
    """Extracts structured Goal objects from SIIS documentation conforming to Contract 1.

    With an `llm_callable` (e.g. extraction.llm_client.LLMChain) the LLM does
    the extraction and paraphrasing in one call; if it's absent or fails, the
    deterministic extractor takes over so the API always answers.
    """

    def __init__(
        self,
        llm_callable: Optional[Callable[[str], str]] = None,
        temperature: float = 0.0,
    ):
        self.llm_callable = llm_callable
        self.temperature = temperature

    def _call_llm(self, prompt: str):
        """Returns (text, model_id, cost_usd). Uses the chain's richer
        `complete()` when available so meta reports the model that actually
        answered, not the one we hoped would."""
        complete = getattr(self.llm_callable, "complete", None)
        if callable(complete):
            text, record = complete(prompt)
            return text, record.model, record.cost_usd
        return self.llm_callable(prompt), "custom-llm", 0.0

    def extract_full(self, query: str, siis_title: str, siis_content: str) -> ExtractionOutcome:
        if not siis_content or not siis_content.strip():
            return ExtractionOutcome(goal=None)

        goal: Optional[Goal] = None
        llm_variations: List[str] = []
        model, cost, llm_used = DETERMINISTIC_MODEL_ID, 0.0, False

        if self.llm_callable is not None:
            prompt = build_extraction_prompt(query, siis_title, siis_content)
            raw_response = ""
            try:
                raw_response, model, cost = self._call_llm(prompt)
                parsed = _expand_compact(json.loads(clean_llm_json(raw_response)))
                if isinstance(parsed, dict):
                    variations = parsed.pop("query_variations", None)
                    if isinstance(variations, list):
                        llm_variations = [v for v in variations if isinstance(v, str)]
                goal = Goal.model_validate(parsed)
                if len(goal.title.split()) > 3:
                    # Truncating a long LLM title gives "Device screen remains";
                    # the query-derived title is always 2-3 clean words.
                    goal.title = topic_and_title(query, siis_title)[1]
                for action in goal.actions:
                    action.category = guard_category(
                        action.actionName, [st for sg in action.stepGroups for st in sg.steps], action.category
                    )
                    if len(action.description.split()) > 7:
                        # Cutting to 7 words leaves "...files and resolve"; a
                        # curated description reads better when one fits.
                        steps = [st for sg in action.stepGroups for st in sg.steps]
                        action.description = known_description(action.actionName, steps) or action.description
                llm_used = True
            except Exception:
                goal = None
                if raw_response:
                    try:
                        # Single-shot LLM repair (Task A.0.3) — spends quota only on bad output.
                        goal, _ = repair_goal_or_json(raw_response, llm_callable=self.llm_callable)
                        llm_used = goal is not None
                    except Exception:
                        goal = None
            if goal is not None and not goal.actions:
                # A plan with no actions is worse than the SIIS-grounded fallback.
                goal, llm_used = None, False
            if goal is None:
                model, cost = DETERMINISTIC_MODEL_ID, 0.0

        if goal is None:
            goal = extract_goal_deterministic(query, siis_title, siis_content)
            if not goal.actions:
                return ExtractionOutcome(goal=None, model=model, cost_usd=cost)

        # Enforce Contract 1: empty deeplink fields ready for catalog resolution
        for action in goal.actions:
            for sg in action.stepGroups:
                sg.actionableDeeplink = None
                sg.validationDeeplink = None

        goal = programmatic_repair_goal(goal)
        report = validate_goal(goal)
        if not report.is_valid:
            repaired_goal, final_report = repair_goal_or_json(goal, llm_callable=None)
            goal = repaired_goal if final_report.is_valid else None

        topic = topic_and_title(query, siis_title)[0]
        return ExtractionOutcome(
            goal=goal,
            query_variations=merge_variations(llm_variations, query, topic),
            model=model,
            cost_usd=round(cost, 6),
            llm_used=llm_used,
        )

    def extract(self, query: str, siis_title: str, siis_content: str) -> Optional[Goal]:
        """Backward-compatible Goal-only entry point."""
        return self.extract_full(query, siis_title, siis_content).goal
