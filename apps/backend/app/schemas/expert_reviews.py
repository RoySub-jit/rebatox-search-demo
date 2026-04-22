from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.research import ExpertReview
from app.schemas.pod_support import PODSupportCategory


class ExpertReviewWrite(BaseModel):
    candidate_pod_id: int
    calculation_run_id: int | None = None
    reviewer_name: str = Field(min_length=1, max_length=255)
    reviewer_email: str | None = Field(default=None, max_length=320)
    verdict: str = Field(min_length=1, max_length=100)
    score: float | None = Field(default=None, ge=0, le=5)
    accepted_current_assessment: bool = False
    expert_review_required_resolved: bool = False
    override_support_category: PODSupportCategory | None = None
    override_support_score: float | None = Field(default=None, ge=0, le=100)
    notes: str | None = None
    reviewed_at: datetime | None = None

    @model_validator(mode="after")
    def validate_override_consistency(self) -> "ExpertReviewWrite":
        if self.accepted_current_assessment and (
            self.override_support_category is not None
            or self.override_support_score is not None
        ):
            raise ValueError(
                "Accepted assessments cannot also set override support values."
            )

        return self


class ExpertReviewCreate(ExpertReviewWrite):
    pass


class ExpertReviewUpdate(ExpertReviewWrite):
    pass


class ExpertReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_pod_id: int | None = None
    finding_id: int | None = None
    calculation_run_id: int | None = None
    reviewer_name: str
    reviewer_email: str | None = None
    verdict: str
    score: float | None = None
    accepted_current_assessment: bool
    expert_review_required_resolved: bool
    override_support_category: PODSupportCategory | None = None
    override_support_score: float | None = None
    notes: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, review: ExpertReview) -> "ExpertReviewRead":
        return cls.model_validate(review)
