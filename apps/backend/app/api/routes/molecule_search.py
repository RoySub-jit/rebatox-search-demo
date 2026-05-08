from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.errors import raise_api_error
from app.schemas.errors import ErrorResponse
from app.schemas.molecule_search import MoleculeDetailResponse, MoleculeSearchResponse
from app.schemas.source_ingestion import SourceProviderName
from app.services.molecule_search import get_molecule_detail, search_molecules

router = APIRouter(prefix="/molecule-search", tags=["molecule-search"])


@router.get(
    "",
    response_model=MoleculeSearchResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_502_BAD_GATEWAY: {"model": ErrorResponse},
    },
)
def search_molecules_route(
    q: Annotated[str, Query(min_length=2, max_length=120)],
    limit: Annotated[int, Query(ge=1, le=20)] = 10,
) -> MoleculeSearchResponse:
    try:
        return search_molecules(query=q, limit=limit)
    except ValueError as exc:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="molecule_search_invalid_query",
            message=str(exc),
        )
    except RuntimeError as exc:
        raise_api_error(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="molecule_search_upstream_error",
            message=str(exc),
        )


@router.get(
    "/{provider}/{external_id}",
    response_model=MoleculeDetailResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_502_BAD_GATEWAY: {"model": ErrorResponse},
    },
)
def get_molecule_detail_route(
    provider: SourceProviderName,
    external_id: str,
) -> MoleculeDetailResponse:
    try:
        return get_molecule_detail(provider=provider, external_id=external_id)
    except ValueError as exc:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="molecule_detail_unsupported_provider",
            message=str(exc),
        )
    except LookupError as exc:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="molecule_detail_not_found",
            message=str(exc),
        )
    except RuntimeError as exc:
        raise_api_error(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="molecule_detail_upstream_error",
            message=str(exc),
        )
