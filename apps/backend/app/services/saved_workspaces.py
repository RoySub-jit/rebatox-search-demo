from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.workspace import SavedWorkspace
from app.schemas.live_search import (
    LiveWorkspaceResponse,
    SaveLiveWorkspaceRequest,
    SavedWorkspaceListItem,
    SavedWorkspaceListResponse,
    SavedWorkspaceResponse,
)


def _saved_workspace_to_response(saved_workspace: SavedWorkspace) -> SavedWorkspaceResponse:
    workspace = LiveWorkspaceResponse.model_validate(saved_workspace.snapshot_json)
    return SavedWorkspaceResponse(
        id=saved_workspace.id,
        label=saved_workspace.label,
        notes=saved_workspace.notes,
        entity_type=workspace.entity_type,
        provider=workspace.record.provider,
        external_id=workspace.record.external_id,
        query=workspace.query,
        saved_at=saved_workspace.created_at,
        workspace=workspace,
    )


def save_workspace_snapshot(
    *,
    db: Session,
    payload: SaveLiveWorkspaceRequest,
) -> SavedWorkspaceResponse:
    workspace = payload.workspace
    saved_workspace = SavedWorkspace(
        label=payload.label or workspace.record.title,
        notes=payload.notes,
        entity_type=workspace.entity_type,
        provider=workspace.record.provider,
        external_id=workspace.record.external_id,
        query=workspace.query,
        snapshot_json=workspace.model_dump(mode="json"),
    )
    db.add(saved_workspace)
    db.commit()
    db.refresh(saved_workspace)
    return _saved_workspace_to_response(saved_workspace)


def list_saved_workspaces(
    *,
    db: Session,
    limit: int = 24,
) -> SavedWorkspaceListResponse:
    normalized_limit = max(1, min(limit, 100))
    saved_workspaces = db.scalars(
        select(SavedWorkspace)
        .order_by(SavedWorkspace.created_at.desc(), SavedWorkspace.id.desc())
        .limit(normalized_limit)
    ).all()

    items = []
    for saved_workspace in saved_workspaces:
        workspace = LiveWorkspaceResponse.model_validate(saved_workspace.snapshot_json)
        items.append(
            SavedWorkspaceListItem(
                id=saved_workspace.id,
                label=saved_workspace.label,
                notes=saved_workspace.notes,
                entity_type=workspace.entity_type,
                provider=workspace.record.provider,
                external_id=workspace.record.external_id,
                query=workspace.query,
                saved_at=saved_workspace.created_at,
                record_title=workspace.record.title,
                record_summary=workspace.record.summary,
                extracted_signal_count=len(workspace.extracted_signals),
                section_count=len(workspace.sections),
            )
        )

    return SavedWorkspaceListResponse(
        total_results=len(items),
        items=items,
    )


def get_saved_workspace(
    *,
    db: Session,
    workspace_id: int,
) -> SavedWorkspaceResponse:
    saved_workspace = db.get(SavedWorkspace, workspace_id)
    if saved_workspace is None:
        raise LookupError(f"No saved workspace was found for id '{workspace_id}'.")

    return _saved_workspace_to_response(saved_workspace)
