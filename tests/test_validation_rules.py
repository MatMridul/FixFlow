"""Comprehensive unit tests for validation rules, URL scrubber, and schema validator."""
import json
from pathlib import Path
import pytest

from schema import (
    Action,
    Condition,
    ContextDeeplinkResponse,
    Deeplink,
    Goal,
    ResultTypes,
    StepGroup,
    ValidationDeepLink,
    actionCategory,
)
from validation import (
    RuleViolation,
    contains_urls,
    scrub_goal,
    scrub_urls,
    validate_action_category_and_deeplinks,
    validate_action_name,
    validate_action_ordering,
    validate_description,
    validate_goal,
    validate_goal_syntax,
    validate_no_urls,
    validate_response,
    validate_score,
    validate_step,
    validate_title,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class TestGoalSyntaxValidator:
    def test_valid_goal_syntax(self):
        assert validate_goal_syntax("Follow these steps to perform this Screen Damage Troubleshooting").valid
        assert validate_goal_syntax("Follow these steps to perform this Display Brightness Configuration").valid
        assert validate_goal_syntax("Follow these steps to perform this Battery Optimization Troubleshooting").valid

    def test_invalid_goal_syntax(self):
        # Missing prefix
        res = validate_goal_syntax("Perform this Screen Damage Troubleshooting")
        assert not res.valid
        assert "does not follow required pattern" in res.message

        # Missing suffix
        res = validate_goal_syntax("Follow these steps to perform this Screen Damage Guide")
        assert not res.valid

        # Empty string
        res = validate_goal_syntax("")
        assert not res.valid


class TestTitleValidator:
    def test_valid_titles(self):
        assert validate_title("Screen display damage").valid
        assert validate_title("Screen flicker").valid
        assert validate_title("Battery drain issue").valid
        assert validate_title("Check Wi-Fi connection").valid

    def test_invalid_word_count(self):
        # 1 word
        assert not validate_title("Display").valid
        # 4 words
        assert not validate_title("Screen display damage issue").valid

    def test_invalid_casing(self):
        # Title case instead of sentence case
        res = validate_title("Screen Display Damage")
        assert not res.valid
        assert "Title Case instead of Sentence Case" in res.message

        # All lowercase
        assert not validate_title("screen display damage").valid


class TestActionNameValidator:
    def test_valid_action_names(self):
        assert validate_action_name("Back Up Phone Data").valid
        assert validate_action_name("Schedule Screen Repair Service").valid
        assert validate_action_name("Adjust Screen Brightness").valid
        assert validate_action_name("Turn on Power Saving").valid

    def test_invalid_action_names(self):
        # Lowercase first letter
        assert not validate_action_name("back up phone data").valid
        # Empty string
        assert not validate_action_name("").valid


class TestDescriptionValidator:
    def test_valid_descriptions(self):
        # Official sample examples (9 & 12 words)
        assert validate_description("It will facilitate secure data transfer between your devices").valid
        assert validate_description("It will help you locate the nearest Samsung service center and schedule").valid
        # 6 words
        assert validate_description("It will stabilise your display brightness").valid

    def test_invalid_descriptions(self):
        # Missing "It will"
        res = validate_description("This will stabilise your display brightness")
        assert not res.valid
        assert "must start with 'It will'" in res.message


class TestStepValidator:
    def test_valid_steps(self):
        assert validate_step("Navigate to and open Settings.").valid
        assert validate_step("Tap on Accounts and backup.").valid
        assert validate_step("Select Back up data to secure your personal files.").valid
        assert validate_step("Restart your phone.").valid

    def test_step_with_prohibited_urls(self):
        res = validate_step("Visit https://support.samsung.com/screen for repairs.")
        assert not res.valid
        assert "prohibited external web URL" in res.message

        res2 = validate_step("Click [here](http://samsung.com) to view instructions.")
        assert not res2.valid
        assert "prohibited external web URL" in res2.message


class TestActionCategoryAndOrdering:
    def test_manual_action_with_deeplink_rejected(self):
        action = Action(
            actionName="Manual Service Call",
            description="It will schedule a service technician visit",
            category=actionCategory.manual,
            stepGroups=[
                StepGroup(
                    steps=["Call support."],
                    actionableDeeplink=Deeplink(
                        deeplink="bixby://masked/service",
                        description="Service call",
                    ),
                )
            ],
        )
        res = validate_action_category_and_deeplinks(action)
        assert not res.valid
        assert "Manual action 'Manual Service Call' step group 0 cannot carry actionableDeeplink" in res.message

    def test_action_ordering_critical_last(self):
        auto_action = Action(
            actionName="Adjust Brightness",
            description="It will lower brightness",
            category=actionCategory.auto,
            stepGroups=[],
        )
        critical_action = Action(
            actionName="Factory Data Reset",
            description="It will wipe device data",
            category=actionCategory.critical,
            stepGroups=[],
        )

        # Valid: auto before critical
        assert validate_action_ordering([auto_action, critical_action]).valid

        # Invalid: critical before auto
        res = validate_action_ordering([critical_action, auto_action])
        assert not res.valid
        assert "Critical actions must be sorted last" in res.message


class TestUrlScrubber:
    def test_contains_urls(self):
        assert contains_urls("Visit http://samsung.com")
        assert contains_urls("Visit https://samsung.com/support")
        assert contains_urls("Visit www.samsung.com")
        assert contains_urls("Check [this link](https://samsung.com)")
        assert not contains_urls("Open Settings and tap Display.")
        assert not contains_urls("bixby://masked/act/12345")
        assert not contains_urls("voiceassist://masked/act/12345")

    def test_scrub_urls(self):
        text = "Visit https://samsung.com/help or [Support](http://support.samsung.com) for details."
        scrubbed = scrub_urls(text)
        assert "https://" not in scrubbed
        assert "http://" not in scrubbed
        assert "Support" in scrubbed
        assert not contains_urls(scrubbed)

    def test_scrub_goal(self):
        goal = Goal(
            goal="Follow these steps to perform this Screen Troubleshooting",
            title="Screen flicker",
            score=0.9,
            actions=[
                Action(
                    actionName="Contact Support Online",
                    description="It will connect you to https://support.samsung.com today",
                    category=actionCategory.manual,
                    stepGroups=[
                        StepGroup(
                            steps=[
                                "Visit https://samsung.com/service for details.",
                                "Follow the on-screen steps.",
                            ]
                        )
                    ],
                )
            ],
        )
        scrubbed = scrub_goal(goal)
        assert not contains_urls(scrubbed.actions[0].description)
        assert not contains_urls(scrubbed.actions[0].stepGroups[0].steps[0])


class TestFullSampleValidation:
    """Verify that the official sample_output.json passes all validation rules completely."""

    def test_sample_output_passes_full_validation(self):
        sample_path = DATA_DIR / "sample_output.json"
        with open(sample_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        response = ContextDeeplinkResponse.model_validate(raw_data["response"])
        report = validate_response(response)

        assert report.is_valid, f"Validation errors: {report.errors}"
        assert len(report.errors) == 0
        # Check that it doesn't raise
        report.raise_if_invalid()
