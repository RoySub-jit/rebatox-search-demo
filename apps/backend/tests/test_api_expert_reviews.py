from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from app.models.catalog import Product
from app.models.document import SourceDocument
from app.models.research import CandidatePOD, ExpertReview, Finding, Study


def _build_review_target(db_session):
    product = Product(
        name="Review Target",
        slug="review-target",
        manufacturer="Example Labs",
    )
    source_document = SourceDocument(
        title="Review Packet 12",
        document_type="assessment_report",
        source_uri="https://example.test/review-packet-12",
    )
    study = Study(
        product=product,
        source_document=source_document,
        title="Target study",
        objective="Document a direct oral POD.",
        study_design="Repeat-dose study",
        population="Adult patients with human relevance.",
        status="complete",
        published_at=datetime(2024, 7, 1, tzinfo=timezone.utc),
    )
    finding = Finding(
        study=study,
        title="Explicit oral POD",
        summary="The study documents an explicit oral NOAEL.",
        finding_type="supportive",
        evidence_direction="supportive",
        effect_estimate=Decimal("1.0"),
    )
    candidate_pod = CandidatePOD(
        product=product,
        finding=finding,
        title="Lead POD",
        claim_text="NOAEL of 5 mg/kg/day selected from the oral study.",
        rationale="Direct oral evidence is available for the product.",
        status="active",
        confidence_score=Decimal("0.90"),
    )

    db_session.add_all([product, source_document, study, finding, candidate_pod])
    db_session.commit()
    db_session.refresh(candidate_pod)

    return product, candidate_pod


def test_create_expert_review_persists_new_review(client, db_session):
    _, candidate_pod = _build_review_target(db_session)

    response = client.post(
        "/api/v1/expert-reviews",
        json={
            "candidate_pod_id": candidate_pod.id,
            "reviewer_name": "Dr. Nova Expert",
            "reviewer_email": "nova@example.test",
            "verdict": "approve",
            "score": 4.5,
            "accepted_current_assessment": True,
            "expert_review_required_resolved": True,
            "notes": "Direct evidence is sufficient for the current package.",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["candidate_pod_id"] == candidate_pod.id
    assert payload["finding_id"] == candidate_pod.finding_id
    assert payload["reviewer_name"] == "Dr. Nova Expert"
    assert payload["accepted_current_assessment"] is True
    assert payload["expert_review_required_resolved"] is True
    assert payload["override_support_category"] is None
    assert payload["override_support_score"] is None
    assert payload["notes"] == "Direct evidence is sufficient for the current package."
    assert payload["reviewed_at"]

    persisted = db_session.get(ExpertReview, payload["id"])
    assert persisted is not None
    assert persisted.candidate_pod_id == candidate_pod.id
    assert persisted.finding_id == candidate_pod.finding_id


def test_update_expert_review_updates_existing_review(client, db_session):
    _, candidate_pod = _build_review_target(db_session)
    review = ExpertReview(
        candidate_pod=candidate_pod,
        finding=candidate_pod.finding,
        reviewer_name="Dr. Nova Expert",
        verdict="revise",
        score=Decimal("3.0"),
        notes="Initial note.",
        reviewed_at=datetime(2024, 7, 2, tzinfo=timezone.utc),
    )
    db_session.add(review)
    db_session.commit()
    db_session.refresh(review)

    response = client.put(
        f"/api/v1/expert-reviews/{review.id}",
        json={
            "candidate_pod_id": candidate_pod.id,
            "reviewer_name": "Dr. Nova Expert",
            "reviewer_email": "nova@example.test",
            "verdict": "approve",
            "score": 4.8,
            "accepted_current_assessment": False,
            "expert_review_required_resolved": True,
            "override_support_category": "inferred_pod_from_public_data",
            "override_support_score": 67,
            "notes": "Updated after manual reconciliation.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == review.id
    assert payload["verdict"] == "approve"
    assert payload["score"] == 4.8
    assert payload["expert_review_required_resolved"] is True
    assert payload["override_support_category"] == "inferred_pod_from_public_data"
    assert payload["override_support_score"] == 67.0
    assert payload["notes"] == "Updated after manual reconciliation."

    db_session.refresh(review)
    assert float(review.override_support_score) == 67.0
    assert review.override_support_category == "inferred_pod_from_public_data"
    assert review.expert_review_required_resolved is True


def test_report_exposes_prior_expert_notes_in_review_section(client, db_session):
    product, candidate_pod = _build_review_target(db_session)
    older_review = ExpertReview(
        candidate_pod=candidate_pod,
        finding=candidate_pod.finding,
        reviewer_name="Dr. First Reviewer",
        verdict="revise",
        score=Decimal("3.5"),
        notes="Initial review requested a tighter bridge justification.",
        reviewed_at=datetime(2024, 7, 2, tzinfo=timezone.utc),
    )
    newer_review = ExpertReview(
        candidate_pod=candidate_pod,
        finding=candidate_pod.finding,
        reviewer_name="Dr. Second Reviewer",
        verdict="approve",
        score=Decimal("4.2"),
        accepted_current_assessment=True,
        expert_review_required_resolved=True,
        notes="Follow-up review accepted the current evidence package.",
        reviewed_at=datetime(2024, 7, 8, tzinfo=timezone.utc),
    )
    db_session.add_all([older_review, newer_review])
    db_session.commit()

    response = client.get(f"/api/v1/reports/{product.id}")

    assert response.status_code == 200
    items = response.json()["expert_review_section"]["items"]
    assert [item["reviewer_name"] for item in items] == [
        "Dr. Second Reviewer",
        "Dr. First Reviewer",
    ]
    assert items[0]["notes"] == "Follow-up review accepted the current evidence package."
    assert items[1]["notes"] == "Initial review requested a tighter bridge justification."
    assert items[0]["linked_candidate_pod_id"] == candidate_pod.id
    assert items[0]["accepted_current_assessment"] is True
    assert items[0]["expert_review_required_resolved"] is True


def test_report_reflects_expert_review_override_state_in_candidate_pod_assessment(
    client,
    db_session,
):
    product, candidate_pod = _build_review_target(db_session)
    review = ExpertReview(
        candidate_pod=candidate_pod,
        finding=candidate_pod.finding,
        reviewer_name="Dr. Override Expert",
        verdict="approve",
        score=Decimal("4.6"),
        expert_review_required_resolved=True,
        override_support_category="inferred_pod_from_public_data",
        override_support_score=Decimal("61.0"),
        notes="Treat the current package as inferred until the bridge is signed off.",
        reviewed_at=datetime(2024, 7, 9, tzinfo=timezone.utc),
    )
    db_session.add(review)
    db_session.commit()

    response = client.get(f"/api/v1/reports/{product.id}")

    assert response.status_code == 200
    assessment = response.json()["candidate_pod_assessment"]["items"][0]
    assert assessment["support_category"] == "inferred_pod_from_public_data"
    assert assessment["support_score"] == 61.0
    assert assessment["expert_review_required"] is False
    assert "Latest expert review update" in assessment["confidence_rationale"]
    assert "support score overridden to 61.0" in assessment["confidence_rationale"]
