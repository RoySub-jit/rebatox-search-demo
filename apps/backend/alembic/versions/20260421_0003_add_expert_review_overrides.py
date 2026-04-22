"""add expert review override fields

Revision ID: 20260421_0003
Revises: 20260419_0002
Create Date: 2026-04-21 09:30:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260421_0003"
down_revision = "20260419_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "expert_reviews",
        sa.Column(
            "accepted_current_assessment",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "expert_reviews",
        sa.Column(
            "expert_review_required_resolved",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "expert_reviews",
        sa.Column(
            "override_support_category",
            sa.String(length=100),
            nullable=True,
        ),
    )
    op.add_column(
        "expert_reviews",
        sa.Column(
            "override_support_score",
            sa.Numeric(precision=5, scale=2),
            nullable=True,
        ),
    )

    op.alter_column(
        "expert_reviews",
        "accepted_current_assessment",
        server_default=None,
    )
    op.alter_column(
        "expert_reviews",
        "expert_review_required_resolved",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("expert_reviews", "override_support_score")
    op.drop_column("expert_reviews", "override_support_category")
    op.drop_column("expert_reviews", "expert_review_required_resolved")
    op.drop_column("expert_reviews", "accepted_current_assessment")
