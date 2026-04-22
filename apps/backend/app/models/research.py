from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import PrimaryKeyMixin, TimestampMixin


class Study(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "studies"
    __table_args__ = (
        UniqueConstraint("external_id", name="uq_studies_external_id"),
        Index("ix_studies_product_id", "product_id"),
        Index("ix_studies_published_at", "published_at"),
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    comparator_id: Mapped[int | None] = mapped_column(
        ForeignKey("comparators.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_document_id: Mapped[int | None] = mapped_column(
        ForeignKey("source_documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    study_design: Mapped[str | None] = mapped_column(String(255), nullable=True)
    population: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    product: Mapped["Product"] = relationship(back_populates="studies")
    comparator: Mapped["Comparator | None"] = relationship(back_populates="studies")
    source_document: Mapped["SourceDocument | None"] = relationship(
        back_populates="studies"
    )
    findings: Mapped[list["Finding"]] = relationship(
        back_populates="study",
        cascade="all, delete-orphan",
    )
    limitations: Mapped[list["Limitation"]] = relationship(
        back_populates="study",
        cascade="all, delete-orphan",
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="study"
    )
    calculation_runs: Mapped[list["CalculationRun"]] = relationship(
        back_populates="study"
    )


class Finding(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "findings"
    __table_args__ = (
        Index("ix_findings_study_id", "study_id"),
        Index("ix_findings_finding_type", "finding_type"),
    )

    study_id: Mapped[int] = mapped_column(
        ForeignKey("studies.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    finding_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    outcome_measure: Mapped[str | None] = mapped_column(String(255), nullable=True)
    effect_estimate: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 4),
        nullable=True,
    )
    evidence_direction: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    statistical_significance: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    study: Mapped["Study"] = relationship(back_populates="findings")
    citation_spans: Mapped[list["CitationSpan"]] = relationship(
        back_populates="finding",
        cascade="all, delete-orphan",
    )
    candidate_pods: Mapped[list["CandidatePOD"]] = relationship(
        back_populates="finding"
    )
    limitations: Mapped[list["Limitation"]] = relationship(back_populates="finding")
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="finding"
    )
    expert_reviews: Mapped[list["ExpertReview"]] = relationship(
        back_populates="finding"
    )


class CandidatePOD(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "candidate_pods"
    __table_args__ = (
        Index("ix_candidate_pods_product_id", "product_id"),
        Index("ix_candidate_pods_status", "status"),
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    comparator_id: Mapped[int | None] = mapped_column(
        ForeignKey("comparators.id", ondelete="SET NULL"),
        nullable=True,
    )
    finding_id: Mapped[int | None] = mapped_column(
        ForeignKey("findings.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(100), nullable=False, default="draft")
    confidence_score: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    product: Mapped["Product"] = relationship(back_populates="candidate_pods")
    comparator: Mapped["Comparator | None"] = relationship(
        back_populates="candidate_pods"
    )
    finding: Mapped["Finding | None"] = relationship(back_populates="candidate_pods")
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="candidate_pod"
    )
    calculation_runs: Mapped[list["CalculationRun"]] = relationship(
        back_populates="candidate_pod"
    )
    expert_reviews: Mapped[list["ExpertReview"]] = relationship(
        back_populates="candidate_pod"
    )


class Limitation(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "limitations"
    __table_args__ = (
        Index("ix_limitations_study_id", "study_id"),
        Index("ix_limitations_finding_id", "finding_id"),
    )

    study_id: Mapped[int] = mapped_column(
        ForeignKey("studies.id", ondelete="CASCADE"),
        nullable=False,
    )
    finding_id: Mapped[int | None] = mapped_column(
        ForeignKey("findings.id", ondelete="SET NULL"),
        nullable=True,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str | None] = mapped_column(String(50), nullable=True)

    study: Mapped["Study"] = relationship(back_populates="limitations")
    finding: Mapped["Finding | None"] = relationship(back_populates="limitations")


class Recommendation(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "recommendations"
    __table_args__ = (
        Index("ix_recommendations_candidate_pod_id", "candidate_pod_id"),
        Index("ix_recommendations_study_id", "study_id"),
        Index("ix_recommendations_finding_id", "finding_id"),
    )

    candidate_pod_id: Mapped[int | None] = mapped_column(
        ForeignKey("candidate_pods.id", ondelete="SET NULL"),
        nullable=True,
    )
    study_id: Mapped[int | None] = mapped_column(
        ForeignKey("studies.id", ondelete="SET NULL"),
        nullable=True,
    )
    finding_id: Mapped[int | None] = mapped_column(
        ForeignKey("findings.id", ondelete="SET NULL"),
        nullable=True,
    )
    recommendation_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    recommendation_text: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str | None] = mapped_column(String(100), nullable=True)

    candidate_pod: Mapped["CandidatePOD | None"] = relationship(
        back_populates="recommendations"
    )
    study: Mapped["Study | None"] = relationship(back_populates="recommendations")
    finding: Mapped["Finding | None"] = relationship(back_populates="recommendations")


class CalculationRun(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "calculation_runs"
    __table_args__ = (
        Index("ix_calculation_runs_status", "status"),
        Index("ix_calculation_runs_candidate_pod_id", "candidate_pod_id"),
    )

    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
    )
    comparator_id: Mapped[int | None] = mapped_column(
        ForeignKey("comparators.id", ondelete="SET NULL"),
        nullable=True,
    )
    study_id: Mapped[int | None] = mapped_column(
        ForeignKey("studies.id", ondelete="SET NULL"),
        nullable=True,
    )
    candidate_pod_id: Mapped[int | None] = mapped_column(
        ForeignKey("candidate_pods.id", ondelete="SET NULL"),
        nullable=True,
    )
    run_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="pending",
    )
    parameters_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    product: Mapped["Product | None"] = relationship(back_populates="calculation_runs")
    comparator: Mapped["Comparator | None"] = relationship(
        back_populates="calculation_runs"
    )
    study: Mapped["Study | None"] = relationship(back_populates="calculation_runs")
    candidate_pod: Mapped["CandidatePOD | None"] = relationship(
        back_populates="calculation_runs"
    )
    expert_reviews: Mapped[list["ExpertReview"]] = relationship(
        back_populates="calculation_run"
    )


class ExpertReview(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "expert_reviews"
    __table_args__ = (
        Index("ix_expert_reviews_candidate_pod_id", "candidate_pod_id"),
        Index("ix_expert_reviews_finding_id", "finding_id"),
        Index("ix_expert_reviews_calculation_run_id", "calculation_run_id"),
    )

    candidate_pod_id: Mapped[int | None] = mapped_column(
        ForeignKey("candidate_pods.id", ondelete="SET NULL"),
        nullable=True,
    )
    finding_id: Mapped[int | None] = mapped_column(
        ForeignKey("findings.id", ondelete="SET NULL"),
        nullable=True,
    )
    calculation_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("calculation_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    reviewer_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    verdict: Mapped[str] = mapped_column(String(100), nullable=False)
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    accepted_current_assessment: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    expert_review_required_resolved: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    override_support_category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    override_support_score: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    candidate_pod: Mapped["CandidatePOD | None"] = relationship(
        back_populates="expert_reviews"
    )
    finding: Mapped["Finding | None"] = relationship(back_populates="expert_reviews")
    calculation_run: Mapped["CalculationRun | None"] = relationship(
        back_populates="expert_reviews"
    )
