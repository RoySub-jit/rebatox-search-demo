from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from app.models.catalog import Comparator, Product
from app.models.document import CitationSpan, DocumentChunk, SourceDocument
from app.models.research import CandidatePOD, ExpertReview, Finding, Limitation, Recommendation, Study


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
    assert evidence_summary["citations"] == []

    candidate_assessment = payload["candidate_pod_assessment"]
    assert candidate_assessment["items"][0]["title"] == "Lead NOAEL candidate"
    assert isinstance(candidate_assessment["items"][0]["confidence_score"], float)
    assert candidate_assessment["items"][0]["confidence_score"] == 0.85
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

    assert comparator_item["name"] == "Reference Gamma"
    assert comparator_item["relevance_score"] == 5.0
    assert "weak comparator match" in comparator_item["relevance_rationale"]
    assert limitation_titles == {
        "Missing route",
        "Missing species relevance",
        "No explicit POD",
        "Sparse dose context",
        "Analog-only evidence",
        "Low extraction confidence",
    }


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
        "citations": [],
    }
    assert payload["limitations"] == {
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
