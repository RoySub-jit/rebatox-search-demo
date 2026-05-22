from __future__ import annotations

from app.schemas.live_search import (
    LiveSearchResult,
    LiveWorkspaceExtractedSignal,
    LiveWorkspacePodWorksheet,
    LiveWorkspaceSection,
)
from app.services.live_search.pod_analysis import build_pod_analysis, build_pod_worksheet


def test_build_pod_analysis_normalizes_microgram_per_kg_day_candidates() -> None:
    record = LiveSearchResult(
        entity_type="degradant",
        provider="pubmed",
        external_id="pm-1",
        title="NDMA toxicology note",
    )
    sections = [
        LiveWorkspaceSection(
            key="abstract",
            title="Abstract",
            content=[
                "Sprague-Dawley rats received oral NDMA 250 µg/kg/day for 28 days. NOAEL was established at 250 µg/kg/day.",
            ],
        )
    ]

    analysis = build_pod_analysis(
        record=record,
        sections=sections,
        extracted_signals=[],
    )

    assert analysis.primary_candidate is not None
    assert analysis.primary_candidate.pod_term == "NOAEL"
    assert analysis.primary_candidate.species == "rat"
    assert analysis.primary_candidate.route == "oral"
    assert analysis.primary_candidate.duration == "28 days"
    assert analysis.primary_candidate.normalized_mg_per_kg_day == 0.25
    assert analysis.primary_candidate.normalization_note == "Converted from µg/kg/day to mg/kg/day."
    assert any(
        item.label == "Normalized screening basis" and item.result_text == "0.25 mg/kg/day"
        for item in analysis.derived_calculations
    )
    assert any(
        item.label == "Screening human equivalent dose"
        for item in analysis.derived_calculations
    )


def test_build_pod_analysis_normalizes_human_mg_per_day_candidates() -> None:
    record = LiveSearchResult(
        entity_type="molecule",
        provider="pubmed",
        external_id="pm-2",
        title="Clinical dose note",
    )
    sections = [
        LiveWorkspaceSection(
            key="abstract",
            title="Abstract",
            content=[
                "Healthy volunteers received oral study drug 100 mg/day for 14 days, with systemic exposure monitored throughout the trial.",
            ],
        )
    ]

    analysis = build_pod_analysis(
        record=record,
        sections=sections,
        extracted_signals=[
            LiveWorkspaceExtractedSignal(
                key="study_model",
                label="Study model",
                value="Human / clinical",
            )
        ],
    )

    assert analysis.primary_candidate is not None
    assert analysis.primary_candidate.species == "human"
    assert analysis.primary_candidate.normalized_mg_per_kg_day == 2.0
    assert analysis.primary_candidate.normalization_note == (
        "Converted from mg/day to mg/kg/day using a 50 kg screening body weight."
    )
    assert any(
        item.label == "50 kg screening conversion" and item.result_text == "100 mg/day"
        for item in analysis.derived_calculations
    )
    assert any(
        "did not include explicit POD language" in warning
        for warning in analysis.warnings
    )


def test_build_pod_analysis_supports_bw_style_units_and_noaec_terms() -> None:
    record = LiveSearchResult(
        entity_type="degradant",
        provider="pubmed",
        external_id="pm-3",
        title="Impurity inhalation note",
    )
    sections = [
        LiveWorkspaceSection(
            key="abstract",
            title="Abstract",
            content=[
                "Wistar rats received inhalation exposure at a NOAEC of 25 mg/kg bw/day for 13 weeks in the subchronic study.",
            ],
        )
    ]

    analysis = build_pod_analysis(
        record=record,
        sections=sections,
        extracted_signals=[],
    )

    assert analysis.primary_candidate is not None
    assert analysis.primary_candidate.pod_term == "NOAEC"
    assert analysis.primary_candidate.species == "rat"
    assert analysis.primary_candidate.route == "inhalation"
    assert analysis.primary_candidate.duration == "13 weeks"
    assert analysis.primary_candidate.normalized_mg_per_kg_day == 25.0
    assert analysis.primary_candidate.normalization_note == "Direct mg/kg/day basis from the source text."


def test_build_pod_worksheet_supports_reviewer_entered_manual_basis() -> None:
    record = LiveSearchResult(
        entity_type="el",
        provider="pubmed",
        external_id="pm-4",
        title="Extractables review note",
    )
    analysis = build_pod_analysis(
        record=record,
        sections=[
            LiveWorkspaceSection(
                key="abstract",
                title="Abstract",
                content=[
                    "This review discusses extractables and leachables risk assessment strategy without giving a numeric POD in the abstract.",
                ],
            )
        ],
        extracted_signals=[],
    )

    worksheet = build_pod_worksheet(
        pod_analysis=analysis,
        current_worksheet=LiveWorkspacePodWorksheet(
            manual_basis_label="Reviewer-entered TTC screening basis",
            manual_basis_mg_per_kg_day=0.03,
            body_weight_kg=60.0,
            uncertainty_factor=10.0,
        ),
    )

    assert worksheet.selected_candidate is None
    assert worksheet.manual_basis_label == "Reviewer-entered TTC screening basis"
    assert worksheet.manual_basis_mg_per_kg_day == 0.03
    assert worksheet.selected_basis_label == "Reviewer-entered TTC screening basis"
    assert worksheet.selected_basis_mg_per_kg_day == 0.03
    assert worksheet.screening_intake_mg_day == 1.7999999999999998
    assert worksheet.uf_adjusted_intake_mg_day == 0.18
    assert any(
        "reviewer-entered screening basis" in warning.lower()
        for warning in worksheet.warnings
    )
