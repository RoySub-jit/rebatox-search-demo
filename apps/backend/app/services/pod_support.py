from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from app.models.research import CandidatePOD, Study
from app.schemas.limitations import GeneratedLimitation
from app.schemas.pod_support import (
    CandidatePODSupportResult,
    GeneratedRecommendation,
)

POD_SCORE_BASELINES: dict[str, float] = {
    "explicit_pod_available": 72.0,
    "inferred_pod_from_public_data": 55.0,
    "analog_supported_provisional_pod": 32.0,
    "insufficient_public_data_for_pod": 12.0,
}


def _normalize_confidence_score(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None

    if value > Decimal("1"):
        return value / Decimal("100")

    return value


def _human_join(parts: list[str]) -> str:
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    return f"{', '.join(parts[:-1])}, and {parts[-1]}"


def _limitation_types(limitations: Sequence[GeneratedLimitation]) -> set[str]:
    return {limitation.limitation_type for limitation in limitations}


def _comparator_label(comparator_relevance_score: float | None) -> str:
    if comparator_relevance_score is None:
        return "no comparator score"
    if comparator_relevance_score >= 80:
        return "strong comparator relevance"
    if comparator_relevance_score >= 40:
        return "moderate comparator relevance"
    return "weak comparator relevance"


def _support_category(
    *,
    study: Study | None,
    candidate_pod: CandidatePOD | None,
    limitation_types: set[str],
) -> str:
    if study is None or candidate_pod is None:
        return "insufficient_public_data_for_pod"

    if "analog_only_evidence" in limitation_types:
        return "analog_supported_provisional_pod"

    if "no_explicit_pod" not in limitation_types:
        return "explicit_pod_available"

    severe_gap_count = sum(
        1
        for limitation_type in (
            "missing_route",
            "missing_species_relevance",
            "sparse_dose_context",
            "low_confidence_extraction",
        )
        if limitation_type in limitation_types
    )
    if severe_gap_count >= 2 or candidate_pod.finding is None:
        return "insufficient_public_data_for_pod"

    return "inferred_pod_from_public_data"


def _build_confidence_rationale(
    *,
    category: str,
    comparator_relevance_score: float | None,
    confidence_score: Decimal | None,
    limitations: Sequence[GeneratedLimitation],
) -> str:
    comparator_text = _comparator_label(comparator_relevance_score)
    confidence_text = (
        f"extraction confidence {float(confidence_score):.2f}"
        if confidence_score is not None
        else "no extraction confidence score"
    )
    limitation_titles = [limitation.title for limitation in limitations]

    if category == "explicit_pod_available":
        rationale = (
            f"Explicit POD wording is present, with {comparator_text} and {confidence_text}."
        )
    elif category == "inferred_pod_from_public_data":
        rationale = (
            f"The POD is inferred from public study details rather than named directly, with "
            f"{comparator_text} and {confidence_text}."
        )
    elif category == "analog_supported_provisional_pod":
        rationale = (
            f"The POD currently depends on analog or bridge evidence, with {comparator_text} "
            f"and {confidence_text}."
        )
    else:
        rationale = (
            f"There is not enough direct public evidence to support the POD, with "
            f"{comparator_text} and {confidence_text}."
        )

    if limitation_titles:
        rationale += f" Remaining gaps: {_human_join(limitation_titles)}."

    return rationale


def score_candidate_pod_support(
    *,
    study: Study | None,
    candidate_pod: CandidatePOD | None,
    limitations: Sequence[GeneratedLimitation],
    comparator_relevance_score: float | None = None,
) -> CandidatePODSupportResult:
    limitation_types = _limitation_types(limitations)
    category = _support_category(
        study=study,
        candidate_pod=candidate_pod,
        limitation_types=limitation_types,
    )
    confidence_score = (
        _normalize_confidence_score(candidate_pod.confidence_score)
        if candidate_pod is not None
        else None
    )
    blocking_count = sum(1 for limitation in limitations if limitation.is_blocking)
    non_blocking_count = len(limitations) - blocking_count

    score = POD_SCORE_BASELINES[category]
    if confidence_score is not None:
        score += float(confidence_score * Decimal("12"))

    if comparator_relevance_score is not None:
        if comparator_relevance_score >= 80:
            score += 10
        elif comparator_relevance_score >= 40:
            score += 5

    if category == "explicit_pod_available" and not limitations:
        score += 6
    elif category == "inferred_pod_from_public_data" and study is not None:
        score += 4

    score -= blocking_count * 12
    score -= non_blocking_count * 4
    support_score = round(max(0.0, min(100.0, score)), 2)

    expert_review_required = not (
        category == "explicit_pod_available"
        and blocking_count == 0
        and (comparator_relevance_score or 0.0) >= 80
        and (confidence_score is None or confidence_score >= Decimal("0.75"))
    )

    return CandidatePODSupportResult(
        support_category=category,
        support_score=support_score,
        confidence_rationale=_build_confidence_rationale(
            category=category,
            comparator_relevance_score=comparator_relevance_score,
            confidence_score=confidence_score,
            limitations=limitations,
        ),
        expert_review_required=expert_review_required,
    )


def generate_pod_recommendations(
    *,
    candidate_pod: CandidatePOD | None,
    support_result: CandidatePODSupportResult,
    limitations: Sequence[GeneratedLimitation],
    comparator_relevance_score: float | None = None,
) -> list[GeneratedRecommendation]:
    if candidate_pod is None:
        return []

    recommendations: list[GeneratedRecommendation] = []
    primary_limitation = next((item for item in limitations if item.is_blocking), None)
    if primary_limitation is None and limitations:
        primary_limitation = limitations[0]

    if support_result.support_category == "explicit_pod_available":
        if support_result.expert_review_required:
            recommendations.append(
                GeneratedRecommendation(
                    title="Close remaining gaps around the explicit POD",
                    rationale=(
                        f"The candidate POD is explicit, but {_comparator_label(comparator_relevance_score)} "
                        "or unresolved evidence gaps still justify follow-up before finalization."
                    ),
                    priority="medium",
                    linked_limitation_title=(
                        primary_limitation.title if primary_limitation is not None else None
                    ),
                    recommendation_status="suggested",
                )
            )
        return recommendations

    if support_result.support_category == "inferred_pod_from_public_data":
        recommendations.append(
            GeneratedRecommendation(
                title="Confirm the inferred POD with targeted follow-up evidence",
                rationale=(
                    f"The current POD is inferred rather than explicit, and {_comparator_label(comparator_relevance_score)} "
                    "means the public evidence should be anchored with a targeted confirmation step."
                ),
                priority="medium" if (comparator_relevance_score or 0.0) >= 40 else "high",
                linked_limitation_title=(
                    primary_limitation.title if primary_limitation is not None else None
                ),
                recommendation_status="suggested",
            )
        )
    elif support_result.support_category == "analog_supported_provisional_pod":
        recommendations.append(
            GeneratedRecommendation(
                title="Generate direct product-specific POD confirmation",
                rationale=(
                    "The current POD depends on analog or bridge evidence and should be backed by direct product-specific tox data before final use."
                ),
                priority="high",
                linked_limitation_title=(
                    next(
                        (
                            limitation.title
                            for limitation in limitations
                            if limitation.limitation_type == "analog_only_evidence"
                        ),
                        primary_limitation.title if primary_limitation is not None else None,
                    )
                ),
                recommendation_status="suggested",
            )
        )
    else:
        recommendations.append(
            GeneratedRecommendation(
                title="Build a foundational evidence package before selecting a POD",
                rationale=(
                    "The current evidence does not support a defendable public-data POD, so foundational route, species relevance, and dose context need to be established first."
                ),
                priority="high",
                linked_limitation_title=(
                    primary_limitation.title if primary_limitation is not None else None
                ),
                recommendation_status="suggested",
            )
        )

    if (comparator_relevance_score or 0.0) < 40:
        recommendations.append(
            GeneratedRecommendation(
                title="Identify a more relevant comparator or justify the bridge",
                rationale=(
                    "Comparator relevance is weak, so the report should either identify a closer analog or document why the current bridge is still appropriate."
                ),
                priority="high"
                if support_result.support_category
                in {"analog_supported_provisional_pod", "insufficient_public_data_for_pod"}
                else "medium",
                linked_limitation_title=(
                    primary_limitation.title if primary_limitation is not None else None
                ),
                recommendation_status="suggested",
            )
        )

    return recommendations
