from __future__ import annotations

from sqlalchemy import Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import PrimaryKeyMixin, TimestampMixin


class Product(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_products_slug"),
        Index("ix_products_name", "name"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    studies: Mapped[list["Study"]] = relationship(back_populates="product")
    candidate_pods: Mapped[list["CandidatePOD"]] = relationship(
        back_populates="product"
    )
    calculation_runs: Mapped[list["CalculationRun"]] = relationship(
        back_populates="product"
    )


class Comparator(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "comparators"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_comparators_slug"),
        Index("ix_comparators_name", "name"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    studies: Mapped[list["Study"]] = relationship(back_populates="comparator")
    candidate_pods: Mapped[list["CandidatePOD"]] = relationship(
        back_populates="comparator"
    )
    calculation_runs: Mapped[list["CalculationRun"]] = relationship(
        back_populates="comparator"
    )
