from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

LimitationType = Literal[
    "missing_route",
    "missing_species_relevance",
    "no_explicit_pod",
    "sparse_dose_context",
    "low_confidence_extraction",
    "analog_only_evidence",
]
LimitationSeverity = Literal["low", "medium", "high"]


class GeneratedLimitation(BaseModel):
    limitation_type: LimitationType
    description: str
    severity: LimitationSeverity
    why_it_matters: str
    resolution_suggestion: str
    is_blocking: bool
