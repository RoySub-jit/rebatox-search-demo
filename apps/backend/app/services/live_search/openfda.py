from __future__ import annotations

from datetime import datetime, timezone

from app.schemas.live_search import (
    EntityType,
    LiveSearchResult,
    LiveWorkspaceResponse,
    LiveWorkspaceReviewCue,
    LiveWorkspaceSection,
)
from app.services.live_search.pod_analysis import build_pod_analysis
from app.services.molecule_search import get_molecule_detail, search_molecules


def search_openfda_records(
    *,
    entity_type: EntityType,
    query: str,
    limit: int,
) -> list[LiveSearchResult]:
    if entity_type != "molecule":
        return []

    response = search_molecules(query=query, limit=limit)
    return [
        LiveSearchResult(
            entity_type=entity_type,
            provider=item.provider,
            external_id=item.external_id,
            title=item.title,
            subtitle=item.product_type,
            summary=item.summary,
            document_type="label_record",
            published_at=item.published_at,
            source_uri=item.source_uri,
            identifiers=item.identifiers,
            generic_name=item.generic_name,
            brand_names=item.brand_names,
            manufacturer_names=item.manufacturer_names,
            routes=item.routes,
            substance_names=item.substance_names,
            product_type=item.product_type,
        )
        for item in response.items
    ]


def resolve_openfda_workspace(
    *,
    entity_type: EntityType,
    external_id: str,
    query: str | None = None,
) -> LiveWorkspaceResponse:
    if entity_type != "molecule":
        raise ValueError("openFDA live workspaces currently support molecule queries only.")

    detail = get_molecule_detail(provider="openfda", external_id=external_id)

    sections = [
        LiveWorkspaceSection(
            key=section.key,
            title=section.title,
            content=section.content,
        )
        for section in detail.sections
    ]
    record = LiveSearchResult(
        entity_type=entity_type,
        provider=detail.molecule.provider,
        external_id=detail.molecule.external_id,
        title=detail.molecule.title,
        subtitle=detail.molecule.product_type,
        summary=detail.molecule.summary,
        document_type="label_record",
        published_at=detail.molecule.published_at,
        source_uri=detail.molecule.source_uri,
        identifiers=detail.molecule.identifiers,
        generic_name=detail.molecule.generic_name,
        brand_names=detail.molecule.brand_names,
        manufacturer_names=detail.molecule.manufacturer_names,
        routes=detail.molecule.routes,
        substance_names=detail.molecule.substance_names,
        product_type=detail.molecule.product_type,
    )

    return LiveWorkspaceResponse(
        entity_type=entity_type,
        query=query,
        record=record,
        sections=sections,
        pod_analysis=build_pod_analysis(
            record=record,
            sections=sections,
            extracted_signals=[],
        ),
        review_cue=LiveWorkspaceReviewCue(
            title="Label-backed stewardship review",
            description=(
                "Use this live label record to confirm indication, route, dosing, "
                "warnings, and product context before moving into deeper POD or risk review."
            ),
        ),
        retrieved_at=datetime.now(timezone.utc),
    )
