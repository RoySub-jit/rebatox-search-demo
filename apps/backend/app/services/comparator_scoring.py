from __future__ import annotations

from collections.abc import Sequence

from app.schemas.comparator_scoring import (
    ComparatorScoringInput,
    ComparatorScoringResult,
)

FIELD_WEIGHTS: tuple[tuple[str, str, float], ...] = (
    ("same_target", "same target", 0.35),
    ("same_modality", "same modality", 0.25),
    ("same_route", "same route", 0.20),
    ("same_indication", "same indication", 0.15),
    ("same_scaffold", "same scaffold", 0.05),
)
MAX_RELEVANCE_SCORE = sum(weight for _, _, weight in FIELD_WEIGHTS)


def _human_join(parts: list[str]) -> str:
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    return f"{', '.join(parts[:-1])}, and {parts[-1]}"


def _match_label(score: float) -> str:
    if score >= 80:
        return "strong comparator match"
    if score >= 40:
        return "partial comparator match"
    return "weak comparator match"


def _build_rationale(
    *,
    comparator_name: str | None,
    relevance_score: float,
    matched_fields: list[str],
    missing_fields: list[str],
) -> str:
    if comparator_name:
        subject = comparator_name
    else:
        subject = "This comparator"

    if not matched_fields:
        return (
            f"{subject} is a weak comparator match because none of the weighted biologics "
            "relevance fields aligned."
        )

    matched_summary = _human_join(matched_fields)
    rationale = (
        f"{subject} is a {_match_label(relevance_score)} driven by {matched_summary}."
    )
    if missing_fields:
        rationale += f" Remaining gaps: {_human_join(missing_fields)}."

    return rationale


def score_comparator(
    comparator: ComparatorScoringInput | None,
) -> ComparatorScoringResult:
    if comparator is None:
        return ComparatorScoringResult(
            comparator_name=None,
            relevance_score=0.0,
            rationale=(
                "No comparator was provided, so no biologics relevance score could be assigned."
            ),
        )

    matched_fields: list[str] = []
    missing_fields: list[str] = []
    weighted_score = 0.0

    for field_name, label, weight in FIELD_WEIGHTS:
        if getattr(comparator, field_name):
            matched_fields.append(f"{label} (+{int(weight * 100)}%)")
            weighted_score += weight
        else:
            missing_fields.append(label)

    relevance_score = round((weighted_score / MAX_RELEVANCE_SCORE) * 100, 2)

    return ComparatorScoringResult(
        comparator_name=comparator.comparator_name,
        relevance_score=relevance_score,
        rationale=_build_rationale(
            comparator_name=comparator.comparator_name,
            relevance_score=relevance_score,
            matched_fields=matched_fields,
            missing_fields=missing_fields,
        ),
    )


def rank_comparators(
    comparators: Sequence[ComparatorScoringInput],
) -> list[ComparatorScoringResult]:
    ranked = [score_comparator(comparator) for comparator in comparators]
    return sorted(
        ranked,
        key=lambda item: (-item.relevance_score, (item.comparator_name or "").lower()),
    )
