"""Self-repair loop for correcting malformed troubleshooting payloads."""
import json
import re
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from schema import Action, ContextDeeplinkResponse, Goal, StepGroup, actionCategory
from validation.rules import (
    ALLOWED_ABBREVIATIONS,
    validate_action_category_and_deeplinks,
    validate_action_name,
    validate_action_ordering,
    validate_description,
    validate_goal_syntax,
    validate_score,
    validate_step,
    validate_title,
)
from validation.schema_validator import ValidationReport, validate_goal
from validation.scrubber import contains_urls, scrub_goal, scrub_urls


def to_sentence_case(text: str) -> str:
    """Convert text into sentence case, respecting standard abbreviations."""
    words = text.strip().split()
    if not words:
        return text

    # Ensure 2-3 words
    if len(words) > 3:
        words = words[:3]
    elif len(words) == 1:
        words.append("issue")

    first_word = words[0].capitalize()
    rest_words = []
    for w in words[1:]:
        clean = re.sub(r'[^\w]', '', w)
        if clean.lower() in ALLOWED_ABBREVIATIONS:
            rest_words.append(clean.upper())
        else:
            rest_words.append(w.lower())

    return f"{first_word} {' '.join(rest_words)}"


def to_title_case(text: str) -> str:
    """Convert text into Title Case for action names."""
    minor_words = {"a", "an", "the", "and", "but", "or", "for", "nor", "on", "at", "to", "from", "by", "with", "in", "of"}
    words = text.strip().split()
    if not words:
        return text

    titled = []
    for i, w in enumerate(words):
        if i == 0 or w.lower() not in minor_words:
            titled.append(w.capitalize())
        else:
            titled.append(w.lower())
    return " ".join(titled)


def programmatic_repair_goal(goal: Goal) -> Goal:
    """
    Apply deterministic, fast zero-LLM repairs:
    1. Scrub external URLs.
    2. Enforce 'It will' prefix on action descriptions.
    3. Normalize title casing to sentence case.
    4. Normalize action names to Title Case.
    5. Strip actionableDeeplink on manual actions.
    6. Sort critical actions to the end.
    7. Normalize goal phrasing if malformed.
    """
    # 1. Scrub external URLs
    goal = scrub_goal(goal)

    # 2. Fix Goal phrasing if close
    if not validate_goal_syntax(goal.goal).valid:
        raw_g = goal.goal.strip()
        topic = re.sub(r'^(Follow these steps to perform this|Steps to perform|Troubleshooting for)\s*', '', raw_g, flags=re.IGNORECASE)
        topic = re.sub(r'\s*(Troubleshooting|Configuration)$', '', topic, flags=re.IGNORECASE).strip()
        if not topic:
            topic = "Device"
        goal.goal = f"Follow these steps to perform this {to_title_case(topic)} Troubleshooting"

    # 3. Fix Title casing and length
    if not validate_title(goal.title).valid:
        goal.title = to_sentence_case(goal.title)

    # 4. Fix score bounds
    goal.score = max(0.0, min(1.0, float(goal.score)))

    # 5. Fix Actions
    for action in goal.actions:
        # Title case action name
        if not validate_action_name(action.actionName).valid:
            action.actionName = to_title_case(action.actionName)

        # Ensure description starts with "It will "
        desc = action.description.strip()
        if not desc.startswith("It will"):
            if desc.lower().startswith("it will"):
                action.description = "It will" + desc[7:]
            elif desc.lower().startswith("this will"):
                action.description = "It will" + desc[9:]
            else:
                action.description = f"It will {desc[0].lower() + desc[1:] if desc else 'resolve this issue'}"

        # Manual actions cannot carry actionableDeeplink
        if action.category == actionCategory.manual:
            for sg in action.stepGroups:
                sg.actionableDeeplink = None
                sg.validationDeeplink = None

    # 6. Sort critical actions last
    non_critical = [a for a in goal.actions if a.category != actionCategory.critical]
    critical = [a for a in goal.actions if a.category == actionCategory.critical]
    goal.actions = non_critical + critical

    return goal


def construct_repair_prompt(invalid_payload: str, error_messages: List[str]) -> str:
    """Construct a prompt instructing the LLM to fix the invalid payload based on exact error messages."""
    errors_list = "\n".join(f"- {err}" for err in error_messages)
    return (
        "You are FixFlow's JSON repair assistant. Fix the following JSON troubleshooting payload "
        "so that it strictly complies with all schema rules.\n\n"
        f"Validation Errors to Fix:\n{errors_list}\n\n"
        "Strict Requirements:\n"
        "1. 'goal' must match: 'Follow these steps to perform this <Topic> Troubleshooting'\n"
        "2. 'title' must be 2-3 words in sentence case (first word capitalized, rest lowercase).\n"
        "3. 'actionName' must be Title Case.\n"
        "4. 'description' must start with 'It will '.\n"
        "5. 'category' must be 'auto', 'manual', or 'critical'. Critical actions MUST be last.\n"
        "6. If category is 'manual', actionableDeeplink and validationDeeplink must be null.\n"
        "7. NO external web URLs anywhere.\n"
        "8. Return ONLY valid JSON, with no markdown fences, no explanation.\n\n"
        f"Invalid Payload:\n{invalid_payload}"
    )


def repair_goal_or_json(
    target: Union[Goal, Dict[str, Any], str],
    llm_callable: Optional[Callable[[str], str]] = None,
    max_llm_attempts: int = 1,
) -> Tuple[Optional[Goal], ValidationReport]:
    """
    Execute the tiered repair loop:
    Step 1: Attempt JSON parse and model instantiation.
    Step 2: Apply programmatic zero-LLM auto-fixes.
    Step 3: Validate against all rules. If valid, return.
    Step 4: If invalid and llm_callable provided, invoke single-shot LLM repair.
    Step 5: Re-validate repaired output. Return repaired Goal or None on failure.
    """
    goal: Optional[Goal] = None
    raw_payload_str = ""

    # Step 1: Parse input to Goal
    if isinstance(target, Goal):
        goal = target
        raw_payload_str = json.dumps(goal.model_dump())
    elif isinstance(target, dict):
        raw_payload_str = json.dumps(target)
        try:
            goal = Goal.model_validate(target)
        except Exception:
            pass
    elif isinstance(target, str):
        raw_payload_str = target.strip()
        # Strip potential markdown fences
        clean_str = re.sub(r'^```(?:json)?\s*', '', raw_payload_str, flags=re.MULTILINE)
        clean_str = re.sub(r'```$', '', clean_str, flags=re.MULTILINE).strip()
        try:
            parsed = json.loads(clean_str)
            goal = Goal.model_validate(parsed)
        except Exception:
            pass

    # Step 2: Programmatic repairs
    if goal is not None:
        goal = programmatic_repair_goal(goal)
        report = validate_goal(goal)
        if report.is_valid:
            return goal, report
    else:
        report = ValidationReport()
        report.add_error("Initial JSON or schema parse failed.")

    # Step 3: Single-shot LLM repair (if allowed and callable present)
    if llm_callable is not None and max_llm_attempts > 0:
        prompt = construct_repair_prompt(raw_payload_str, report.errors)
        try:
            repaired_text = llm_callable(prompt)
            clean_repaired = re.sub(r'^```(?:json)?\s*', '', repaired_text.strip(), flags=re.MULTILINE)
            clean_repaired = re.sub(r'```$', '', clean_repaired, flags=re.MULTILINE).strip()
            repaired_data = json.loads(clean_repaired)
            repaired_goal = Goal.model_validate(repaired_data)
            # Re-apply programmatic repair for complete safety
            repaired_goal = programmatic_repair_goal(repaired_goal)
            final_report = validate_goal(repaired_goal)
            if final_report.is_valid:
                return repaired_goal, final_report
            return None, final_report
        except Exception as e:
            report.add_error(f"LLM repair failed: {str(e)}")
            return None, report

    return (goal if report.is_valid else None), report
