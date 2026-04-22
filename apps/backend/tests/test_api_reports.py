from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from app.models.catalog import Comparator, Product
from app.models.document import CitationSpan, DocumentChunk, SourceDocument
from app.models.research import (
    CalculationRun,
    CandidatePOD,
    ExpertReview,
    Finding,
    Limitation,
    Recommendation,
    Study,
)


def _build_seeded_report_data(db_session):
    product = Product(
        name="Cardiovex XR",
        slug="cardiovex-xr",
        manufacturer="Example Labs",
        description="Extended-release safety assessment candidate.",
    )
    comparator = Comparator(
        name="Legacy IR comparator",
        slug="legacy-ir-comparator",
        category="active_control",
        description="Immediate-release comparator used in adherence framing.",
    )
    source_document = SourceDocument(
        title="CSR CVX-301",
        document_type="clinical_study_report",
        source_uri="https://example.test/cvx-301",
    )
    chunk_content = (
        "Patients received oral dosing for 12 weeks. "
        "Systemic exposure remained within the maintenance band and supported the NOAEL selection."
    )
    document_chunk = DocumentChunk(
        source_document=source_document,
        chunk_index=0,
        content=chunk_content,
        page_number_start=21,
        page_number_end=22,
    )
    study = Study(
        product=product,
        comparator=comparator,
        source_document=source_document,
        title="CVX-301 maintenance study",
        objective="Evaluate oral maintenance dosing and exposure stability.",
        study_design="Randomized clinical trial",
        population="Adult patients",
        status="complete",
        published_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
    )
    finding = Finding(
        study=study,
        title="Exposure stability",
        summary="Systemic exposure remained stable during the maintenance period.",
        finding_type="safety",
        evidence_direction="supportive",
        effect_estimate=Decimal("0.85"),
    )
    quoted_text = (
        "Systemic exposure remained within the maintenance band and supported the NOAEL selection."
    )
    start_offset = chunk_content.index("Systemic exposure")
    end_offset = start_offset + len(quoted_text)
    citation_span = CitationSpan(
        finding=finding,
        document_chunk=document_chunk,
        start_offset=start_offset,
        end_offset=end_offset,
        quoted_text=quoted_text,
        label="exposure_support",
    )
    candidate_pod = CandidatePOD(
        product=product,
        comparator=comparator,
        finding=finding,
        title="Lead NOAEL candidate",
        claim_text="NOAEL of 5 mg/kg/day retained for the current report.",
        rationale="Oral route, clinical exposure context, and quantitative screening all align.",
        status="active",
        confidence_score=Decimal("0.85"),
    )
    limitation = Limitation(
        study=study,
        finding=finding,
        description="Duration bridge remains limited for long-term extrapolation.",
        severity="medium",
    )
    recommendation = Recommendation(
        candidate_pod=candidate_pod,
        study=study,
        finding=finding,
        recommendation_type="next_experiment",
        recommendation_text="Run a longer-duration oral bridging study to extend the maintenance exposure narrative.",
        priority="high",
        status="open",
    )
    expert_review = ExpertReview(
        candidate_pod=candidate_pod,
        finding=finding,
        reviewer_name="Dr. Ada Review",
        reviewer_email="ada@example.test",
        verdict="revise",
        score=Decimal("4.0"),
        notes="Needs longer-duration confirmation before final recommendation freeze.",
        reviewed_at=datetime(2024, 3, 1, tzinfo=timezone.utc),
    )

    db_session.add_all(
        [
            product,
            comparator,
            source_document,
            document_chunk,
            study,
            finding,
            citation_span,
            candidate_pod,
            limitation,
            recommendation,
            expert_review,
        ]
    )
    db_session.commit()
    db_session.refresh(product)

    return product


def _build_partial_report_data_without_optional_sections(db_session):
    product = Product(
        name="Sparse Signals",
        slug="sparse-signals",
        manufacturer="Example Labs",
    )
    source_document = SourceDocument(
        title="Briefing Note 202",
        document_type="internal_summary",
        source_uri="https://example.test/briefing-note-202",
    )
    chunk_content = "Adult patients received oral dosing for 14 days with stable observation notes."
    document_chunk = DocumentChunk(
        source_document=source_document,
        chunk_index=0,
        content=chunk_content,
        page_number_start=4,
        page_number_end=4,
    )
    study = Study(
        product=product,
        source_document=source_document,
        title="Signal confirmation study",
        objective="Confirm the maintenance exposure narrative.",
        study_design="Open-label clinical study",
        population="Adult patients",
        status="complete",
        published_at=datetime(2024, 2, 20, tzinfo=timezone.utc),
    )
    finding = Finding(
        study=study,
        title="Stable exposure window",
        summary="Exposure remained stable across the observation period.",
        finding_type="supportive",
        evidence_direction="supportive",
        effect_estimate=Decimal("1.25"),
    )
    quoted_text = "Adult patients received oral dosing for 14 days with stable observation notes."
    citation_span = CitationSpan(
        finding=finding,
        document_chunk=document_chunk,
        start_offset=0,
        end_offset=len(quoted_text),
        quoted_text=quoted_text,
        label="study_summary",
    )

    db_session.add_all(
        [
            product,
            source_document,
            document_chunk,
            study,
            finding,
            citation_span,
        ]
    )
    db_session.commit()
    db_session.refresh(product)

    return product


def _build_bare_product(db_session):
    product = Product(
        name="Bare Product",
        slug="bare-product",
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


def _build_strong_comparator_report_data(db_session):
    product = Product(
        name="Biologic Prime",
        slug="biologic-prime",
        manufacturer="Example Labs",
    )
    comparator = Comparator(
        name="Reference Alpha",
        slug="reference-alpha",
        category="same_target same_modality",
        description=(
            "same_route same_indication same_scaffold comparator with strong biologic alignment."
        ),
    )
    source_document = SourceDocument(
        title="Comparator Dossier 11",
        document_type="assessment_report",
        source_uri="https://example.test/comparator-dossier-11",
    )
    chunk_text = (
        "Adult patients received oral dosing for 28 days, and the NOAEL of 5 mg/kg/day "
        "was retained with documented human relevance."
    )
    document_chunk = DocumentChunk(
        source_document=source_document,
        chunk_index=0,
        content=chunk_text,
        page_number_start=8,
        page_number_end=8,
    )
    study = Study(
        product=product,
        comparator=comparator,
        source_document=source_document,
        title="Reference alignment study",
        objective=(
            "Evaluate oral dosing and confirm a NOAEL across 5 mg/kg/day and 15 mg/kg/day groups."
        ),
        study_design="Repeat-dose clinical study",
        population="Adult patients with documented human relevance.",
        status="complete",
        published_at=datetime(2024, 5, 10, tzinfo=timezone.utc),
    )
    finding = Finding(
        study=study,
        title="Reference alignment",
        summary="Comparator-aligned exposure supports the selected NOAEL.",
        finding_type="supportive",
        evidence_direction="supportive",
        effect_estimate=Decimal("1.10"),
    )
    citation_span = CitationSpan(
        finding=finding,
        document_chunk=document_chunk,
        start_offset=0,
        end_offset=len(chunk_text),
        quoted_text=chunk_text,
        label="comparator_alignment",
    )
    candidate_pod = CandidatePOD(
        product=product,
        comparator=comparator,
        finding=finding,
        title="Reference NOAEL candidate",
        claim_text="NOAEL of 5 mg/kg/day selected from the oral study.",
        rationale="Human relevance is documented and the oral route is aligned for review.",
        status="confirmed",
        confidence_score=Decimal("0.93"),
    )

    db_session.add_all(
        [
            product,
            comparator,
            source_document,
            document_chunk,
            study,
            finding,
            citation_span,
            candidate_pod,
        ]
    )
    db_session.commit()
    db_session.refresh(product)

    return product


def _build_weak_comparator_report_data(db_session):
    product = Product(
        name="Bridge Candidate",
        slug="bridge-candidate",
        manufacturer="Example Labs",
    )
    comparator = Comparator(
        name="Reference Gamma",
        slug="reference-gamma",
        category="bridge_reference",
        description="same_scaffold comparator with limited bridge support.",
    )
    source_document = SourceDocument(
        title="Bridge Memo 7",
        document_type="assessment_report",
        source_uri="https://example.test/bridge-memo-7",
    )
    chunk_text = (
        "Rat bridge study summary relying on read-across support from an analog compound."
    )
    document_chunk = DocumentChunk(
        source_document=source_document,
        chunk_index=0,
        content=chunk_text,
        page_number_start=2,
        page_number_end=2,
    )
    study = Study(
        product=product,
        comparator=comparator,
        source_document=source_document,
        title="Bridge toxicology assessment",
        objective="Summarize support from a rat bridge study.",
        study_design="Toxicology bridge study",
        population="Rat model",
        status="complete",
        published_at=datetime(2024, 6, 12, tzinfo=timezone.utc),
    )
    finding = Finding(
        study=study,
        title="Bridge-only support",
        summary="Current support depends on analog bridge evidence.",
        finding_type="supportive",
        evidence_direction="uncertain",
        effect_estimate=Decimal("0.40"),
    )
    citation_span = CitationSpan(
        finding=finding,
        document_chunk=document_chunk,
        start_offset=0,
        end_offset=len(chunk_text),
        quoted_text=chunk_text,
        label="bridge_support",
    )
    candidate_pod = CandidatePOD(
        product=product,
        comparator=comparator,
        finding=finding,
        title="Bridge support candidate",
        claim_text="Selected from the bridge study findings.",
        rationale="Read-across from an analog compound supports the current selection.",
        status="provisional",
        confidence_score=Decimal("0.25"),
    )

    db_session.add_all(
        [
            product,
            comparator,
            source_document,
            document_chunk,
            study,
            finding,
            citation_span,
            candidate_pod,
        ]
    )
    db_session.commit()
    db_session.refresh(product)

    return product


def _add_calculation_run(
    db_session,
    *,
    product: Product,
    run_type: str,
    status: str,
    parameters_json: dict,
    result_json: dict,
):
    calculation_run = CalculationRun(
        product=product,
        study=product.studies[0] if product.studies else None,
        candidate_pod=product.candidate_pods[0] if product.candidate_pods else None,
        run_type=run_type,
        status=status,
        parameters_json=parameters_json,
        result_json=result_json,
        started_at=datetime(2024, 4, 1, 12, 0, tzinfo=timezone.utc),
        completed_at=datetime(2024, 4, 1, 12, 0, tzinfo=timezone.utc),
    )
    db_session.add(calculation_run)
    db_session.commit()
    db_session.refresh(product)

    return calculation_run


def test_get_product_report_returns_structured_sections_with_citations(client, db_session):
    product = _build_seeded_report_data(db_session)

    response = client.get(f"/api/v1/reports/{product.id}")

    assert response.status_code == 200

    payload = response.json()
    assert payload["product_id"] == product.id
    assert payload["generated_at"]

    product_overview = payload["product_overview"]
    assert product_overview["name"] == "Cardiovex XR"
    assert product_overview["study_count"] == 1
    assert product_overview["finding_count"] == 1
    assert product_overview["candidate_pod_count"] == 1
    assert product_overview["citations"][0]["source_document_title"] == "CSR CVX-301"

    comparator_summary = payload["comparator_summary"]
    assert len(comparator_summary["items"]) == 1
    assert comparator_summary["items"][0]["name"] == "Legacy IR comparator"
    assert comparator_summary["items"][0]["linked_study_count"] == 1
    assert comparator_summary["citations"] == []

    evidence_summary = payload["evidence_summary"]
    assert evidence_summary["study_count"] == 1
    assert evidence_summary["finding_count"] == 1
    assert evidence_summary["studies"][0]["title"] == "CVX-301 maintenance study"
    assert evidence_summary["findings"][0]["title"] == "Exposure stability"
    assert isinstance(evidence_summary["findings"][0]["effect_estimate"], float)
    assert evidence_summary["findings"][0]["effect_estimate"] == 0.85
    assert evidence_summary["findings"][0]["citations"][0]["quoted_text"] == (
        "Systemic exposure remained within the maintenance band and supported the NOAEL selection."
    )
    assert "finding_id" not in evidence_summary["findings"][0]["citations"][0]
    assert evidence_summary["calculations"] == []
    assert evidence_summary["citations"] == []

    candidate_assessment = payload["candidate_pod_assessment"]
    assert candidate_assessment["items"][0]["title"] == "Lead NOAEL candidate"
    assert isinstance(candidate_assessment["items"][0]["confidence_score"], float)
    assert candidate_assessment["items"][0]["confidence_score"] == 0.85
    assert candidate_assessment["items"][0]["support_category"] == "explicit_pod_available"
    assert candidate_assessment["items"][0]["support_score"] == 88.2
    assert candidate_assessment["items"][0]["expert_review_required"] is True
    assert "weak comparator relevance" in candidate_assessment["items"][0]["confidence_rationale"]
    assert candidate_assessment["citations"] == []

    limitations = payload["limitations"]
    assert limitations["items"][0]["description"] == (
        "Duration bridge remains limited for long-term extrapolation."
    )
    assert limitations["items"][0]["citations"]
    assert limitations["citations"] == []

    suggested_next_experiments = payload["suggested_next_experiments"]
    assert suggested_next_experiments["items"][0]["source"] == "recommendation"
    assert suggested_next_experiments["items"][0]["priority"] == "high"
    assert suggested_next_experiments["items"][1]["title"] == (
        "Close remaining gaps around the explicit POD"
    )
    assert suggested_next_experiments["items"][1]["recommendation_status"] == "suggested"
    assert suggested_next_experiments["citations"] == []

    expert_review_section = payload["expert_review_section"]
    assert expert_review_section["review_count"] == 1
    assert isinstance(expert_review_section["average_score"], float)
    assert expert_review_section["average_score"] == 4.0
    assert expert_review_section["items"][0]["reviewer_name"] == "Dr. Ada Review"
    assert isinstance(expert_review_section["items"][0]["score"], float)
    assert expert_review_section["items"][0]["score"] == 4.0
    assert expert_review_section["items"][0]["citations"]
    assert expert_review_section["citations"] == []


def test_get_product_report_returns_empty_section_shapes_for_missing_optional_report_data(
    client,
    db_session,
):
    product = _build_partial_report_data_without_optional_sections(db_session)

    response = client.get(f"/api/v1/reports/{product.id}")

    assert response.status_code == 200

    payload = response.json()
    assert payload["product_id"] == product.id

    assert payload["comparator_summary"] == {
        "items": [],
        "citations": [],
    }
    assert payload["candidate_pod_assessment"] == {
        "items": [],
        "citations": [],
    }
    assert payload["limitations"] == {
        "items": [],
        "citations": [],
    }
    assert payload["expert_review_section"] == {
        "review_count": 0,
        "average_score": None,
        "items": [],
        "citations": [],
    }


def test_get_product_report_includes_valid_calculation_summary(client, db_session):
    product = _build_seeded_report_data(db_session)
    _add_calculation_run(
        db_session,
        product=product,
        run_type="margin_of_exposure",
        status="ok",
        parameters_json={
            "point_of_departure": "100",
            "exposure": "2",
            "basis": "mg/kg/day",
        },
        result_json={
            "calculator": "margin_of_exposure",
            "formula": "MOE = POD / Exposure",
            "inputs": {
                "point_of_departure": "100",
                "exposure": "2",
                "basis": "mg/kg/day",
            },
            "assumptions": [
                "Point of departure and exposure share the same dose basis.",
            ],
            "result": {
                "value": "50.0",
                "unit": "ratio",
            },
            "warnings": [],
            "status": "ok",
        },
    )

    response = client.get(f"/api/v1/reports/{product.id}")

    assert response.status_code == 200

    calculation = response.json()["evidence_summary"]["calculations"][0]
    assert calculation["calculation_type"] == "margin_of_exposure"
    assert calculation["status"] == "ok"
    assert calculation["formula_version"] == "1.0"
    assert calculation["inputs"] == {
        "point_of_departure": "100",
        "exposure": "2",
        "basis": "mg/kg/day",
    }
    assert calculation["outputs"] == {
        "value": "50.0",
        "unit": "ratio",
    }
    assert calculation["assumptions"] == [
        "Point of departure and exposure share the same dose basis."
    ]
    assert calculation["warnings"] == []
    assert calculation["citations"][0]["source_document_title"] == "CSR CVX-301"


def test_get_product_report_includes_warning_status_calculation_summary(client, db_session):
    product = _build_seeded_report_data(db_session)
    _add_calculation_run(
        db_session,
        product=product,
        run_type="ade",
        status="warning",
        parameters_json={
            "point_of_departure_mg_per_kg_day": "0.6",
            "body_weight_kg": "50",
            "modifying_factor_f1": "1",
            "modifying_factor_f2": "1",
            "modifying_factor_f3": "1",
            "modifying_factor_f4": "1",
            "modifying_factor_f5": "1",
            "point_of_departure_label": "POD",
            "result_unit": "mg/day",
        },
        result_json={
            "calculator": "ade_calculator_shell",
            "formula": "ADE = POD x body_weight / composite_modifying_factor",
            "formula_version": "2026.04",
            "inputs": {
                "point_of_departure_mg_per_kg_day": "0.6",
                "body_weight_kg": "50",
            },
            "assumptions": [
                "All modifying factors default to 1 unless specified otherwise.",
            ],
            "result": {
                "value": "30.0",
                "unit": "mg/day",
                "composite_modifying_factor": "1",
            },
            "warnings": [
                "All modifying factors are 1, so no uncertainty adjustment has been applied."
            ],
            "status": "warning",
        },
    )

    response = client.get(f"/api/v1/reports/{product.id}")

    assert response.status_code == 200

    calculation = response.json()["evidence_summary"]["calculations"][0]
    assert calculation["calculation_type"] == "ade"
    assert calculation["status"] == "warning"
    assert calculation["formula_version"] == "2026.04"
    assert calculation["warnings"] == [
        "All modifying factors are 1, so no uncertainty adjustment has been applied."
    ]
    assert calculation["outputs"]["value"] == "30.0"


def test_get_product_report_returns_empty_calculation_summaries_when_none_are_linked(
    client,
    db_session,
):
    product = _build_partial_report_data_without_optional_sections(db_session)

    response = client.get(f"/api/v1/reports/{product.id}")

    assert response.status_code == 200
    assert response.json()["evidence_summary"]["calculations"] == []


def test_get_product_report_integrates_strong_comparator_and_no_limitations(
    client,
    db_session,
):
    product = _build_strong_comparator_report_data(db_session)

    response = client.get(f"/api/v1/reports/{product.id}")

    assert response.status_code == 200

    payload = response.json()
    comparator_item = payload["comparator_summary"]["items"][0]

    assert comparator_item["name"] == "Reference Alpha"
    assert comparator_item["relevance_score"] == 100.0
    assert "strong comparator match" in comparator_item["relevance_rationale"]
    assert payload["candidate_pod_assessment"]["items"][0]["support_category"] == (
        "explicit_pod_available"
    )
    assert payload["candidate_pod_assessment"]["items"][0]["support_score"] == 99.16
    assert payload["candidate_pod_assessment"]["items"][0]["expert_review_required"] is False
    assert payload["limitations"] == {
        "items": [],
        "citations": [],
    }


def test_get_product_report_integrates_weak_comparator_and_multiple_limitations(
    client,
    db_session,
):
    product = _build_weak_comparator_report_data(db_session)

    response = client.get(f"/api/v1/reports/{product.id}")

    assert response.status_code == 200

    payload = response.json()
    comparator_item = payload["comparator_summary"]["items"][0]
    limitation_titles = {item["title"] for item in payload["limitations"]["items"]}
    recommendation_titles = {
        item["title"] for item in payload["suggested_next_experiments"]["items"]
    }

    assert comparator_item["name"] == "Reference Gamma"
    assert comparator_item["relevance_score"] == 5.0
    assert "weak comparator match" in comparator_item["relevance_rationale"]
    assert payload["candidate_pod_assessment"]["items"][0]["support_category"] == (
        "analog_supported_provisional_pod"
    )
    assert payload["candidate_pod_assessment"]["items"][0]["support_score"] == 0.0
    assert payload["candidate_pod_assessment"]["items"][0]["expert_review_required"] is True
    assert limitation_titles == {
        "Missing route",
        "Missing species relevance",
        "No explicit POD",
        "Sparse dose context",
        "Analog-only evidence",
        "Low extraction confidence",
    }
    assert "Generate direct product-specific POD confirmation" in recommendation_titles
    assert "Identify a more relevant comparator or justify the bridge" in recommendation_titles


def test_get_product_report_handles_no_comparator_and_no_study_data(
    client,
    db_session,
):
    product = _build_bare_product(db_session)

    response = client.get(f"/api/v1/reports/{product.id}")

    assert response.status_code == 200

    payload = response.json()
    assert payload["product_id"] == product.id
    assert payload["product_overview"]["study_count"] == 0
    assert payload["comparator_summary"] == {
        "items": [],
        "citations": [],
    }
    assert payload["evidence_summary"] == {
        "study_count": 0,
        "finding_count": 0,
        "studies": [],
        "findings": [],
        "calculations": [],
        "citations": [],
    }
    assert payload["limitations"] == {
        "items": [],
        "citations": [],
    }
    assert payload["candidate_pod_assessment"] == {
        "items": [],
        "citations": [],
    }
    assert payload["suggested_next_experiments"] == {
        "items": [],
        "citations": [],
    }


def test_get_product_report_returns_not_found_for_missing_product(client):
    response = client.get("/api/v1/reports/999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "code": "product_not_found",
            "message": "Product with id 999 was not found.",
        }
    }
