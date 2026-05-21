from __future__ import annotations

import re
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
from app.services.live_search.echa import resolve_echa_workspace, search_echa_records
from app.services.live_search.openfda import (
    resolve_openfda_workspace,
    search_openfda_records,
)
from app.services.live_search.pubchem import (
    resolve_pubchem_workspace,
    search_pubchem_records,
)
from app.services.live_search.pubmed import (
    resolve_pubmed_workspace,
    search_pubmed_records,
)

SEARCH_TTL_SECONDS = 6 * 60 * 60
WORKSPACE_TTL_SECONDS = 24 * 60 * 60
NON_ALNUM_PATTERN = re.compile(r"[^a-z0-9]+")

SUPPORTED_SOURCES_BY_ENTITY: dict[EntityType, tuple[SourceProviderName, ...]] = {
    "molecule": ("openfda", "dailymed", "pubchem", "pubmed", "echa"),
    "degradant": ("pubmed", "echa"),
    "el": ("pubmed", "echa"),
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
    if source == "pubchem":
        return search_pubchem_records(entity_type=entity_type, query=query, limit=limit)
    if source == "pubmed":
        return search_pubmed_records(entity_type=entity_type, query=query, limit=limit)
    if source == "echa":
        return search_echa_records(entity_type=entity_type, query=query, limit=limit)

    raise ValueError(f"Provider '{source}' is not yet supported for live search.")


def _source_warning(*, source: SourceProviderName, error: Exception) -> str:
    return f"{source} was unavailable for this search: {error}"


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return NON_ALNUM_PATTERN.sub("", value.casefold())


def _molecule_result_score(item: LiveSearchResult, query: str) -> tuple[float, int]:
    normalized_query = _normalize_text(query)
    generic = _normalize_text(item.generic_name)
    brands = [_normalize_text(value) for value in item.brand_names]
    title = _normalize_text(item.title)

    score = 0.0
    if generic == normalized_query and generic:
        score += 5
    if normalized_query in brands:
        score += 4
    if title == normalized_query and title:
        score += 3.5
    if generic and normalized_query and normalized_query in generic:
        score += 2
    if any(normalized_query and normalized_query in brand for brand in brands):
        score += 1.5
    if title and normalized_query and normalized_query in title:
        score += 1
    if item.summary:
        score += 0.4
    if item.routes:
        score += 0.3
    if item.manufacturer_names:
        score += 0.2

    richness = (
        len(item.brand_names)
        + len(item.routes)
        + len(item.manufacturer_names)
        + len(item.substance_names)
        + (1 if item.summary else 0)
    )
    return score, richness


def _canonical_molecule_key(item: LiveSearchResult) -> str:
    for candidate in (
        item.generic_name,
        item.brand_names[0] if item.brand_names else None,
        item.title,
    ):
        normalized = _normalize_text(candidate)
        if normalized:
            return normalized
    return f"{item.provider}:{item.external_id}"


def _collapse_molecule_results(
    *,
    items: list[LiveSearchResult],
    query: str,
) -> list[LiveSearchResult]:
    deduped: list[LiveSearchResult] = []
    seen_by_provider_key: dict[tuple[str, str], LiveSearchResult] = {}

    for item in items:
        if item.provider not in {"openfda", "dailymed", "pubchem"}:
            deduped.append(item)
            continue

        provider_key = (item.provider, _canonical_molecule_key(item))
        existing = seen_by_provider_key.get(provider_key)
        if existing is None:
            seen_by_provider_key[provider_key] = item
            continue

        if _molecule_result_score(item, query) > _molecule_result_score(existing, query):
            seen_by_provider_key[provider_key] = item

    ordered_label_items = [
        seen_by_provider_key[key]
        for key in seen_by_provider_key
    ]
    ordered_label_items.sort(
        key=lambda item: _molecule_result_score(item, query),
        reverse=True,
    )

    non_label_items = [item for item in deduped if item.provider not in {"openfda", "dailymed", "pubchem"}]
    return ordered_label_items + non_label_items


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
        warnings: list[str] = []

        for source in sources:
            try:
                source_items = _search_single_source(
                    entity_type=entity_type,
                    source=source,
                    query=normalized_query,
                    limit=per_source_limit,
                )
            except RuntimeError as exc:
                warnings.append(_source_warning(source=source, error=exc))
                continue

            for item in source_items:
                item_key = (item.provider, item.external_id)
                if item_key in seen_keys:
                    continue

                seen_keys.add(item_key)
                items.append(item)

        if entity_type == "molecule":
            items = _collapse_molecule_results(items=items, query=normalized_query)

        return LiveSearchResponse(
            entity_type=entity_type,
            query=normalized_query,
            sources=list(sources),
            limit=safe_limit,
            total_results=min(len(items), safe_limit),
            warnings=warnings,
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
        if provider == "pubchem":
            return resolve_pubchem_workspace(
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
        if provider == "echa":
            return resolve_echa_workspace(
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
