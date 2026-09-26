"""API request and response models for FixFlow (Samsung PRISM Theme 02)."""
from typing import List, Optional

from pydantic import BaseModel, Field

from schema import (
    Action,
    BaseDeeplink,
    Condition,
    ContextDeeplinkResponse,
    Deeplink,
    Goal,
    ResultTypes,
    StepGroup,
    ValidationDeepLink,
    actionCategory,
)


class SIISResponse(BaseModel):
    """Raw SIIS (Samsung internal knowledge store) document associated with a query."""
    title: str = Field(..., description="Title of the SIIS reference document")
    content: str = Field(..., description="Troubleshooting guide text extracted from SIIS")


class TroubleshootRequest(BaseModel):
    """POST /v1/troubleshoot request envelope."""
    query: str = Field(..., description="User's colloquial device complaint")
    siis_response: Optional[SIISResponse] = Field(
        default=None,
        description="Optional SIIS reference payload. Required on cold path; optional on cache hit."
    )


class MetaBlock(BaseModel):
    """Telemetry, cache status, latency, and fallback metadata."""
    latency_ms: float = Field(default=0.0, description="End-to-end execution latency in milliseconds")
    cache_hit: bool = Field(default=False, description="Whether the request was served via cache")
    model: str = Field(default="", description="Identifier of the model or cache pipeline used")
    cost_usd: float = Field(default=0.0, description="Estimated API compute cost in USD")
    fallback: Optional[str] = Field(
        default=None,
        description="Fallback reason code if no match or error ('no_match', 'no_siis_context', etc.)"
    )


class TroubleshootResponse(BaseModel):
    """Full API response envelope supporting Appendix B metadata while strictly encapsulating ContextDeeplinkResponse."""
    query: str = Field(..., description="Original user complaint")
    query_variations: Optional[List[str]] = Field(
        default=None,
        description="Paraphrased query variations (8-10 items when generated)"
    )
    response: ContextDeeplinkResponse = Field(
        ...,
        description="Standard hackathon response containing list of Goal objects"
    )
    meta: Optional[MetaBlock] = Field(
        default=None,
        description="Operational telemetry and execution metadata"
    )


__all__ = [
    "BaseDeeplink",
    "Deeplink",
    "Condition",
    "ResultTypes",
    "actionCategory",
    "ValidationDeepLink",
    "StepGroup",
    "Action",
    "Goal",
    "ContextDeeplinkResponse",
    "SIISResponse",
    "TroubleshootRequest",
    "MetaBlock",
    "TroubleshootResponse",
]
