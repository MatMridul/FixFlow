"""N4 completion tests, run against the real catalog. The 138-entry
verified pattern (onURL -> boolean/equal/True) and the resulting
originalType breakdown of the 432 partial entries were established by
direct inspection (see resolution/validation_inference.py docstring), not
assumed — these tests pin that data shape so a catalog refresh would flag
a real regression rather than silently drifting.
"""
from __future__ import annotations

import json
from pathlib import Path

from catalog.loader import load_catalog
from resolution.validation_inference import infer_validation_ref

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _raw_catalog():
    return json.loads((DATA_DIR / "deeplinks.json").read_text(encoding="utf-8"))["deeplinks"]


def test_onurl_entries_all_have_full_validation_already():
    entries = [e for e in _raw_catalog() if e["originalType"] == "onURL"]
    assert len(entries) == 138
    assert all(e["validation"] and "resultType" in e["validation"] for e in entries)


def test_offurl_missing_validation_gets_symmetric_inference():
    catalog = load_catalog(DATA_DIR / "deeplinks.json")
    off_url_partial = next(
        e for e in catalog if e.originalType == "offURL" and e.validation and e.validation.resultType is None
    )
    ref = infer_validation_ref(off_url_partial)
    assert ref is not None
    assert ref["resultType"] == "boolean"
    assert ref["condition"] == "equal"
    assert ref["value"] == "False"
    assert ref["inferred"] is True


def test_onclickurl_gets_no_validation_not_a_guessed_boolean():
    catalog = load_catalog(DATA_DIR / "deeplinks.json")
    page_entry = next(e for e in catalog if e.originalType == "onClickURL" and e.validation)
    assert infer_validation_ref(page_entry) is None


def test_updateurl_stays_none_requires_siis_text():
    catalog = load_catalog(DATA_DIR / "deeplinks.json")
    update_entry = next(e for e in catalog if e.originalType == "updateURL" and e.validation)
    assert infer_validation_ref(update_entry) is None


def test_full_validation_entry_is_copied_verbatim_not_reinferred():
    catalog = load_catalog(DATA_DIR / "deeplinks.json")
    dl0542 = catalog.get("DL-0542")
    ref = infer_validation_ref(dl0542)
    assert ref["inferred"] is False
    assert ref["value"] == "True"
