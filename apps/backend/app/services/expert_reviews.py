from __future__ import annotations

from datetime import datetime, timezone

from fastapi import status
from sqlalchemy.orm import Session

from app.api.errors import raise_api_error
from app.models.research import CalculationRun, CandidatePOD, ExpertReview
from app.schemas.expert_reviews import ExpertReviewCreate, ExpertReviewUpdate


def _get_candidate_pod(*, db: Session, candidate_pod_id: int) -> CandidatePOD:
    candidate_pod = db.get(CandidatePOD, candidate_pod_id)
    if candidate_pod is None:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="candidate_pod_not_found",
            message=f"Candidate POD with id {candidate_pod_id} was not found.",
        )

    return candidate_pod


def _get_calculation_run(
    *,
    db: Session,
    calculation_run_id: int | None,
) -> CalculationRun | None:
    if calculation_run_id is None:
        return None

    calculation_run = db.get(CalculationRun, calculation_run_id)
    if calculation_run is None:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="calculation_run_not_found",
            message=f"Calculation run with id {calculation_run_id} was not found.",
        )

    return calculation_run


def _validated_relationships(
    *,
    db: Session,
    candidate_pod_id: int,
    calculation_run_id: int | None,
) -> tuple[CandidatePOD, CalculationRun | None]:
    candidate_pod = _get_candidate_pod(db=db, candidate_pod_id=candidate_pod_id)
    calculation_run = _get_calculation_run(
        db=db,
        calculation_run_id=calculation_run_id,
    )

    if (
        calculation_run is not None
        and calculation_run.candidate_pod_id is not None
        and calculation_run.candidate_pod_id != candidate_pod.id
    ):
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="expert_review_link_mismatch",
            message=(
                "Calculation run does not belong to the supplied candidate POD."
            ),
        )

    return candidate_pod, calculation_run


def _apply_payload(
    *,
    review: ExpertReview,
    payload: ExpertReviewCreate | ExpertReviewUpdate,
    candidate_pod: CandidatePOD,
    calculation_run: CalculationRun | None,
) -> None:
    review.candidate_pod_id = candidate_pod.id
    review.finding_id = candidate_pod.finding_id
    review.calculation_run_id = calculation_run.id if calculation_run is not None else None
    review.reviewer_name = payload.reviewer_name.strip()
    review.reviewer_email = payload.reviewer_email.strip() if payload.reviewer_email else None
    review.verdict = payload.verdict.strip()
    review.score = payload.score
    review.accepted_current_assessment = payload.accepted_current_assessment
    review.expert_review_required_resolved = payload.expert_review_required_resolved
    review.override_support_category = payload.override_support_category
    review.override_support_score = payload.override_support_score
    review.notes = payload.notes.strip() if payload.notes else None
    review.reviewed_at = payload.reviewed_at or datetime.now(timezone.utc)


def create_expert_review(*, db: Session, payload: ExpertReviewCreate) -> ExpertReview:
    candidate_pod, calculation_run = _validated_relationships(
        db=db,
        candidate_pod_id=payload.candidate_pod_id,
        calculation_run_id=payload.calculation_run_id,
    )

    review = ExpertReview()
    _apply_payload(
        review=review,
        payload=payload,
        candidate_pod=candidate_pod,
        calculation_run=calculation_run,
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    return review


def update_expert_review(
    *,
    db: Session,
    expert_review_id: int,
    payload: ExpertReviewUpdate,
) -> ExpertReview:
    review = db.get(ExpertReview, expert_review_id)
    if review is None:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="expert_review_not_found",
            message=f"Expert review with id {expert_review_id} was not found.",
        )

    candidate_pod, calculation_run = _validated_relationships(
        db=db,
        candidate_pod_id=payload.candidate_pod_id,
        calculation_run_id=payload.calculation_run_id,
    )
    _apply_payload(
        review=review,
        payload=payload,
        candidate_pod=candidate_pod,
        calculation_run=calculation_run,
    )
    db.commit()
    db.refresh(review)

    return review
