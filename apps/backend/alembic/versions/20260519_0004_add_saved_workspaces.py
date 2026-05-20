"""add saved workspaces

Revision ID: 20260519_0004
Revises: 20260421_0003
Create Date: 2026-05-19 20:35:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260519_0004"
down_revision = "20260421_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "saved_workspaces",
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("query", sa.Text(), nullable=True),
        sa.Column("snapshot_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_saved_workspaces_entity_type",
        "saved_workspaces",
        ["entity_type"],
        unique=False,
    )
    op.create_index(
        "ix_saved_workspaces_provider",
        "saved_workspaces",
        ["provider"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_saved_workspaces_provider", table_name="saved_workspaces")
    op.drop_index("ix_saved_workspaces_entity_type", table_name="saved_workspaces")
    op.drop_table("saved_workspaces")
