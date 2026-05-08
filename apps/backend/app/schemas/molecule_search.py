from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from app.schemas.source_ingestion import SourceProviderName, SourceRecordIdentifier


class MoleculeSearchResult(BaseModel):
    provider: SourceProviderName
    external_id: str
    title: str
    generic_name: str | None = None
    brand_names: list[str] = Field(default_factory=list)
    manufacturer_names: list[str] = Field(default_factory=list)
    routes: list[str] = Field(default_factory=list)
    substance_names: list[str] = Field(default_factory=list)
    product_type: str | None = None
    published_at: date | None = None
    summary: str | None = None
    source_uri: str | None = None
    identifiers: list[SourceRecordIdentifier] = Field(default_factory=list)


class MoleculeSearchResponse(BaseModel):
    query: str
    limit: int
    total_results: int
    items: list[MoleculeSearchResult] = Field(default_factory=list)


class MoleculeLabelSection(BaseModel):
    key: str
    title: str
    content: list[str] = Field(default_factory=list)


class MoleculeDetailResponse(BaseModel):
    molecule: MoleculeSearchResult
    sections: list[MoleculeLabelSection] = Field(default_factory=list)
