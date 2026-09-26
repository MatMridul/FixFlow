"""Schema-constrained LLM extractor for converting SIIS text into intermediate Goal structures."""
import json
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from extraction.prompt import build_extraction_prompt
from schema import Action, Goal, StepGroup, actionCategory
from validation import (
    contains_urls,
    programmatic_repair_goal,
    repair_goal_or_json,
    validate_goal,
)


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


def extract_fallback_actions_from_siis(content: str) -> List[Action]:
    """
    Deterministic rule-based fallback extractor:
    Parses steps, headings, and bullet points from raw SIIS text when offline or without LLM.
    """
    actions: List[Action] = []
    # Split by headings or steps (e.g. ## Step 1:, Step 1:, 1., etc.)
    sections = re.split(r'\n(?=#{1,3}\s+|Step\s+\d+:?|\d+\.\s+)', content)

    for sec in sections:
        lines = [line.strip() for line in sec.split('\n') if line.strip()]
        if not lines:
            continue

        header_line = lines[0]
        # Clean title
        action_title = re.sub(r'^#+\s*', '', header_line).strip()
        action_title = re.sub(r'^(?:Step\s+\d+:?|\d+[\.\)])\s*', '', action_title, flags=re.IGNORECASE).strip()
        if not action_title or len(action_title.split()) > 6 or len(lines) == 1:
            lower_h = header_line.lower()
            if any(w in lower_h for w in ["display", "screen", "flicker", "brightness"]):
                action_title = "Adjust Display Settings"
            elif any(w in lower_h for w in ["battery", "charge", "drain"]):
                action_title = "Inspect Battery Usage"
            elif any(w in lower_h for w in ["network", "wifi", "bluetooth", "connection"]):
                action_title = "Check Network Settings"
            else:
                action_title = "Review Device Settings"

        # Categorize
        lower_title = action_title.lower()
        if any(w in lower_title for w in ["reset", "wipe", "factory", "erase"]):
            category = actionCategory.critical
        elif any(w in lower_title for w in ["visit", "contact", "support", "service", "physical"]):
            category = actionCategory.manual
        else:
            category = actionCategory.auto

        # Extract steps
        step_lines = []
        for line in lines[1:]:
            cleaned_line = re.sub(r'^(?:[-*•]|\d+\.)\s*', '', line).strip()
            if cleaned_line and not contains_urls(cleaned_line) and len(cleaned_line) > 5:
                step_lines.append(cleaned_line)

        if not step_lines:
            # If no multi-line steps, extract sentences from the section content
            candidate_sentences = [
                s.strip() for s in re.split(r'(?<=[.!?])\s+', sec)
                if s.strip() and not contains_urls(s) and len(s.strip()) > 5
            ]
            if candidate_sentences:
                step_lines.extend(candidate_sentences)
            else:
                candidate = re.sub(r'^(?:[-*•]|\d+\.)\s*', '', header_line).strip()
                if candidate:
                    step_lines.append(candidate)

        actions.append(
            Action(
                actionName=action_title,
                description=f"It will help you {action_title.lower()} properly",
                category=category,
                stepGroups=[
                    StepGroup(
                        steps=step_lines,
                        actionableDeeplink=None,
                        validationDeeplink=None,
                    )
                ],
            )
        )

    # If nothing extracted, create default safe action
    if not actions:
        actions.append(
            Action(
                actionName="Review Device Settings",
                description="It will help inspect and configure device settings",
                category=actionCategory.auto,
                stepGroups=[
                    StepGroup(
                        steps=["Navigate to and open Settings.", "Review related device options."],
                        actionableDeeplink=None,
                        validationDeeplink=None,
                    )
                ],
            )
        )

    return actions


class StructureExtractor:
    """Extracts structured Goal objects from SIIS documentation conforming to Contract 1."""

    def __init__(
        self,
        llm_callable: Optional[Callable[[str], str]] = None,
        temperature: float = 0.0,
    ):
        self.llm_callable = llm_callable
        self.temperature = temperature

    def extract(self, query: str, siis_title: str, siis_content: str) -> Optional[Goal]:
        """
        Extract an intermediate Goal from SIIS content.
        Enforces Contract 1: deeplinks are initialized to None.
        Returns repaired and validated Goal, or None if extraction fails.
        """
        if not siis_content or not siis_content.strip():
            return None

        goal: Optional[Goal] = None

        if self.llm_callable is not None:
            prompt = build_extraction_prompt(query, siis_title, siis_content)
            try:
                raw_response = self.llm_callable(prompt)
                cleaned_json = clean_llm_json(raw_response)
                parsed = json.loads(cleaned_json)
                goal = Goal.model_validate(parsed)
            except Exception:
                # Attempt repair if JSON failed to parse
                goal, _ = repair_goal_or_json(raw_response, llm_callable=self.llm_callable)

        # Fallback to deterministic extraction if LLM is not provided or failed
        if goal is None:
            actions = extract_fallback_actions_from_siis(siis_content)
            topic = re.sub(r'[^\w\s]', '', siis_title).strip()
            if not topic:
                topic = "Device"
            goal = Goal(
                goal=f"Follow these steps to perform this {topic} Troubleshooting",
                title=f"{topic} issue",
                actions=actions,
                score=0.90,
            )

        # Enforce Contract 1: empty deeplink fields ready for catalog resolution
        for action in goal.actions:
            for sg in action.stepGroups:
                sg.actionableDeeplink = None
                sg.validationDeeplink = None

        # Apply programmatic repairs to ensure casing and rule compliance
        goal = programmatic_repair_goal(goal)
        report = validate_goal(goal)

        if report.is_valid:
            return goal

        # Final repair attempt if still invalid
        repaired_goal, final_report = repair_goal_or_json(goal, llm_callable=self.llm_callable)
        return repaired_goal if final_report.is_valid else None
