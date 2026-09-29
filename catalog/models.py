"""Data models for the raw deeplink catalog (data/deeplinks.json).

Field shapes are taken directly from inspecting the real catalog, not from the
brief's prose (see FixFlow_Idea_v3.md findings E/F/G). In particular:
- `validation` is only ever `{deeplink, key}` — resultType/condition/value are
  never supplied here and must be derived elsewhere (N4, Dev A's extraction).
- `description` is full-sentence prose, not a breadcrumb path (finding F).
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class ValidationRef(BaseModel):
    deeplink: str
    key: str
    # Present on ~24% of entries (138/570) — when set, copy verbatim instead
    # of deriving from SIIS text (corrects FixFlow_Idea_v3.md finding E,
    # which was based on an under-sampled check).
    resultType: Optional[str] = None
    condition: Optional[str] = None
    value: Optional[str] = None


class CatalogEntry(BaseModel):
    id: str
    deeplink: str
    description: str
    message: str
    originalType: Optional[str] = None
    control_type: Optional[int] = None
    qna_description: str = ""
    validation: Optional[ValidationRef] = None

    @property
    def is_dummy_positive(self) -> bool:
        return self.deeplink in ("bixby://dummy_positive", "voiceassist://dummy_positive") or self.deeplink.endswith("://dummy_positive")

    def searchable_text(self) -> str:
        """Text surface used for matching. Never the deeplink/URI itself —
        catalog integrity requires matching on metadata only (brief §4.2)."""
        parts = [self.description, self.message, self.qna_description]
        text = " ".join(p for p in parts if p)
        lowered = text.lower()
        extras = []
        if "quick access panel" in lowered:
            extras.append("edge panels edge panel")
        elif "edge panel" in lowered:
            extras.append("quick access panels")
        if "techcorp" in lowered:
            extras.append("samsung")
        elif "samsung" in lowered:
            extras.append("techcorp")
        if "data transfer" in lowered:
            extras.append("smart switch")
        elif "smart switch" in lowered:
            extras.append("data transfer")
        if extras:
            text = f"{text} {' '.join(extras)}"
        return text
