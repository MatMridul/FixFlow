"""Completes N4 for the catalog-derivable slice of the 432/570 entries whose
`validation` object is `{deeplink, key}` only (finding E, corrected).

Direct inspection of data/deeplinks.json's 138 entries that DO carry a full
validation object shows a 100%-consistent pattern:

    originalType == "onURL"  =>  {resultType: "boolean", condition: "equal", value: "True"}
    (138/138, no exceptions, no other originalType ever has a full object)

That single data point lets us close most of the remaining gap without
touching SIIS text at all:

- onURL (138/570):    already 100% covered by the catalog itself. Nothing to do.
- offURL (138/570):   the symmetric twin of onURL. We infer
                       {boolean, equal, "False"} by symmetry with the
                       verified onURL pattern. This is a HYPOTHESIS, not a
                       verified fact — no offURL entry in the catalog
                       actually confirms it, since 0 of them carry a full
                       validation object. Flagged `inferred=True` in the
                       output so Dev A's SIIS-provenance step (N5) can
                       override it if the step text says otherwise.
- onClickURL (253/570): these open a page; they have no on/off state to
                       validate. Correct answer is `None`, not a guessed
                       boolean — inventing one would silently claim a
                       verification the action can't actually perform.
- updateURL (36/570):  sets a specific numeric/string value (e.g. a
                       brightness level, a timeout duration). The target
                       value is genuinely not in the catalog and genuinely
                       requires reading the SIIS step text ("set timeout to
                       30 seconds") to determine. This is the one slice
                       finding E's original claim was right about — stays
                       Dev A's extraction-side work.
"""
from __future__ import annotations

from typing import Optional

from catalog.models import CatalogEntry


def infer_validation_ref(entry: CatalogEntry) -> Optional[dict]:
    """Best-effort validationDeeplink fields derivable from the catalog
    alone, for entries whose `validation` lacks resultType/condition/value.
    Returns None when no catalog-only inference is safe (onClickURL,
    updateURL, or no validation object at all)."""
    if entry.validation is None:
        return None
    if entry.validation.resultType is not None:
        # Already complete — not this function's job, see
        # resolution.binder._to_validation_ref for the verbatim-copy path.
        return {
            "deeplink": entry.validation.deeplink,
            "key": entry.validation.key,
            "resultType": entry.validation.resultType,
            "condition": entry.validation.condition,
            "value": entry.validation.value,
            "inferred": False,
        }

    base = {"deeplink": entry.validation.deeplink, "key": entry.validation.key}

    if entry.originalType == "offURL":
        return {
            **base,
            "resultType": "boolean",
            "condition": "equal",
            "value": "False",
            "inferred": True,
        }

    # onClickURL (page-open, no state to validate) and updateURL (numeric
    # value genuinely requires SIIS text) both correctly return None here.
    return None
