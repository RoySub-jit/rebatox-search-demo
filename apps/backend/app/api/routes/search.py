from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.errors import raise_api_error
from app.schemas.errors import ErrorResponse
from app.schemas.live_search import EntityType, LiveSearchResponse
from app.schemas.source_ingestion import SourceProviderName
from app.services.live_search.service import search_live_records

router = APIRouter(prefix="/search", tags=["live-search"])


def _parse_sources(value: str | None) -> list[SourceProviderName] | None:
    if value is None or value.strip() == "":
        return None

    items: list[SourceProviderName] = []
    for raw_item in value.split(","):
        item = raw_item.strip().lower()
        if item not in {"dailymed", "openfda", "pubmed"}:
            raise ValueError(f"Unsupported source provider '{raw_item.strip()}'.")
        items.append(item)  # type: ignore[arg-type]

    return items or None


@router.get(
    "",
    response_model=LiveSearchResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_502_BAD_GATEWAY: {"model": ErrorResponse},
    },
)
def search_live_records_route(
    entity_type: EntityType,
    q: Annotated[str, Query(min_length=2, max_length=120)],
    limit: Annotated[int, Query(ge=1, le=20)] = 10,
    sources: Annotated[str | None, Query(max_length=120)] = None,
) -> LiveSearchResponse:
    try:
        return search_live_records(
            entity_type=entity_type,
            query=q,
            limit=limit,
            requested_sources=_parse_sources(sources),
        )
    except ValueError as exc:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="live_search_invalid_request",
            message=str(exc),
        )
    except RuntimeError as exc:
        raise_api_error(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="live_search_upstream_error",
            message=str(exc),
        )
