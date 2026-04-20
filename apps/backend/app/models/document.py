from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import PrimaryKeyMixin, TimestampMixin


class SourceDocument(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "source_documents"
    __table_args__ = (
        UniqueConstraint("external_id", name="uq_source_documents_external_id"),
        Index("ix_source_documents_published_at", "published_at"),
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source_uri: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    document_chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="source_document",
        cascade="all, delete-orphan",
    )
    studies: Mapped[list["Study"]] = relationship(back_populates="source_document")


class DocumentChunk(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint(
            "source_document_id",
            "chunk_index",
            name="uq_document_chunks_source_document_chunk_index",
        ),
        Index("ix_document_chunks_source_document_id", "source_document_id"),
    )

    source_document_id: Mapped[int] = mapped_column(
        ForeignKey("source_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_number_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_number_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    source_document: Mapped["SourceDocument"] = relationship(
        back_populates="document_chunks"
    )
    citation_spans: Mapped[list["CitationSpan"]] = relationship(
        back_populates="document_chunk",
        cascade="all, delete-orphan",
    )


class CitationSpan(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "citation_spans"
    __table_args__ = (
        CheckConstraint("start_offset >= 0", name="ck_citation_spans_start_offset"),
        CheckConstraint(
            "end_offset > start_offset",
            name="ck_citation_spans_end_offset",
        ),
        Index("ix_citation_spans_finding_id", "finding_id"),
        Index("ix_citation_spans_document_chunk_id", "document_chunk_id"),
    )

    finding_id: Mapped[int] = mapped_column(
        ForeignKey("findings.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_chunk_id: Mapped[int] = mapped_column(
        ForeignKey("document_chunks.id", ondelete="CASCADE"),
        nullable=False,
    )
    start_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    end_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    quoted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    label: Mapped[str | None] = mapped_column(String(100), nullable=True)

    finding: Mapped["Finding"] = relationship(back_populates="citation_spans")
    document_chunk: Mapped["DocumentChunk"] = relationship(
        back_populates="citation_spans"
    )
