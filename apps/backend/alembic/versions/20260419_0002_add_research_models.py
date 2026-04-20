"""add research evidence models

Revision ID: 20260419_0002
Revises: 20260419_0001
Create Date: 2026-04-19 00:30:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260419_0002"
down_revision = "20260419_0001"
branch_labels = None
depends_on = None


def _timestamp_columns() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("manufacturer", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_products_slug"),
    )
    op.create_index("ix_products_name", "products", ["name"], unique=False)

    op.create_table(
        "comparators",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_comparators_slug"),
    )
    op.create_index("ix_comparators_name", "comparators", ["name"], unique=False)

    op.create_table(
        "source_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("document_type", sa.String(length=100), nullable=False),
        sa.Column("source_uri", sa.String(length=1024), nullable=True),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "external_id",
            name="uq_source_documents_external_id",
        ),
    )
    op.create_index(
        "ix_source_documents_published_at",
        "source_documents",
        ["published_at"],
        unique=False,
    )

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_document_id", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("page_number_start", sa.Integer(), nullable=True),
        sa.Column("page_number_end", sa.Integer(), nullable=True),
        sa.Column("char_count", sa.Integer(), nullable=True),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(
            ["source_document_id"],
            ["source_documents.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_document_id",
            "chunk_index",
            name="uq_document_chunks_source_document_chunk_index",
        ),
    )
    op.create_index(
        "ix_document_chunks_source_document_id",
        "document_chunks",
        ["source_document_id"],
        unique=False,
    )

    op.create_table(
        "studies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("comparator_id", sa.Integer(), nullable=True),
        sa.Column("source_document_id", sa.Integer(), nullable=True),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("objective", sa.Text(), nullable=True),
        sa.Column("study_design", sa.String(length=255), nullable=True),
        sa.Column("population", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=100), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(
            ["comparator_id"],
            ["comparators.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_document_id"],
            ["source_documents.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_id", name="uq_studies_external_id"),
    )
    op.create_index("ix_studies_product_id", "studies", ["product_id"], unique=False)
    op.create_index(
        "ix_studies_published_at",
        "studies",
        ["published_at"],
        unique=False,
    )

    op.create_table(
        "findings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("study_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("finding_type", sa.String(length=100), nullable=True),
        sa.Column("outcome_measure", sa.String(length=255), nullable=True),
        sa.Column("effect_estimate", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("evidence_direction", sa.String(length=50), nullable=True),
        sa.Column("statistical_significance", sa.String(length=100), nullable=True),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["study_id"], ["studies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_findings_study_id", "findings", ["study_id"], unique=False)
    op.create_index(
        "ix_findings_finding_type",
        "findings",
        ["finding_type"],
        unique=False,
    )

    op.create_table(
        "candidate_pods",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("comparator_id", sa.Integer(), nullable=True),
        sa.Column("finding_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=100), nullable=False),
        sa.Column("confidence_score", sa.Numeric(precision=5, scale=2), nullable=True),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(
            ["comparator_id"],
            ["comparators.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["finding_id"], ["findings.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_candidate_pods_product_id",
        "candidate_pods",
        ["product_id"],
        unique=False,
    )
    op.create_index(
        "ix_candidate_pods_status",
        "candidate_pods",
        ["status"],
        unique=False,
    )

    op.create_table(
        "citation_spans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("finding_id", sa.Integer(), nullable=False),
        sa.Column("document_chunk_id", sa.Integer(), nullable=False),
        sa.Column("start_offset", sa.Integer(), nullable=False),
        sa.Column("end_offset", sa.Integer(), nullable=False),
        sa.Column("quoted_text", sa.Text(), nullable=True),
        sa.Column("label", sa.String(length=100), nullable=True),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "start_offset >= 0",
            name="ck_citation_spans_start_offset",
        ),
        sa.CheckConstraint(
            "end_offset > start_offset",
            name="ck_citation_spans_end_offset",
        ),
        sa.ForeignKeyConstraint(
            ["document_chunk_id"],
            ["document_chunks.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["finding_id"], ["findings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_citation_spans_finding_id",
        "citation_spans",
        ["finding_id"],
        unique=False,
    )
    op.create_index(
        "ix_citation_spans_document_chunk_id",
        "citation_spans",
        ["document_chunk_id"],
        unique=False,
    )

    op.create_table(
        "limitations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("study_id", sa.Integer(), nullable=False),
        sa.Column("finding_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=True),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["finding_id"], ["findings.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["study_id"], ["studies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_limitations_study_id",
        "limitations",
        ["study_id"],
        unique=False,
    )
    op.create_index(
        "ix_limitations_finding_id",
        "limitations",
        ["finding_id"],
        unique=False,
    )

    op.create_table(
        "recommendations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("candidate_pod_id", sa.Integer(), nullable=True),
        sa.Column("study_id", sa.Integer(), nullable=True),
        sa.Column("finding_id", sa.Integer(), nullable=True),
        sa.Column("recommendation_type", sa.String(length=100), nullable=True),
        sa.Column("recommendation_text", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=100), nullable=True),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(
            ["candidate_pod_id"],
            ["candidate_pods.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["finding_id"], ["findings.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["study_id"], ["studies.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_recommendations_candidate_pod_id",
        "recommendations",
        ["candidate_pod_id"],
        unique=False,
    )
    op.create_index(
        "ix_recommendations_study_id",
        "recommendations",
        ["study_id"],
        unique=False,
    )
    op.create_index(
        "ix_recommendations_finding_id",
        "recommendations",
        ["finding_id"],
        unique=False,
    )

    op.create_table(
        "calculation_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("comparator_id", sa.Integer(), nullable=True),
        sa.Column("study_id", sa.Integer(), nullable=True),
        sa.Column("candidate_pod_id", sa.Integer(), nullable=True),
        sa.Column("run_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=100), nullable=False),
        sa.Column("parameters_json", sa.JSON(), nullable=True),
        sa.Column("result_json", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(
            ["candidate_pod_id"],
            ["candidate_pods.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["comparator_id"],
            ["comparators.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["study_id"], ["studies.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_calculation_runs_status",
        "calculation_runs",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_calculation_runs_candidate_pod_id",
        "calculation_runs",
        ["candidate_pod_id"],
        unique=False,
    )

    op.create_table(
        "expert_reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("candidate_pod_id", sa.Integer(), nullable=True),
        sa.Column("finding_id", sa.Integer(), nullable=True),
        sa.Column("calculation_run_id", sa.Integer(), nullable=True),
        sa.Column("reviewer_name", sa.String(length=255), nullable=False),
        sa.Column("reviewer_email", sa.String(length=320), nullable=True),
        sa.Column("verdict", sa.String(length=100), nullable=False),
        sa.Column("score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(
            ["calculation_run_id"],
            ["calculation_runs.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["candidate_pod_id"],
            ["candidate_pods.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["finding_id"], ["findings.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_expert_reviews_candidate_pod_id",
        "expert_reviews",
        ["candidate_pod_id"],
        unique=False,
    )
    op.create_index(
        "ix_expert_reviews_finding_id",
        "expert_reviews",
        ["finding_id"],
        unique=False,
    )
    op.create_index(
        "ix_expert_reviews_calculation_run_id",
        "expert_reviews",
        ["calculation_run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_expert_reviews_calculation_run_id", table_name="expert_reviews")
    op.drop_index("ix_expert_reviews_finding_id", table_name="expert_reviews")
    op.drop_index("ix_expert_reviews_candidate_pod_id", table_name="expert_reviews")
    op.drop_table("expert_reviews")

    op.drop_index("ix_calculation_runs_candidate_pod_id", table_name="calculation_runs")
    op.drop_index("ix_calculation_runs_status", table_name="calculation_runs")
    op.drop_table("calculation_runs")

    op.drop_index("ix_recommendations_finding_id", table_name="recommendations")
    op.drop_index("ix_recommendations_study_id", table_name="recommendations")
    op.drop_index("ix_recommendations_candidate_pod_id", table_name="recommendations")
    op.drop_table("recommendations")

    op.drop_index("ix_limitations_finding_id", table_name="limitations")
    op.drop_index("ix_limitations_study_id", table_name="limitations")
    op.drop_table("limitations")

    op.drop_index("ix_citation_spans_document_chunk_id", table_name="citation_spans")
    op.drop_index("ix_citation_spans_finding_id", table_name="citation_spans")
    op.drop_table("citation_spans")

    op.drop_index("ix_candidate_pods_status", table_name="candidate_pods")
    op.drop_index("ix_candidate_pods_product_id", table_name="candidate_pods")
    op.drop_table("candidate_pods")

    op.drop_index("ix_findings_finding_type", table_name="findings")
    op.drop_index("ix_findings_study_id", table_name="findings")
    op.drop_table("findings")

    op.drop_index("ix_studies_published_at", table_name="studies")
    op.drop_index("ix_studies_product_id", table_name="studies")
    op.drop_table("studies")

    op.drop_index(
        "ix_document_chunks_source_document_id",
        table_name="document_chunks",
    )
    op.drop_table("document_chunks")

    op.drop_index(
        "ix_source_documents_published_at",
        table_name="source_documents",
    )
    op.drop_table("source_documents")

    op.drop_index("ix_comparators_name", table_name="comparators")
    op.drop_table("comparators")

    op.drop_index("ix_products_name", table_name="products")
    op.drop_table("products")
