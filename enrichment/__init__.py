"""FixFlow enrichment package for intent signature extraction and clause splitting."""
from enrichment.intent_signature import (
    IntentSignature,
    extract_intent_signature,
    signatures_compatible,
)

__all__ = [
    "IntentSignature",
    "extract_intent_signature",
    "signatures_compatible",
]
