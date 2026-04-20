from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.schemas.source_ingestion import NormalizedSourceMetadata, SourceProviderName
from app.services.source_ingestion.base import SourceMetadataProvider
from app.services.source_ingestion.dailymed import DailyMedMetadataProvider
from app.services.source_ingestion.openfda import OpenFDAMetadataProvider
from app.services.source_ingestion.pubmed import PubMedMetadataProvider

DEFAULT_PROVIDERS: dict[SourceProviderName, SourceMetadataProvider] = {
    "dailymed": DailyMedMetadataProvider(),
    "openfda": OpenFDAMetadataProvider(),
    "pubmed": PubMedMetadataProvider(),
}


class SourceIngestionService:
    def __init__(
        self,
        providers: Mapping[SourceProviderName, SourceMetadataProvider] | None = None,
    ) -> None:
        self._providers = dict(providers or DEFAULT_PROVIDERS)

    def get_provider(self, provider: SourceProviderName) -> SourceMetadataProvider:
        try:
            return self._providers[provider]
        except KeyError as exc:
            raise ValueError(f"Unsupported source provider: {provider}.") from exc

    def fetch_metadata(
        self,
        *,
        provider: SourceProviderName,
        identifier: str,
    ) -> dict[str, Any]:
        return self.get_provider(provider).fetch_metadata(identifier=identifier)

    def parse_metadata(
        self,
        *,
        provider: SourceProviderName,
        payload: Mapping[str, Any],
    ) -> NormalizedSourceMetadata:
        return self.get_provider(provider).parse_metadata(payload)
