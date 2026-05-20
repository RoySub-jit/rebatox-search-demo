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


class LiveWorkspaceExtractedSignal(BaseModel):
    key: str
    label: str
    value: str
    source_section_key: str | None = None
    confidence: Literal["high", "medium", "low"] = "medium"


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
    extracted_signals: list[LiveWorkspaceExtractedSignal] = Field(default_factory=list)
    review_cue: LiveWorkspaceReviewCue
    retrieval_mode: Literal["live"] = "live"
    retrieved_at: datetime


class SaveLiveWorkspaceRequest(BaseModel):
    workspace: LiveWorkspaceResponse
    label: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=4000)


class SavedWorkspaceResponse(BaseModel):
    id: int
    label: str
    notes: str | None = None
    entity_type: EntityType
    provider: SourceProviderName
    external_id: str
    query: str | None = None
    saved_at: datetime
    workspace: LiveWorkspaceResponse


class SavedWorkspaceListItem(BaseModel):
    id: int
    label: str
    notes: str | None = None
    entity_type: EntityType
    provider: SourceProviderName
    external_id: str
    query: str | None = None
    saved_at: datetime
    record_title: str
    record_summary: str | None = None
    extracted_signal_count: int = 0
    section_count: int = 0


class SavedWorkspaceListResponse(BaseModel):
    total_results: int
    items: list[SavedWorkspaceListItem] = Field(default_factory=list)
