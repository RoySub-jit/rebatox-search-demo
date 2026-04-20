from __future__ import annotations

from decimal import Decimal

from app.models.research import CandidatePOD, Study
from app.services.limitations import generate_rule_based_limitations


def build_study(**overrides) -> Study:
    payload = {
        "product_id": 1,
        "title": "Oral rat repeat-dose toxicology study",
        "objective": (
            "Evaluate oral dosing and identify a NOAEL across 5 mg/kg/day and 15 mg/kg/day cohorts."
        ),
        "study_design": "Repeat-dose toxicology study",
        "population": "Rat model with documented human relevance for safety extrapolation.",
        "status": "complete",
    }
    payload.update(overrides)
    return Study(**payload)


def build_candidate_pod(**overrides) -> CandidatePOD:
    payload = {
        "product_id": 1,
        "title": "NOAEL POD candidate",
        "claim_text": (
            "Point of departure NOAEL of 5 mg/kg/day selected from the oral rat study."
        ),
        "rationale": (
            "Species relevance to humans is documented and the extracted POD is ready for review."
        ),
        "status": "confirmed",
        "confidence_score": Decimal("0.92"),
    }
    payload.update(overrides)
    return CandidatePOD(**payload)


def limitation_types(study: Study, candidate_pod: CandidatePOD) -> set[str]:
    return {
        limitation.limitation_type
        for limitation in generate_rule_based_limitations(
            study=study,
            candidate_pod=candidate_pod,
        )
    }


def test_generator_returns_no_limitations_for_well_supported_candidate_pod():
    study = build_study()
    candidate_pod = build_candidate_pod()

    limitations = generate_rule_based_limitations(
        study=study,
        candidate_pod=candidate_pod,
    )

    assert limitations == []


def test_generator_returns_empty_list_for_missing_study_or_candidate_pod():
    study = build_study()
    candidate_pod = build_candidate_pod()

    assert generate_rule_based_limitations(study=None, candidate_pod=candidate_pod) == []
    assert generate_rule_based_limitations(study=study, candidate_pod=None) == []
    assert generate_rule_based_limitations(study=None, candidate_pod=None) == []


def test_generator_flags_missing_route():
    study = build_study(
        title="Rat repeat-dose toxicology study",
        objective="Identify a NOAEL across 5 mg/kg/day and 15 mg/kg/day cohorts.",
    )
    candidate_pod = build_candidate_pod(
        claim_text="Point of departure NOAEL of 5 mg/kg/day selected from the rat study.",
    )

    assert limitation_types(study, candidate_pod) == {"missing_route"}


def test_generator_flags_missing_species_relevance():
    study = build_study(
        title="Oral repeat-dose toxicology study",
        population=None,
    )
    candidate_pod = build_candidate_pod(
        rationale="The extracted POD is ready for review.",
    )

    limitations = generate_rule_based_limitations(
        study=study,
        candidate_pod=candidate_pod,
    )

    assert [limitation.limitation_type for limitation in limitations] == [
        "missing_species_relevance"
    ]
    assert limitations[0].title == "Missing species relevance"
    assert limitations[0].severity == "high"
    assert limitations[0].is_blocking is True


def test_generator_flags_missing_explicit_pod():
    study = build_study()
    candidate_pod = build_candidate_pod(
        title="Lead safety candidate",
        claim_text="Selected from the oral rat study at 5 mg/kg/day.",
        rationale="Species relevance to humans is documented and ready for review.",
    )

    limitations = generate_rule_based_limitations(
        study=study,
        candidate_pod=candidate_pod,
    )

    assert [limitation.limitation_type for limitation in limitations] == [
        "no_explicit_pod"
    ]
    assert limitations[0].title == "No explicit POD"


def test_generator_flags_sparse_dose_context():
    study = build_study(
        objective="Evaluate oral dosing in a rat model with human relevance.",
    )
    candidate_pod = build_candidate_pod(
        claim_text="Point of departure NOAEL selected from the oral rat study.",
    )

    limitations = generate_rule_based_limitations(
        study=study,
        candidate_pod=candidate_pod,
    )

    assert [limitation.limitation_type for limitation in limitations] == [
        "sparse_dose_context"
    ]
    assert limitations[0].is_blocking is True


def test_generator_flags_low_confidence_extraction_from_score():
    study = build_study()
    candidate_pod = build_candidate_pod(confidence_score=Decimal("0.42"))

    limitations = generate_rule_based_limitations(
        study=study,
        candidate_pod=candidate_pod,
    )

    assert [limitation.limitation_type for limitation in limitations] == [
        "low_confidence_extraction"
    ]
    assert limitations[0].severity == "medium"
    assert limitations[0].is_blocking is False


def test_generator_flags_analog_only_evidence():
    study = build_study(
        title="Oral bridge assessment in rat model",
    )
    candidate_pod = build_candidate_pod(
        rationale=(
            "Read-across from an analog compound provides the current bridge justification with documented human relevance."
        ),
    )

    limitations = generate_rule_based_limitations(
        study=study,
        candidate_pod=candidate_pod,
    )

    assert [limitation.limitation_type for limitation in limitations] == [
        "analog_only_evidence"
    ]
    assert limitations[0].title == "Analog-only evidence"


def test_generator_escalates_very_low_confidence_to_blocking():
    study = build_study()
    candidate_pod = build_candidate_pod(confidence_score=Decimal("25"))

    limitations = generate_rule_based_limitations(
        study=study,
        candidate_pod=candidate_pod,
    )

    assert [limitation.limitation_type for limitation in limitations] == [
        "low_confidence_extraction"
    ]
    assert limitations[0].title == "Low extraction confidence"
    assert limitations[0].severity == "high"
    assert limitations[0].is_blocking is True


def test_generator_can_return_multiple_simultaneous_limitations():
    study = build_study(
        title="Bridge toxicology assessment",
        objective="Summarize support from a rat bridge study.",
        study_design="Toxicology bridge study",
        population="Rat model",
    )
    candidate_pod = build_candidate_pod(
        title="Lead bridge candidate",
        claim_text="Selected from the bridge study findings.",
        rationale="Read-across from an analog compound supports the current selection.",
        confidence_score=Decimal("0.25"),
    )

    limitations = generate_rule_based_limitations(
        study=study,
        candidate_pod=candidate_pod,
    )

    assert {limitation.limitation_type for limitation in limitations} == {
        "missing_route",
        "missing_species_relevance",
        "no_explicit_pod",
        "sparse_dose_context",
        "analog_only_evidence",
        "low_confidence_extraction",
    }
    assert {limitation.title for limitation in limitations} == {
        "Missing route",
        "Missing species relevance",
        "No explicit POD",
        "Sparse dose context",
        "Analog-only evidence",
        "Low extraction confidence",
    }
    assert all(limitation.description for limitation in limitations)
    assert all(limitation.why_it_matters for limitation in limitations)
    assert all(limitation.resolution_suggestion for limitation in limitations)
