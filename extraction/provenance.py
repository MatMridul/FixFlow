"""Novelty N5: Step-to-SIIS Provenance Bipartite Filter (Hallucination Elimination)."""
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from schema import Action, Goal, StepGroup


def split_into_sentences(text: str) -> List[str]:
    """Split raw text into clean, individual sentences."""
    if not text:
        return []
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Split by common sentence terminators (. ! ? or newline)
    raw_sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
    sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 3]
    return sentences


def _tokenize(text: str) -> Set[str]:
    """Extract lowercase alphanumeric tokens ignoring common stopwords."""
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "to", "on", "in",
        "of", "for", "and", "or", "it", "will", "this", "that", "you",
        "your", "tap", "open", "go", "select", "click", "step"
    }
    words = re.findall(r"\b[a-zA-Z0-9_-]+\b", text.lower())
    return {w for w in words if w not in stopwords and len(w) > 1}


def compute_sentence_overlap(step_text: str, siis_sentences: List[str]) -> Tuple[float, Optional[str]]:
    """
    Compute bipartite overlap between a candidate step and SIIS sentences.
    Returns:
        (best_overlap_score, best_matching_sentence)
    """
    step_tokens = _tokenize(step_text)
    if not step_tokens:
        return 0.0, None

    best_score = 0.0
    best_sentence = None

    for sentence in siis_sentences:
        sent_tokens = _tokenize(sentence)
        if not sent_tokens:
            continue

        intersection = step_tokens.intersection(sent_tokens)
        if not intersection:
            continue

        # Containment score: proportion of step keywords substantiated in the sentence
        containment = len(intersection) / len(step_tokens)

        # Jaccard similarity
        union = step_tokens.union(sent_tokens)
        jaccard = len(intersection) / len(union)

        # Combined harmonic/weighted score prioritizing containment
        score = (0.75 * containment) + (0.25 * jaccard)

        if score > best_score:
            best_score = score
            best_sentence = sentence

    return min(1.0, best_score), best_sentence


def filter_provenance(
    goal: Goal,
    siis_text: str,
    threshold: float = 0.20,
) -> Tuple[Goal, float, List[Dict[str, Any]]]:
    """
    Filter out hallucinated steps not grounded in the SIIS reference text.

    Args:
        goal: Raw extracted Goal object.
        siis_text: Combined SIIS title and content text.
        threshold: Minimum overlap score required to keep a step.

    Returns:
        (filtered_goal, grounding_coverage, provenance_map)
    """
    siis_sentences = split_into_sentences(siis_text)
    if not siis_sentences:
        # If no SIIS sentences, all steps are technically ungrounded
        return goal, 0.0, []

    total_steps = 0
    grounded_steps = 0
    provenance_map: List[Dict[str, Any]] = []

    clean_actions: List[Action] = []

    for action in goal.actions:
        clean_step_groups: List[StepGroup] = []

        for group in action.stepGroups:
            valid_steps: List[str] = []

            for step in group.steps:
                total_steps += 1
                overlap_score, matched_sentence = compute_sentence_overlap(step, siis_sentences)

                is_grounded = overlap_score >= threshold
                if is_grounded:
                    grounded_steps += 1
                    valid_steps.append(step)

                provenance_map.append({
                    "action_name": action.actionName,
                    "step": step,
                    "grounded": is_grounded,
                    "overlap_score": round(overlap_score, 3),
                    "matched_sentence": matched_sentence,
                })

            if valid_steps:
                # Reconstruct step group with only grounded steps
                clean_step_groups.append(
                    StepGroup(
                        steps=valid_steps,
                        actionableDeeplink=group.actionableDeeplink,
                        validationDeeplink=group.validationDeeplink,
                    )
                )

        if clean_step_groups:
            # Reconstruct action with remaining valid step groups
            clean_actions.append(
                Action(
                    actionName=action.actionName,
                    description=action.description,
                    category=action.category,
                    stepGroups=clean_step_groups,
                )
            )

    grounding_coverage = (grounded_steps / total_steps) if total_steps > 0 else 0.0

    filtered_goal = Goal(
        goal=goal.goal,
        title=goal.title,
        score=goal.score,
        actions=clean_actions,
    )

    return filtered_goal, round(grounding_coverage, 3), provenance_map
