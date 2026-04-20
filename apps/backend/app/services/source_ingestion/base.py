from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from app.schemas.source_ingestion import NormalizedSourceMetadata, SourceProviderName


class SourceMetadataProvider(ABC):
    source_name: SourceProviderName

    def fetch_metadata(self, *, identifier: str) -> dict[str, Any]:
        raise NotImplementedError(
            f"Network fetching is not implemented yet for {self.source_name} metadata."
        )

    @abstractmethod
    def parse_metadata(self, payload: Mapping[str, Any]) -> NormalizedSourceMetadata:
        """Normalize provider-specific metadata into a shared document model."""
