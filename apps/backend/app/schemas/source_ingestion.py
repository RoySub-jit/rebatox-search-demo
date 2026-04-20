from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

SourceProviderName = Literal["dailymed", "openfda", "pubmed"]


class SourceRecordIdentifier(BaseModel):
    namespace: str
    value: str


class SourceMetadataLookup(BaseModel):
    provider: SourceProviderName
    identifier: str


class NormalizedSourceMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: SourceProviderName
    external_id: str
    title: str
    document_type: str
    source_uri: str | None = None
    published_at: date | None = None
    summary: str | None = None
    journal: str | None = None
    authors: list[str] = Field(default_factory=list)
    organizations: list[str] = Field(default_factory=list)
    identifiers: list[SourceRecordIdentifier] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    raw_metadata: dict[str, Any] = Field(default_factory=dict)
