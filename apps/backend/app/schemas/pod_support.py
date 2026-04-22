from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

PODSupportCategory = Literal[
    "explicit_pod_available",
    "inferred_pod_from_public_data",
    "analog_supported_provisional_pod",
    "insufficient_public_data_for_pod",
]


class CandidatePODSupportResult(BaseModel):
    support_category: PODSupportCategory
    support_score: float
    confidence_rationale: str
    expert_review_required: bool


class GeneratedRecommendation(BaseModel):
    title: str
    rationale: str
    priority: str
    linked_limitation_title: str | None = None
    recommendation_status: str
