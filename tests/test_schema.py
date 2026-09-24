"""Unit tests for schema contracts, API models, and starter kit validation."""
import json
from pathlib import Path
import pytest
from pydantic import ValidationError

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
from api.models import (
    MetaBlock,
    SIISResponse,
    TroubleshootRequest,
    TroubleshootResponse,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class TestSchemaContracts:
    """Verify that official schema models and sample output satisfy all contract rules."""

    def test_sample_output_json_validates(self):
        sample_path = DATA_DIR / "sample_output.json"
        assert sample_path.exists(), "data/sample_output.json must exist"

        with open(sample_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        # 1. Validates as full TroubleshootResponse envelope
        response_envelope = TroubleshootResponse.model_validate(raw_data)
        assert response_envelope.query == raw_data["query"]
        assert len(response_envelope.response.contexts) == 1

        # 2. Validates core ContextDeeplinkResponse
        context_response = ContextDeeplinkResponse.model_validate(raw_data["response"])
        assert len(context_response.contexts) == 1

        goal: Goal = context_response.contexts[0]
        assert goal.goal == "Follow these steps to perform this Screen Damage Troubleshooting"
        assert goal.title == "Screen display damage"
        assert goal.score == 0.95
        assert len(goal.actions) == 2

        # Check action 1: Auto action with deeplinks
        action1: Action = goal.actions[0]
        assert action1.actionName == "Back Up Phone Data"
        assert action1.category == actionCategory.auto
        assert len(action1.stepGroups) == 1
        sg1: StepGroup = action1.stepGroups[0]
        assert len(sg1.steps) == 3
        assert sg1.actionableDeeplink is not None
        assert sg1.actionableDeeplink.originalType == "onURL"
        assert sg1.validationDeeplink is not None
        assert sg1.validationDeeplink.resultType == ResultTypes.boolean
        assert sg1.validationDeeplink.condition == Condition.equal
        assert sg1.validationDeeplink.value == "True"

        # Check action 2: Manual action without deeplinks
        action2: Action = goal.actions[1]
        assert action2.actionName == "Schedule Screen Repair Service"
        assert action2.category == actionCategory.manual
        sg2: StepGroup = action2.stepGroups[0]
        assert sg2.actionableDeeplink is None
        assert sg2.validationDeeplink is None

    def test_illegal_schema_raises_validation_error(self):
        # 1. Invalid action category
        with pytest.raises(ValidationError):
            Action(
                actionName="Test",
                description="It will test invalid category",
                stepGroups=[],
                category="not_a_category",  # type: ignore
            )

        # 2. Missing required fields in Goal
        with pytest.raises(ValidationError):
            Goal.model_validate({"goal": "Test goal"})

        # 3. Invalid ResultType in ValidationDeepLink
        with pytest.raises(ValidationError):
            ValidationDeepLink(
                deeplink="bixby://test",
                key="test_key",
                resultType="invalid_result_type",  # type: ignore
            )

        # 4. Invalid Condition in ValidationDeepLink
        with pytest.raises(ValidationError):
            ValidationDeepLink(
                deeplink="bixby://test",
                key="test_key",
                condition="between",  # type: ignore
            )

        # 5. Non-numeric score in Goal
        with pytest.raises(ValidationError):
            Goal(
                goal="Follow these steps to perform this Troubleshooting",
                title="Title",
                actions=[],
                score="not_a_number",  # type: ignore
            )


class TestApiModels:
    """Verify TroubleshootRequest and TroubleshootResponse envelopes."""

    def test_troubleshoot_request_valid(self):
        # Without SIIS
        req1 = TroubleshootRequest(query="Screen flickers")
        assert req1.query == "Screen flickers"
        assert req1.siis_response is None

        # With SIIS
        req2 = TroubleshootRequest(
            query="Screen flickers",
            siis_response=SIISResponse(
                title="Screen issue",
                content="Guide content here"
            )
        )
        assert req2.siis_response is not None
        assert req2.siis_response.title == "Screen issue"

    def test_troubleshoot_request_invalid(self):
        with pytest.raises(ValidationError):
            TroubleshootRequest.model_validate({})

        with pytest.raises(ValidationError):
            TroubleshootRequest.model_validate({"query": "Valid", "siis_response": {"title": "Missing content"}})

    def test_troubleshoot_response_with_meta_and_variations(self):
        resp = TroubleshootResponse(
            query="Battery drains fast",
            query_variations=["battery dying quickly", "fast battery drain"],
            response=ContextDeeplinkResponse(
                contexts=[
                    Goal(
                        goal="Follow these steps to perform this Battery Troubleshooting",
                        title="Battery drain",
                        score=0.92,
                        actions=[
                            Action(
                                actionName="Turn On Power Saving",
                                description="It will extend your device battery life",
                                category=actionCategory.auto,
                                stepGroups=[
                                    StepGroup(
                                        steps=["Open Settings.", "Tap Battery.", "Turn on Power saving."],
                                        actionableDeeplink=Deeplink(
                                            deeplink="bixby://masked/power_saving",
                                            description="Power saving settings",
                                            message="Turn on Power saving",
                                        ),
                                        validationDeeplink=ValidationDeepLink(
                                            deeplink="bixby://masked/val_power",
                                            key="Power saving",
                                            resultType=ResultTypes.boolean,
                                            condition=Condition.equal,
                                            value="true",
                                        ),
                                    )
                                ],
                            )
                        ],
                    )
                ]
            ),
            meta=MetaBlock(
                latency_ms=14.5,
                cache_hit=True,
                model="cache-compositional-v1",
                cost_usd=0.0,
                fallback=None,
            ),
        )
        data = resp.model_dump()
        assert data["meta"]["cache_hit"] is True
        assert data["meta"]["latency_ms"] == 14.5
        assert len(data["query_variations"]) == 2
        assert len(data["response"]["contexts"]) == 1


class TestStarterKitIntegrity:
    """Verify that all starter kit data assets extracted into data/ are intact and non-empty."""

    def test_starter_kit_files_exist_and_parse(self):
        deeplinks_path = DATA_DIR / "deeplinks.json"
        siis_path = DATA_DIR / "siis_responses.json"
        input_path = DATA_DIR / "input.txt"

        assert deeplinks_path.exists(), "deeplinks.json must exist in data/"
        assert siis_path.exists(), "siis_responses.json must exist in data/"
        assert input_path.exists(), "input.txt must exist in data/"

        with open(deeplinks_path, "r", encoding="utf-8") as f:
            deeplinks_data = json.load(f)
            assert isinstance(deeplinks_data, dict)
            assert "deeplinks" in deeplinks_data
            assert len(deeplinks_data["deeplinks"]) == 578, f"Expected 578 deeplinks, found {len(deeplinks_data['deeplinks'])}"

        with open(siis_path, "r", encoding="utf-8") as f:
            siis_data = json.load(f)
            assert "responses" in siis_data
            assert len(siis_data["responses"]) == 20

        with open(input_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            assert len(lines) == 20
