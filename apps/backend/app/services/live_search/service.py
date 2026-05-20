from __future__ import annotations

from collections.abc import Sequence
from math import ceil

from app.schemas.live_search import (
    EntityType,
    LiveSearchResponse,
    LiveSearchResult,
    LiveWorkspaceResponse,
    ResolveLiveWorkspaceRequest,
)
from app.schemas.source_ingestion import SourceProviderName
from app.services.cache import get_cache
from app.services.live_search.dailymed import (
    resolve_dailymed_workspace,
    search_dailymed_records,
)
from app.services.live_search.openfda import (
    resolve_openfda_workspace,
    search_openfda_records,
)
from app.services.live_search.pubmed import (
    resolve_pubmed_workspace,
    search_pubmed_records,
)

SEARCH_TTL_SECONDS = 6 * 60 * 60
WORKSPACE_TTL_SECONDS = 24 * 60 * 60

SUPPORTED_SOURCES_BY_ENTITY: dict[EntityType, tuple[SourceProviderName, ...]] = {
    "molecule": ("openfda", "dailymed", "pubmed"),
    "degradant": ("pubmed",),
    "el": ("pubmed",),
}


def _normalize_query(query: str) -> str:
    normalized = " ".join(query.split())
    if len(normalized) < 2:
        raise ValueError("Search queries must be at least 2 characters long.")

    return normalized


def _requested_sources(
    *,
    entity_type: EntityType,
    requested_sources: Sequence[SourceProviderName] | None = None,
) -> tuple[SourceProviderName, ...]:
    supported = SUPPORTED_SOURCES_BY_ENTITY[entity_type]
    if not requested_sources:
        return supported

    unique_sources = tuple(dict.fromkeys(requested_sources))
    invalid_sources = [source for source in unique_sources if source not in supported]
    if invalid_sources:
        invalid_list = ", ".join(invalid_sources)
        raise ValueError(
            f"Unsupported source selection for {entity_type} search: {invalid_list}."
        )

    return unique_sources


def _search_single_source(
    *,
    entity_type: EntityType,
    source: SourceProviderName,
    query: str,
    limit: int,
) -> list[LiveSearchResult]:
    if source == "openfda":
        return search_openfda_records(entity_type=entity_type, query=query, limit=limit)
    if source == "dailymed":
        return search_dailymed_records(entity_type=entity_type, query=query, limit=limit)
    if source == "pubmed":
        return search_pubmed_records(entity_type=entity_type, query=query, limit=limit)

    raise ValueError(f"Provider '{source}' is not yet supported for live search.")


def search_live_records(
    *,
    entity_type: EntityType,
    query: str,
    limit: int = 10,
    requested_sources: Sequence[SourceProviderName] | None = None,
) -> LiveSearchResponse:
    normalized_query = _normalize_query(query)
    safe_limit = max(1, min(limit, 20))
    sources = _requested_sources(
        entity_type=entity_type,
        requested_sources=requested_sources,
    )
    cache_key = (
        f"live-search:{entity_type}:{','.join(sources)}:"
        f"{normalized_query.casefold()}:{safe_limit}"
    )

    def load_response() -> LiveSearchResponse:
        per_source_limit = max(1, ceil(safe_limit / max(len(sources), 1)))
        items: list[LiveSearchResult] = []
        seen_keys: set[tuple[str, str]] = set()

        for source in sources:
            source_items = _search_single_source(
                entity_type=entity_type,
                source=source,
                query=normalized_query,
                limit=per_source_limit,
            )
            for item in source_items:
                item_key = (item.provider, item.external_id)
                if item_key in seen_keys:
                    continue

                seen_keys.add(item_key)
                items.append(item)

        return LiveSearchResponse(
            entity_type=entity_type,
            query=normalized_query,
            sources=list(sources),
            limit=safe_limit,
            total_results=min(len(items), safe_limit),
            items=items[:safe_limit],
        )

    return get_cache().get_or_set(
        cache_key,
        ttl_seconds=SEARCH_TTL_SECONDS,
        loader=load_response,
    )


def resolve_live_workspace(
    request: ResolveLiveWorkspaceRequest,
) -> LiveWorkspaceResponse:
    supported_sources = _requested_sources(
        entity_type=request.entity_type,
        requested_sources=[request.provider],
    )
    provider = supported_sources[0]
    cache_key = (
        f"live-workspace:{request.entity_type}:{provider}:{request.external_id}:"
        f"{(request.query or '').strip().casefold()}"
    )

    def load_workspace() -> LiveWorkspaceResponse:
        if provider == "openfda":
            return resolve_openfda_workspace(
                entity_type=request.entity_type,
                external_id=request.external_id,
                query=request.query,
            )
        if provider == "dailymed":
            return resolve_dailymed_workspace(
                entity_type=request.entity_type,
                external_id=request.external_id,
                query=request.query,
            )
        if provider == "pubmed":
            return resolve_pubmed_workspace(
                entity_type=request.entity_type,
                external_id=request.external_id,
                query=request.query,
            )

        raise ValueError(f"Provider '{provider}' is not yet supported for live workspaces.")

    return get_cache().get_or_set(
        cache_key,
        ttl_seconds=WORKSPACE_TTL_SECONDS,
        loader=load_workspace,
    )
