from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.errors import ErrorResponse
from app.schemas.expert_reviews import (
    ExpertReviewCreate,
    ExpertReviewRead,
    ExpertReviewUpdate,
)
from app.services.expert_reviews import create_expert_review, update_expert_review

router = APIRouter(prefix="/expert-reviews", tags=["expert-reviews"])


@router.post(
    "",
    response_model=ExpertReviewRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    },
)
def create_expert_review_route(
    payload: ExpertReviewCreate,
    db: Session = Depends(get_db),
) -> ExpertReviewRead:
    review = create_expert_review(db=db, payload=payload)
    return ExpertReviewRead.from_model(review)


@router.put(
    "/{expert_review_id}",
    response_model=ExpertReviewRead,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    },
)
def update_expert_review_route(
    expert_review_id: int,
    payload: ExpertReviewUpdate,
    db: Session = Depends(get_db),
) -> ExpertReviewRead:
    review = update_expert_review(
        db=db,
        expert_review_id=expert_review_id,
        payload=payload,
    )
    return ExpertReviewRead.from_model(review)
