"""High-level schema validator and compliance checker for FixFlow."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Union

from schema import ContextDeeplinkResponse, Goal
from validation.rules import (
    RuleViolation,
    validate_action_category_and_deeplinks,
    validate_action_name,
    validate_action_ordering,
    validate_description,
    validate_goal_syntax,
    validate_no_urls,
    validate_score,
    validate_step,
    validate_title,
)
from validation.scrubber import contains_urls


@dataclass
class ValidationReport:
    """Consolidated report of validation outcomes, errors, and warnings."""
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def raise_if_invalid(self) -> None:
        """Raise RuleViolation if there are fatal errors."""
        if not self.is_valid:
            error_summary = "; ".join(self.errors)
            raise RuleViolation(f"Validation failed with {len(self.errors)} error(s): {error_summary}")


def validate_goal(goal: Goal) -> ValidationReport:
    """Validate a single Goal object against all Theme 02 text and structure rules."""
    report = ValidationReport()

    # 1. Goal syntax
    res = validate_goal_syntax(goal.goal)
    if not res.valid:
        report.add_error(res.message)
    elif res.is_warning:
        report.add_warning(res.message)

    # 2. Title format
    res = validate_title(goal.title)
    if not res.valid:
        report.add_error(res.message)
    elif res.is_warning:
        report.add_warning(res.message)

    # 3. Score range
    res = validate_score(goal.score)
    if not res.valid:
        report.add_error(res.message)

    # 4. Action ordering (critical actions last)
    res = validate_action_ordering(goal.actions)
    if not res.valid:
        report.add_error(res.message)

    if not goal.actions:
        report.add_warning(f"Goal '{goal.title}' contains zero actions.")

    # 5. Action level checks
    for a_idx, action in enumerate(goal.actions):
        # Action Name
        res = validate_action_name(action.actionName)
        if not res.valid:
            report.add_error(f"Action [{a_idx}] '{action.actionName}': {res.message}")
        elif res.is_warning:
            report.add_warning(f"Action [{a_idx}] '{action.actionName}': {res.message}")

        # Description
        res = validate_description(action.description)
        if not res.valid:
            report.add_error(f"Action [{a_idx}] '{action.actionName}': {res.message}")
        elif res.is_warning:
            report.add_warning(f"Action [{a_idx}] '{action.actionName}': {res.message}")

        # Category and Deeplink constraints
        res = validate_action_category_and_deeplinks(action)
        if not res.valid:
            report.add_error(f"Action [{a_idx}] '{action.actionName}': {res.message}")

        # Check for web URLs in action text
        if contains_urls(action.actionName):
            report.add_error(f"Action [{a_idx}] actionName contains web URL.")
        if contains_urls(action.description):
            report.add_error(f"Action [{a_idx}] description contains web URL.")

        # StepGroup checks
        for sg_idx, sg in enumerate(action.stepGroups):
            if not sg.steps:
                report.add_error(f"Action [{a_idx}] StepGroup [{sg_idx}] has no steps.")

            for s_idx, step in enumerate(sg.steps):
                res = validate_step(step)
                if not res.valid:
                    report.add_error(f"Action [{a_idx}] Step [{s_idx}]: {res.message}")
                elif res.is_warning:
                    report.add_warning(f"Action [{a_idx}] Step [{s_idx}]: {res.message}")

            # Check actionableDeeplink URI if present
            if sg.actionableDeeplink is not None:
                uri = sg.actionableDeeplink.deeplink
                if contains_urls(uri):
                    report.add_error(f"Action [{a_idx}] StepGroup [{sg_idx}] actionableDeeplink contains web URL: {uri}")

            # Check validationDeeplink URI if present
            if sg.validationDeeplink is not None:
                uri = sg.validationDeeplink.deeplink
                if contains_urls(uri):
                    report.add_error(f"Action [{a_idx}] StepGroup [{sg_idx}] validationDeeplink contains web URL: {uri}")

    return report


def validate_response(response: Union[ContextDeeplinkResponse, Dict[str, Any]]) -> ValidationReport:
    """Validate a full ContextDeeplinkResponse object or raw dict."""
    if isinstance(response, dict):
        try:
            response = ContextDeeplinkResponse.model_validate(response)
        except Exception as e:
            rep = ValidationReport()
            rep.add_error(f"Pydantic schema validation failed: {str(e)}")
            return rep

    report = ValidationReport()
    for i, goal in enumerate(response.contexts):
        goal_report = validate_goal(goal)
        for err in goal_report.errors:
            report.add_error(f"Context [{i}]: {err}")
        for warn in goal_report.warnings:
            report.add_warning(f"Context [{i}]: {warn}")

    return report
