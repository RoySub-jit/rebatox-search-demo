from __future__ import annotations

from decimal import Decimal

from app.models.research import CandidatePOD, Finding, Study
from app.schemas.limitations import GeneratedLimitation
from app.services.pod_support import (
    generate_pod_recommendations,
    score_candidate_pod_support,
)


def build_study(**overrides) -> Study:
    payload = {
        "product_id": 1,
        "title": "Oral repeat-dose tox study",
        "objective": "Evaluate oral dosing across 5 mg/kg/day and 15 mg/kg/day groups.",
        "study_design": "Repeat-dose tox study",
        "population": "Adult patients with documented human relevance.",
        "status": "complete",
    }
    payload.update(overrides)
    return Study(**payload)


def build_finding(study: Study, **overrides) -> Finding:
    payload = {
        "study": study,
        "title": "Lead POD finding",
        "summary": "The NOAEL remained stable across the studied dose range.",
        "finding_type": "supportive",
        "evidence_direction": "supportive",
    }
    payload.update(overrides)
    return Finding(**payload)


def build_candidate_pod(finding: Finding | None, **overrides) -> CandidatePOD:
    payload = {
        "product_id": 1,
        "finding": finding,
        "title": "Lead NOAEL candidate",
        "claim_text": "NOAEL of 5 mg/kg/day selected from the oral study.",
        "rationale": "Human relevance is documented and ready for review.",
        "status": "confirmed",
        "confidence_score": Decimal("0.90"),
    }
    payload.update(overrides)
    return CandidatePOD(**payload)


def limitation(
    limitation_type: str,
    *,
    title: str,
    is_blocking: bool,
    severity: str = "medium",
) -> GeneratedLimitation:
    return GeneratedLimitation(
        limitation_type=limitation_type,  # type: ignore[arg-type]
        title=title,
        description=f"{title} description.",
        severity=severity,  # type: ignore[arg-type]
        why_it_matters=f"{title} matters.",
        resolution_suggestion=f"Resolve {title.lower()}.",
        is_blocking=is_blocking,
    )


def test_scores_explicit_pod_with_strong_direct_support():
    study = build_study()
    finding = build_finding(study)
    candidate_pod = build_candidate_pod(finding)

    result = score_candidate_pod_support(
        study=study,
        candidate_pod=candidate_pod,
        limitations=[],
        comparator_relevance_score=100.0,
    )

    assert result.support_category == "explicit_pod_available"
    assert result.support_score == 98.8
    assert result.expert_review_required is False
    assert "Explicit POD wording is present" in result.confidence_rationale


def test_scores_inferred_pod_with_moderate_support():
    study = build_study()
    finding = build_finding(study)
    candidate_pod = build_candidate_pod(
        finding,
        title="Lead safety candidate",
        claim_text="Selected from the oral study at 5 mg/kg/day.",
    )
    limitations = [
        limitation("no_explicit_pod", title="No explicit POD", is_blocking=True, severity="high")
    ]

    result = score_candidate_pod_support(
        study=study,
        candidate_pod=candidate_pod,
        limitations=limitations,
        comparator_relevance_score=55.0,
    )

    assert result.support_category == "inferred_pod_from_public_data"
    assert result.support_score == 62.8
    assert result.expert_review_required is True
    assert "inferred from public study details" in result.confidence_rationale


def test_scores_analog_only_pod_context_as_provisional():
    study = build_study()
    finding = build_finding(study)
    candidate_pod = build_candidate_pod(
        finding,
        rationale="Read-across from an analog compound provides the current bridge justification.",
        confidence_score=Decimal("0.25"),
    )
    limitations = [
        limitation(
            "analog_only_evidence",
            title="Analog-only evidence",
            is_blocking=False,
            severity="high",
        )
    ]

    result = score_candidate_pod_support(
        study=study,
        candidate_pod=candidate_pod,
        limitations=limitations,
        comparator_relevance_score=5.0,
    )

    assert result.support_category == "analog_supported_provisional_pod"
    assert result.support_score == 31.0
    assert result.expert_review_required is True
    assert "depends on analog or bridge evidence" in result.confidence_rationale


def test_scores_insufficient_data_pod_case():
    result = score_candidate_pod_support(
        study=None,
        candidate_pod=None,
        limitations=[],
        comparator_relevance_score=None,
    )

    assert result.support_category == "insufficient_public_data_for_pod"
    assert result.support_score == 12.0
    assert result.expert_review_required is True
    assert "not enough direct public evidence" in result.confidence_rationale


def test_generates_recommendations_from_multiple_limitations():
    study = build_study(population="Rat model")
    finding = build_finding(study, evidence_direction="uncertain")
    candidate_pod = build_candidate_pod(
        finding,
        title="Bridge support candidate",
        claim_text="Selected from the bridge study findings.",
        rationale="Read-across from an analog compound supports the current selection.",
        confidence_score=Decimal("0.25"),
    )
    limitations = [
        limitation(
            "analog_only_evidence",
            title="Analog-only evidence",
            is_blocking=False,
            severity="high",
        ),
        limitation(
            "missing_species_relevance",
            title="Missing species relevance",
            is_blocking=True,
            severity="high",
        ),
    ]
    support_result = score_candidate_pod_support(
        study=study,
        candidate_pod=candidate_pod,
        limitations=limitations,
        comparator_relevance_score=5.0,
    )

    recommendations = generate_pod_recommendations(
        candidate_pod=candidate_pod,
        support_result=support_result,
        limitations=limitations,
        comparator_relevance_score=5.0,
    )

    assert [item.title for item in recommendations] == [
        "Generate direct product-specific POD confirmation",
        "Identify a more relevant comparator or justify the bridge",
    ]
    assert all(item.recommendation_status == "suggested" for item in recommendations)
    assert recommendations[0].linked_limitation_title == "Analog-only evidence"
    assert recommendations[1].linked_limitation_title == "Missing species relevance"
