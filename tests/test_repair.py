"""Unit tests for programmatic auto-repair and single-shot LLM repair loop."""
import json
import pytest

from schema import Action, Deeplink, Goal, StepGroup, actionCategory
from validation import (
    contains_urls,
    programmatic_repair_goal,
    repair_goal_or_json,
    validate_goal,
)


class TestProgrammaticRepair:
    def test_repairs_missing_it_will_prefix(self):
        goal = Goal(
            goal="Follow these steps to perform this Display Troubleshooting",
            title="Screen flicker",
            score=0.9,
            actions=[
                Action(
                    actionName="Adjust Brightness",
                    description="lowers the display intensity",
                    category=actionCategory.auto,
                    stepGroups=[StepGroup(steps=["Adjust slider."])],
                )
            ],
        )
        assert not goal.actions[0].description.startswith("It will")
        repaired = programmatic_repair_goal(goal)
        assert repaired.actions[0].description.startswith("It will")
        assert validate_goal(repaired).is_valid

    def test_repairs_casing_and_word_counts(self):
        goal = Goal(
            goal="Follow these steps to perform this Display Troubleshooting",
            title="Screen Display Flicker Issue",  # 4 words, Title Case
            score=0.9,
            actions=[
                Action(
                    actionName="adjust screen brightness",  # lowercase
                    description="It will fix brightness",
                    category=actionCategory.auto,
                    stepGroups=[StepGroup(steps=["Open Settings."])],
                )
            ],
        )
        repaired = programmatic_repair_goal(goal)
        assert repaired.title == "Screen display flicker"
        assert repaired.actions[0].actionName == "Adjust Screen Brightness"
        assert validate_goal(repaired).is_valid

    def test_clears_deeplink_on_manual_action(self):
        goal = Goal(
            goal="Follow these steps to perform this Service Troubleshooting",
            title="Screen damage",
            score=0.8,
            actions=[
                Action(
                    actionName="Contact Service Center",
                    description="It will schedule a repair appointment",
                    category=actionCategory.manual,
                    stepGroups=[
                        StepGroup(
                            steps=["Call Samsung."],
                            actionableDeeplink=Deeplink(
                                deeplink="bixby://masked/service",
                                description="Service",
                            ),
                        )
                    ],
                )
            ],
        )
        # Initially invalid due to manual category with deeplink
        assert not validate_goal(goal).is_valid
        repaired = programmatic_repair_goal(goal)
        assert repaired.actions[0].stepGroups[0].actionableDeeplink is None
        assert validate_goal(repaired).is_valid

    def test_reorders_critical_action_to_last(self):
        critical_action = Action(
            actionName="Factory Reset",
            description="It will erase all user data",
            category=actionCategory.critical,
            stepGroups=[StepGroup(steps=["Reset phone."])],
        )
        auto_action = Action(
            actionName="Clear Cache",
            description="It will wipe cache partition",
            category=actionCategory.auto,
            stepGroups=[StepGroup(steps=["Clear cache."])],
        )
        goal = Goal(
            goal="Follow these steps to perform this Storage Troubleshooting",
            title="Storage issue",
            score=0.85,
            actions=[critical_action, auto_action],  # critical first: invalid
        )
        assert not validate_goal(goal).is_valid
        repaired = programmatic_repair_goal(goal)
        assert repaired.actions[-1].category == actionCategory.critical
        assert validate_goal(repaired).is_valid

    def test_scrubs_urls_during_repair(self):
        goal = Goal(
            goal="Follow these steps to perform this Display Troubleshooting",
            title="Screen flicker",
            score=0.9,
            actions=[
                Action(
                    actionName="Check Updates Online",
                    description="It will check https://samsung.com/update for software patches",
                    category=actionCategory.auto,
                    stepGroups=[
                        StepGroup(steps=["Visit https://samsung.com/patch for details."])
                    ],
                )
            ],
        )
        repaired = programmatic_repair_goal(goal)
        assert not contains_urls(repaired.actions[0].description)
        assert not contains_urls(repaired.actions[0].stepGroups[0].steps[0])
        assert validate_goal(repaired).is_valid


class TestSingleShotLlmRepair:
    def test_llm_repair_invoked_on_broken_json(self):
        broken_json = '{"invalid_key": "broken", "actions": "not_a_list"}'
        call_count = 0

        def mock_llm(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            assert "Validation Errors to Fix:" in prompt
            return json.dumps({
                "goal": "Follow these steps to perform this Display Troubleshooting",
                "title": "Screen flicker",
                "score": 0.88,
                "actions": [
                    {
                        "actionName": "Restart Device",
                        "description": "It will restart your phone to clear temporary glitches",
                        "category": "auto",
                        "stepGroups": [
                            {"steps": ["Press and hold Power button.", "Tap Restart."]}
                        ]
                    }
                ]
            })

        repaired_goal, report = repair_goal_or_json(
            broken_json,
            llm_callable=mock_llm,
            max_llm_attempts=1,
        )

        assert call_count == 1
        assert repaired_goal is not None
        assert report.is_valid
        assert repaired_goal.title == "Screen flicker"

    def test_llm_repair_fails_gracefully_on_invalid_return(self):
        broken_input = "Not even JSON"
        call_count = 0

        def mock_failing_llm(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            return "Still invalid output"

        repaired_goal, report = repair_goal_or_json(
            broken_input,
            llm_callable=mock_failing_llm,
            max_llm_attempts=1,
        )

        assert call_count == 1
        assert repaired_goal is None
        assert not report.is_valid
        assert len(report.errors) > 0
