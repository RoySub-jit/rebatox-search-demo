from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.errors import raise_api_error
from app.db.session import get_db
from app.schemas.errors import ErrorResponse
from app.schemas.live_search import (
    LiveWorkspaceResponse,
    ResolveLiveWorkspaceRequest,
    SaveLiveWorkspaceRequest,
    SavedWorkspaceListResponse,
    SavedWorkspaceResponse,
    UpdateSavedWorkspaceRequest,
)
from app.services.live_search.service import resolve_live_workspace
from app.services.saved_workspaces import (
    get_saved_workspace,
    list_saved_workspaces,
    save_workspace_snapshot,
    update_saved_workspace,
)

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


@router.post(
    "/save",
    response_model=SavedWorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
    },
)
def save_live_workspace_route(
    payload: SaveLiveWorkspaceRequest,
    db: Session = Depends(get_db),
) -> SavedWorkspaceResponse:
    try:
        return save_workspace_snapshot(db=db, payload=payload)
    except ValueError as exc:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="saved_workspace_invalid_request",
            message=str(exc),
        )


@router.get(
    "",
    response_model=SavedWorkspaceListResponse,
)
def list_saved_workspaces_route(
    limit: int = 24,
    db: Session = Depends(get_db),
) -> SavedWorkspaceListResponse:
    return list_saved_workspaces(db=db, limit=limit)


@router.get(
    "/{workspace_id}",
    response_model=SavedWorkspaceResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    },
)
def get_saved_workspace_route(
    workspace_id: int,
    db: Session = Depends(get_db),
) -> SavedWorkspaceResponse:
    try:
        return get_saved_workspace(db=db, workspace_id=workspace_id)
    except LookupError as exc:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="saved_workspace_not_found",
            message=str(exc),
        )


@router.put(
    "/{workspace_id}",
    response_model=SavedWorkspaceResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    },
)
def update_saved_workspace_route(
    workspace_id: int,
    payload: UpdateSavedWorkspaceRequest,
    db: Session = Depends(get_db),
) -> SavedWorkspaceResponse:
    try:
        return update_saved_workspace(
            db=db,
            workspace_id=workspace_id,
            payload=payload,
        )
    except ValueError as exc:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="saved_workspace_invalid_request",
            message=str(exc),
        )
    except LookupError as exc:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="saved_workspace_not_found",
            message=str(exc),
        )
