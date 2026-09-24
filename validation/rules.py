"""Fine-grained rule validators for FixFlow troubleshooting structures."""
import re
from dataclasses import dataclass
from typing import List, Optional

from schema import Action, Deeplink, Goal, StepGroup, actionCategory
from validation.scrubber import contains_urls

# Goal syntax pattern
# Example: "Follow these steps to perform this Screen Damage Troubleshooting"
GOAL_SYNTAX_PATTERN = re.compile(
    r"^Follow these steps to perform this (.+) (Troubleshooting|Configuration)$",
    re.IGNORECASE,
)

# Common imperative verbs opening troubleshooting steps
IMPERATIVE_VERBS = {
    "adjust", "allow", "back", "backup", "change", "check", "choose", "clear",
    "close", "confirm", "connect", "contact", "disable", "disconnect", "drag",
    "enable", "ensure", "enter", "follow", "go", "hold", "insert", "inspect",
    "install", "launch", "locate", "lock", "move", "navigate", "open", "perform",
    "pick", "plug", "power", "press", "provide", "reboot", "reconnect", "remove",
    "reset", "restart", "review", "run", "scroll", "select", "set", "slide",
    "start", "stop", "switch", "swipe", "tap", "test", "toggle", "turn", "unplug",
    "update", "use", "verify", "visit", "wait"
}

ALLOWED_ABBREVIATIONS = {"gps", "usb", "wi-fi", "wifi", "sim", "led", "ram", "os", "ai", "nfc", "sos"}


@dataclass
class ValidationResult:
    """Outcome of an individual rule check."""
    valid: bool
    rule_name: str
    message: str
    is_warning: bool = False


class RuleViolation(Exception):
    """Exception raised when a strict rule is violated."""
    pass


def validate_goal_syntax(goal: str) -> ValidationResult:
    """
    Validate goal format.
    Must be: 'Follow these steps to perform this <Topic> Troubleshooting' (or 'Configuration').
    """
    if not goal or not isinstance(goal, str):
        return ValidationResult(False, "goal_syntax", "Goal must be a non-empty string.")

    match = GOAL_SYNTAX_PATTERN.match(goal.strip())
    if not match:
        return ValidationResult(
            False,
            "goal_syntax",
            f"Goal '{goal}' does not follow required pattern: "
            "'Follow these steps to perform this <Topic> Troubleshooting' (or Configuration)."
        )

    topic = match.group(1).strip()
    if not topic:
        return ValidationResult(False, "goal_syntax", "Goal topic name cannot be empty.")

    return ValidationResult(True, "goal_syntax", "Goal syntax is valid.")


def validate_title(title: str) -> ValidationResult:
    """
    Validate title format.
    Must be: 2–3 words, sentence case.
    """
    if not title or not isinstance(title, str):
        return ValidationResult(False, "title_format", "Title must be a non-empty string.")

    words = title.strip().split()
    if len(words) not in (2, 3):
        return ValidationResult(
            False,
            "title_format",
            f"Title '{title}' must be 2 or 3 words (got {len(words)} words)."
        )

    # Check sentence case: first word capitalized, subsequent words lowercase (unless abbreviation)
    first_word = words[0]
    if not first_word[0].isupper():
        return ValidationResult(
            False,
            "title_format",
            f"Title '{title}' must be sentence case (first letter must be capitalized)."
        )

    for word in words[1:]:
        # Strip trailing punctuation if present
        clean_word = re.sub(r'[^\w]', '', word)
        if clean_word.lower() in ALLOWED_ABBREVIATIONS:
            continue
        if clean_word and clean_word[0].isupper():
            return ValidationResult(
                False,
                "title_format",
                f"Title '{title}' is in Title Case instead of Sentence Case (word '{word}' is capitalized)."
            )

    return ValidationResult(True, "title_format", "Title format is valid.")


def validate_action_name(action_name: str) -> ValidationResult:
    """
    Validate action name.
    Must be: Title Case, exactly one screen.
    """
    if not action_name or not isinstance(action_name, str):
        return ValidationResult(False, "action_name_format", "Action name must be a non-empty string.")

    words = [re.sub(r'[^\w]', '', w) for w in action_name.strip().split() if w]
    if not words:
        return ValidationResult(False, "action_name_format", "Action name contains no valid words.")

    # Minor words allowed to be lowercase in Title Case
    minor_words = {"a", "an", "the", "and", "but", "or", "for", "nor", "on", "at", "to", "from", "by", "with", "in", "of"}

    # Check Title Case
    for i, word in enumerate(words):
        if not word:
            continue
        if i == 0 or word.lower() not in minor_words:
            if word[0].isalpha() and not word[0].isupper():
                return ValidationResult(
                    False,
                    "action_name_format",
                    f"Action name '{action_name}' must be in Title Case (word '{word}' is not capitalized)."
                )

    return ValidationResult(True, "action_name_format", "Action name format is valid.")


def validate_description(description: str, soft_length: bool = True) -> ValidationResult:
    """
    Validate description format.
    Must start with 'It will'. Soft tolerance for length (Finding C: official samples are 9 & 12 words).
    """
    if not description or not isinstance(description, str):
        return ValidationResult(False, "description_format", "Description must be a non-empty string.")

    trimmed = description.strip()
    if not trimmed.startswith("It will"):
        return ValidationResult(
            False,
            "description_format",
            f"Description '{description}' must start with 'It will'."
        )

    words = trimmed.split()
    word_count = len(words)

    # Finding C: 5-7 words is a soft target. Do NOT hard-reject on length.
    if soft_length and (word_count < 4 or word_count > 20):
        return ValidationResult(
            True,
            "description_format",
            f"Description has {word_count} words (guideline targets 5-7 words).",
            is_warning=True,
        )

    return ValidationResult(True, "description_format", "Description format is valid.")


def validate_step(step: str) -> ValidationResult:
    """
    Validate step format.
    Must be imperative sentence, one interaction per step, zero URLs.
    """
    if not step or not isinstance(step, str):
        return ValidationResult(False, "step_format", "Step must be a non-empty string.")

    trimmed = step.strip()

    # URL check
    if contains_urls(trimmed):
        return ValidationResult(
            False,
            "step_format",
            f"Step contains prohibited external web URL: '{trimmed}'."
        )

    words = trimmed.split()
    if not words:
        return ValidationResult(False, "step_format", "Step contains no words.")

    first_word = re.sub(r'[^\w]', '', words[0]).lower()
    if first_word not in IMPERATIVE_VERBS:
        return ValidationResult(
            True,
            "step_format",
            f"Step '{trimmed}' may not start with a recognized imperative verb ('{first_word}').",
            is_warning=True,
        )

    return ValidationResult(True, "step_format", "Step format is valid.")


def validate_action_category_and_deeplinks(action: Action) -> ValidationResult:
    """
    Validate category rules:
    - category must be auto, manual, or critical.
    - manual actions CANNOT carry actionableDeeplink.
    """
    cat = action.category
    if cat not in (actionCategory.auto, actionCategory.manual, actionCategory.critical):
        return ValidationResult(
            False,
            "action_category",
            f"Invalid action category '{cat}'. Must be 'auto', 'manual', or 'critical'."
        )

    if cat == actionCategory.manual:
        for i, sg in enumerate(action.stepGroups):
            if sg.actionableDeeplink is not None:
                return ValidationResult(
                    False,
                    "action_category_manual_deeplink",
                    f"Manual action '{action.actionName}' step group {i} cannot carry actionableDeeplink."
                )

    return ValidationResult(True, "action_category", "Action category and deeplinks are valid.")


def validate_action_ordering(actions: List[Action]) -> ValidationResult:
    """
    Validate action ordering:
    - critical actions must always be sorted last.
    - No non-critical action can appear after a critical action.
    """
    seen_critical = False
    for i, action in enumerate(actions):
        if action.category == actionCategory.critical:
            seen_critical = True
        elif seen_critical:
            return ValidationResult(
                False,
                "action_ordering",
                f"Action '{action.actionName}' (category: {action.category}) appears after a critical action at index {i}. "
                "Critical actions must be sorted last."
            )

    return ValidationResult(True, "action_ordering", "Action ordering is valid.")


def validate_score(score: float) -> ValidationResult:
    """Validate score is float in [0.0, 1.0]."""
    if not isinstance(score, (int, float)):
        return ValidationResult(False, "score_range", f"Score must be a float, got {type(score).__name__}.")

    if not (0.0 <= score <= 1.0):
        return ValidationResult(False, "score_range", f"Score {score} is outside [0.0, 1.0].")

    return ValidationResult(True, "score_range", "Score is valid.")


def validate_no_urls(text: str) -> ValidationResult:
    """Ensure no web URLs exist in text."""
    if contains_urls(text):
        return ValidationResult(False, "no_web_urls", f"Text contains prohibited web URLs: '{text}'.")
    return ValidationResult(True, "no_web_urls", "No web URLs found.")
