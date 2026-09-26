"""Novelty N1: Multi-Intent Clause Splitter and Signature-Based Merger."""
import re
from typing import List, Tuple

from enrichment.intent_signature import IntentSignature, extract_intent_signature


def split_raw_clauses(text: str) -> List[str]:
    """
    Split a compound sentence into candidate clauses.
    Splits on coordinating conjunctions and boundary punctuation:
      - ' and also ', ' and ', ' as well as ', ' along with '
      - ' plus ', ' but ', ' yet '
      - ';', ',' followed by conjunction
    """
    if not text or not text.strip():
        return []

    # Normalize whitespace
    cleaned = re.sub(r"\s+", " ", text).strip()

    # Pattern for compound sentence delimiters
    pattern = r"(?:;\s*|,\s*(?:and|also|plus|but)\s*|\s+(?:and also|as well as|along with|and|plus|also)\s+)"

    raw_parts = re.split(pattern, cleaned, flags=re.IGNORECASE)

    # Filter out empty or trivial fragments
    clauses = [part.strip(" ,;.") for part in raw_parts if len(part.strip(" ,;.")) > 3]

    return clauses if clauses else [cleaned]


def decompose_query_intents(query: str) -> List[Tuple[str, IntentSignature]]:
    """
    Decompose a user complaint into distinct sub-intents.
    
    Over-splitting Protection:
      If adjacent clauses share the exact same domain, component, and symptom
      (e.g., 'phone is slow' and 'very laggy'), they are merged into one sub-intent.
    """
    raw_clauses = split_raw_clauses(query)

    if len(raw_clauses) <= 1:
        return [(query, extract_intent_signature(query))]

    clause_signatures: List[Tuple[str, IntentSignature]] = []

    for clause in raw_clauses:
        sig = extract_intent_signature(clause)
        clause_signatures.append((clause, sig))

    # Merge redundant/overlapping adjacent clauses
    merged: List[Tuple[str, IntentSignature]] = []

    for clause, sig in clause_signatures:
        if not merged:
            merged.append((clause, sig))
            continue

        prev_clause, prev_sig = merged[-1]

        # Check if clauses represent the exact same domain & symptom
        same_domain = (prev_sig.domain == sig.domain) and (sig.domain != "Unknown")
        same_symptom = (prev_sig.symptom == sig.symptom) and (sig.symptom is not None)
        same_polarity = prev_sig.polarity == sig.polarity

        if same_domain and same_symptom and same_polarity:
            # Over-splitting detected: merge into single compound phrase
            combined_clause = f"{prev_clause} and {clause}"
            merged[-1] = (combined_clause, prev_sig)
        else:
            merged.append((clause, sig))

    return merged
