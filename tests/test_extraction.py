"""Unit tests for schema-constrained extractor and prompt builder."""
import json
from pathlib import Path
import pytest

from extraction import StructureExtractor, build_extraction_prompt, clean_llm_json
from schema import Goal
from validation import validate_goal

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class TestExtractionPrompt:
    def test_build_prompt_includes_all_components(self):
        prompt = build_extraction_prompt(
            query="Battery drains fast",
            siis_title="Battery Optimization",
            siis_content="Step 1: Turn on Power saving mode.",
        )
        assert "GROUND TRUTH ONLY" in prompt
        assert "CONTRACT 1 ADHERENCE" in prompt
        assert "Battery drains fast" in prompt
        assert "Battery Optimization" in prompt
        assert "Turn on Power saving mode." in prompt

    def test_clean_llm_json(self):
        fenced_json = "```json\n{\"goal\": \"Follow these steps\", \"score\": 0.9}\n```"
        assert clean_llm_json(fenced_json) == "{\"goal\": \"Follow these steps\", \"score\": 0.9}"

        bare_json = "Some intro text: {\"key\": \"value\"} Some outro text."
        assert clean_llm_json(bare_json) == "{\"key\": \"value\"}"


class TestStructureExtractor:
    def test_extractor_with_mock_llm(self):
        mock_output = json.dumps({
            "goal": "Follow these steps to perform this Display Troubleshooting",
            "title": "Screen flicker",
            "score": 0.93,
            "actions": [
                {
                    "actionName": "Adjust Refresh Rate",
                    "description": "It will stabilize your screen refresh rate",
                    "category": "auto",
                    "stepGroups": [
                        {
                            "steps": [
                                "Navigate to and open Settings.",
                                "Tap on Display.",
                                "Select Motion smoothness.",
                                "Choose Standard 60Hz."
                            ]
                        }
                    ]
                }
            ]
        })

        extractor = StructureExtractor(llm_callable=lambda p: mock_output)
        goal = extractor.extract(
            query="Screen flickers rapidly",
            siis_title="Motion smoothness configuration",
            siis_content="Open Settings > Display > Motion smoothness and set to Standard.",
        )

        assert goal is not None
        assert isinstance(goal, Goal)
        # Contract 1 check: deeplinks must be None
        for action in goal.actions:
            for sg in action.stepGroups:
                assert sg.actionableDeeplink is None
                assert sg.validationDeeplink is None

        # Schema & text rules check
        report = validate_goal(goal)
        assert report.is_valid, f"Validation errors: {report.errors}"

    def test_extractor_deterministic_fallback_with_real_siis(self):
        siis_path = DATA_DIR / "siis_responses.json"
        with open(siis_path, "r", encoding="utf-8") as f:
            siis_data = json.load(f)

        first_scenario = siis_data["responses"][0]
        query = first_scenario["original_query"]
        siis_title = first_scenario["siis_response"]["title"]
        siis_content = first_scenario["siis_response"]["content"]

        # Extractor without LLM (falls back to deterministic parsing)
        extractor = StructureExtractor(llm_callable=None)
        goal = extractor.extract(query=query, siis_title=siis_title, siis_content=siis_content)

        assert goal is not None
        assert isinstance(goal, Goal)
        assert len(goal.actions) > 0

        # Contract 1 verification
        for action in goal.actions:
            for sg in action.stepGroups:
                assert sg.actionableDeeplink is None
                assert sg.validationDeeplink is None

        # Verify compliance
        report = validate_goal(goal)
        assert report.is_valid, f"Validation errors: {report.errors}"

    def test_extractor_empty_siis_returns_none(self):
        extractor = StructureExtractor()
        assert extractor.extract("query", "title", "") is None
        assert extractor.extract("query", "title", "   ") is None
