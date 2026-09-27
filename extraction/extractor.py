"""Schema-constrained LLM extractor for converting SIIS text into intermediate Goal structures."""
import json
import re
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from extraction.deterministic import extract_goal_deterministic, topic_and_title
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
                parsed = json.loads(clean_llm_json(raw_response))
                if isinstance(parsed, dict):
                    variations = parsed.pop("query_variations", None)
                    if isinstance(variations, list):
                        llm_variations = [v for v in variations if isinstance(v, str)]
                goal = Goal.model_validate(parsed)
                llm_used = True
            except Exception:
                if raw_response:
                    try:
                        # Single-shot LLM repair (Task A.0.3) — spends quota only on bad output.
                        goal, _ = repair_goal_or_json(raw_response, llm_callable=self.llm_callable)
                        llm_used = goal is not None
                    except Exception:
                        goal = None
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
