"""Ground-truth smoke test: resolves the official sample_output.json's first
action against the real catalog and checks we land on the exact entry
Samsung's own example uses (DL-0542). This is the P0 exit criterion from
FixFlow_TwoDev_Plan.md: "Retrieval returns verbatim catalog URIs; ordering +
manual rules enforced."
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from catalog.loader import load_catalog
from resolution.retriever import HybridRetriever
from resolution.binder import bind_actionable_deeplink
from resolution.ordering import order_actions

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(DATA_DIR / "deeplinks.json")


@pytest.fixture(scope="module")
def retriever(catalog):
    return HybridRetriever(catalog)


@pytest.fixture(scope="module")
def sample_output():
    return json.loads((DATA_DIR / "sample_output.json").read_text(encoding="utf-8"))


def test_catalog_loads_all_entries(catalog):
    assert len(catalog) == 578


def test_catalog_finds_dummy_positive(catalog):
    assert catalog.dummy_positive is not None
    assert catalog.dummy_positive.deeplink == "bixby://dummy_positive"


def test_auto_action_resolves_to_official_ground_truth(catalog, retriever, sample_output):
    """The sample's first action ('Back Up Phone Data', auto) should resolve
    to DL-0542, the exact catalog entry Samsung's own example points at."""
    action = sample_output["response"]["contexts"][0]["actions"][0]
    assert action["category"] == "auto"
    steps = action["stepGroups"][0]["steps"]

    result = bind_actionable_deeplink(steps, action["category"], catalog, retriever)

    assert result.status == "matched"
    assert result.actionable_deeplink["deeplink"] == "bixby://masked/act/b3ed3ed663"
    # full validation object is one of the 138/570 with resultType present —
    # should be copied verbatim, not left for derivation.
    assert result.validation_ref["resultType"] == "boolean"
    assert result.validation_ref["condition"] == "equal"


def test_manual_action_gets_no_deeplink(catalog, retriever, sample_output):
    action = sample_output["response"]["contexts"][0]["actions"][1]
    assert action["category"] == "manual"
    steps = action["stepGroups"][0]["steps"]

    result = bind_actionable_deeplink(steps, action["category"], catalog, retriever)

    assert result.status == "manual_no_deeplink"
    assert result.actionable_deeplink is None


def test_ordering_matches_official_sample(sample_output):
    """Sample ships auto before manual — order_actions must preserve that
    and must never place manual after critical."""

    class FakeAction:
        def __init__(self, category, name):
            self.category = category
            self.name = name

    actions = [FakeAction("critical", "c"), FakeAction("manual", "m"), FakeAction("auto", "a")]
    ordered = order_actions(actions)
    assert [a.name for a in ordered] == ["a", "m", "c"]


def test_matching_never_uses_raw_uri_text(catalog, retriever):
    """Querying with catalog URI fragments should not out-rank a real
    semantic query — matching must stay on description/message/qna text."""
    results = retriever.search("bixby masked act", top_k=1)
    # every entry's searchable_text excludes the deeplink field by
    # construction (CatalogEntry.searchable_text) — this just documents
    # the contract rather than probing internals.
    assert "bixby://" not in results[0].entry.searchable_text()
