"""Loads data/deeplinks.json into a queryable Catalog.

The catalog is the sole source of truth for deeplink URIs (brief §4.2,
Catalog Integrity). Nothing downstream is allowed to invent or alter a URI —
this module is the only place that reads deeplinks.json.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator, Optional

from catalog.models import CatalogEntry

DEFAULT_CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "deeplinks.json"


class Catalog:
    """In-memory index over the deeplink catalog.

    Exposes lookup by id and iteration over resolvable (non-dummy) entries.
    Retrieval/matching lives in resolution/ — this class only loads + indexes.
    """

    def __init__(self, entries: list[CatalogEntry]):
        self._by_id: dict[str, CatalogEntry] = {e.id: e for e in entries}
        self._dummy_positive: Optional[CatalogEntry] = next(
            (e for e in entries if e.is_dummy_positive), None
        )
        self.scheme: str = "voiceassist"
        for e in entries:
            if "://" in e.deeplink:
                self.scheme = e.deeplink.split("://")[0]
                break

    def __len__(self) -> int:
        return len(self._by_id)

    def __iter__(self) -> Iterator[CatalogEntry]:
        return iter(self._by_id.values())

    def get(self, entry_id: str) -> Optional[CatalogEntry]:
        return self._by_id.get(entry_id)

    def resolvable_entries(self) -> list[CatalogEntry]:
        """All entries eligible for retrieval matching — excludes the
        dummy_positive placeholder, which is a fallback, not a match target."""
        return [e for e in self._by_id.values() if not e.is_dummy_positive]

    @property
    def dummy_positive(self) -> Optional[CatalogEntry]:
        return self._dummy_positive

    @property
    def dummy_positive_uri(self) -> str:
        if self._dummy_positive:
            return self._dummy_positive.deeplink
        return f"{self.scheme}://dummy_positive"


def load_catalog(path: Path | str = DEFAULT_CATALOG_PATH) -> Catalog:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = [CatalogEntry.model_validate(e) for e in raw["deeplinks"]]
    return Catalog(entries)
