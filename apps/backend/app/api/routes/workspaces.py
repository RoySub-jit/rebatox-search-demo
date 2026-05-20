from __future__ import annotations

from fastapi import APIRouter, status

from app.api.errors import raise_api_error
from app.schemas.errors import ErrorResponse
from app.schemas.live_search import (
    LiveWorkspaceResponse,
    ResolveLiveWorkspaceRequest,
)
from app.services.live_search.service import resolve_live_workspace

router = APIRouter(prefix="/workspaces", tags=["live-workspaces"])


@router.post(
    "/resolve",
    response_model=LiveWorkspaceResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_502_BAD_GATEWAY: {"model": ErrorResponse},
    },
)
def resolve_live_workspace_route(
    request: ResolveLiveWorkspaceRequest,
) -> LiveWorkspaceResponse:
    try:
        return resolve_live_workspace(request)
    except ValueError as exc:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="live_workspace_invalid_request",
            message=str(exc),
        )
    except LookupError as exc:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="live_workspace_not_found",
            message=str(exc),
        )
    except RuntimeError as exc:
        raise_api_error(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="live_workspace_upstream_error",
            message=str(exc),
        )
