from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ReportItemSource = Literal["persisted", "generated", "recommendation"]


class ReportCitation(BaseModel):
    source_document_id: int | None = None
    source_document_title: str
    citation_span_id: int | None = None
    label: str | None = None
    quoted_text: str | None = None
    chunk_index: int | None = None
    page_number_start: int | None = None
    page_number_end: int | None = None


class ProductOverviewSection(BaseModel):
    name: str
    slug: str
    manufacturer: str | None = None
    description: str | None = None
    study_count: int
    finding_count: int
    candidate_pod_count: int
    citations: list[ReportCitation] = Field(default_factory=list)


class ComparatorSummaryItem(BaseModel):
    comparator_id: int
    name: str
    category: str | None = None
    description: str | None = None
    relevance_score: float
    relevance_rationale: str
    linked_study_count: int
    linked_candidate_pod_count: int
    citations: list[ReportCitation] = Field(default_factory=list)


class ComparatorSummarySection(BaseModel):
    items: list[ComparatorSummaryItem] = Field(default_factory=list)
    citations: list[ReportCitation] = Field(default_factory=list)


class EvidenceStudyItem(BaseModel):
    study_id: int
    title: str
    study_design: str | None = None
    status: str | None = None
    source_document_title: str | None = None
    published_at: datetime | None = None
    citations: list[ReportCitation] = Field(default_factory=list)


class EvidenceFindingItem(BaseModel):
    finding_id: int
    study_id: int
    study_title: str
    title: str
    summary: str
    finding_type: str | None = None
    evidence_direction: str | None = None
    effect_estimate: float | None = None
    citations: list[ReportCitation] = Field(default_factory=list)


class EvidenceSummarySection(BaseModel):
    study_count: int
    finding_count: int
    studies: list[EvidenceStudyItem] = Field(default_factory=list)
    findings: list[EvidenceFindingItem] = Field(default_factory=list)
    citations: list[ReportCitation] = Field(default_factory=list)


class CandidatePODAssessmentItem(BaseModel):
    candidate_pod_id: int
    title: str
    claim_text: str
    rationale: str | None = None
    status: str
    confidence_score: float | None = None
    comparator_name: str | None = None
    linked_finding_title: str | None = None
    citations: list[ReportCitation] = Field(default_factory=list)


class CandidatePODAssessmentSection(BaseModel):
    items: list[CandidatePODAssessmentItem] = Field(default_factory=list)
    citations: list[ReportCitation] = Field(default_factory=list)


class ReportLimitationItem(BaseModel):
    source: ReportItemSource
    title: str
    description: str
    severity: str | None = None
    why_it_matters: str
    resolution_suggestion: str
    is_blocking: bool
    study_title: str | None = None
    finding_title: str | None = None
    candidate_pod_title: str | None = None
    citations: list[ReportCitation] = Field(default_factory=list)


class LimitationsSection(BaseModel):
    items: list[ReportLimitationItem] = Field(default_factory=list)
    citations: list[ReportCitation] = Field(default_factory=list)


class SuggestedExperimentItem(BaseModel):
    source: ReportItemSource
    title: str
    rationale: str
    priority: str | None = None
    linked_limitation_title: str | None = None
    recommendation_status: str | None = None
    citations: list[ReportCitation] = Field(default_factory=list)


class SuggestedNextExperimentsSection(BaseModel):
    items: list[SuggestedExperimentItem] = Field(default_factory=list)
    citations: list[ReportCitation] = Field(default_factory=list)


class ExpertReviewItem(BaseModel):
    expert_review_id: int
    reviewer_name: str
    reviewer_email: str | None = None
    verdict: str
    score: float | None = None
    notes: str | None = None
    reviewed_at: datetime | None = None
    linked_finding_title: str | None = None
    linked_candidate_pod_title: str | None = None
    citations: list[ReportCitation] = Field(default_factory=list)


class ExpertReviewSection(BaseModel):
    review_count: int
    average_score: float | None = None
    items: list[ExpertReviewItem] = Field(default_factory=list)
    citations: list[ReportCitation] = Field(default_factory=list)


class ProductReportRead(BaseModel):
    product_id: int
    generated_at: datetime
    product_overview: ProductOverviewSection
    comparator_summary: ComparatorSummarySection
    evidence_summary: EvidenceSummarySection
    candidate_pod_assessment: CandidatePODAssessmentSection
    limitations: LimitationsSection
    suggested_next_experiments: SuggestedNextExperimentsSection
    expert_review_section: ExpertReviewSection
