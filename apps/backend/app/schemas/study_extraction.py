from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ExtractionMethod = Literal["rule_based", "llm_reconciled"]
ReconciliationStatus = Literal["skipped", "completed"]


class ExtractionCitationSpan(BaseModel):
    document_chunk_id: int | None = None
    chunk_index: int
    start_offset: int
    end_offset: int
    quoted_text: str
    page_number_start: int | None = None
    page_number_end: int | None = None
    label: str | None = None


class ExtractedStudyField(BaseModel):
    value: str
    citations: list[ExtractionCitationSpan] = Field(default_factory=list)
    extraction_method: ExtractionMethod = "rule_based"


class StudyDetailExtractionResult(BaseModel):
    species: ExtractedStudyField | None = None
    route: ExtractedStudyField | None = None
    duration: ExtractedStudyField | None = None
    dose_text: ExtractedStudyField | None = None
    exposure_text: ExtractedStudyField | None = None
    study_type: ExtractedStudyField | None = None
    explicit_pod_mentions: list[ExtractedStudyField] = Field(default_factory=list)
    reconciliation_status: ReconciliationStatus = "skipped"
    notes: list[str] = Field(default_factory=list)
