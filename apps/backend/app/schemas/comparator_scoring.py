from __future__ import annotations

from pydantic import BaseModel


class ComparatorScoringInput(BaseModel):
    comparator_name: str | None = None
    same_target: bool = False
    same_modality: bool = False
    same_route: bool = False
    same_indication: bool = False
    same_scaffold: bool = False


class ComparatorScoringResult(BaseModel):
    comparator_name: str | None = None
    relevance_score: float
    rationale: str
