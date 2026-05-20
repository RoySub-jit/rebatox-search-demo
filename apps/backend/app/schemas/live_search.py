from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.source_ingestion import SourceProviderName, SourceRecordIdentifier

EntityType = Literal["molecule", "degradant", "el"]


class LiveSearchResult(BaseModel):
    entity_type: EntityType
    provider: SourceProviderName
    external_id: str
    title: str
    subtitle: str | None = None
    summary: str | None = None
    document_type: str | None = None
    published_at: date | None = None
    source_uri: str | None = None
    identifiers: list[SourceRecordIdentifier] = Field(default_factory=list)
    generic_name: str | None = None
    brand_names: list[str] = Field(default_factory=list)
    manufacturer_names: list[str] = Field(default_factory=list)
    routes: list[str] = Field(default_factory=list)
    substance_names: list[str] = Field(default_factory=list)
    product_type: str | None = None
    authors: list[str] = Field(default_factory=list)
    journal: str | None = None
    keywords: list[str] = Field(default_factory=list)


class LiveSearchResponse(BaseModel):
    entity_type: EntityType
    query: str
    sources: list[SourceProviderName] = Field(default_factory=list)
    limit: int
    total_results: int
    items: list[LiveSearchResult] = Field(default_factory=list)


class LiveWorkspaceSection(BaseModel):
    key: str
    title: str
    content: list[str] = Field(default_factory=list)


class LiveWorkspaceReviewCue(BaseModel):
    title: str
    description: str


class ResolveLiveWorkspaceRequest(BaseModel):
    entity_type: EntityType
    provider: SourceProviderName
    external_id: str = Field(min_length=1, max_length=200)
    query: str | None = Field(default=None, max_length=200)


class LiveWorkspaceResponse(BaseModel):
    entity_type: EntityType
    query: str | None = None
    record: LiveSearchResult
    sections: list[LiveWorkspaceSection] = Field(default_factory=list)
    review_cue: LiveWorkspaceReviewCue
    retrieval_mode: Literal["live"] = "live"
    retrieved_at: datetime
