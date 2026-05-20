from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote_plus

from app.schemas.live_search import (
    EntityType,
    LiveSearchResult,
    LiveWorkspaceExtractedSignal,
    LiveWorkspaceResponse,
    LiveWorkspaceReviewCue,
    LiveWorkspaceSection,
)
from app.services.live_search.pod_analysis import build_pod_analysis


def _build_search_uri(query: str) -> str:
    return f"https://echa.europa.eu/search-for-chemicals?query={quote_plus(query)}"


def _build_external_id(entity_type: EntityType, query: str) -> str:
    normalized = "-".join(query.lower().split())
    return f"{entity_type}:{normalized}"


def search_echa_records(
    *,
    entity_type: EntityType,
    query: str,
    limit: int,
) -> list[LiveSearchResult]:
    del limit
    title_prefix = {
        "molecule": "ECHA CHEM lookup",
        "degradant": "ECHA regulatory lookup",
        "el": "ECHA packaging / substance lookup",
    }[entity_type]

    return [
        LiveSearchResult(
            entity_type=entity_type,
            provider="echa",
            external_id=_build_external_id(entity_type, query),
            title=f"{title_prefix}: {query}",
            subtitle="Regulatory lookup",
            summary=(
                "Open the ECHA chemicals database in the browser for classification, "
                "registration, and hazard context. Server-side enrichment is limited in this prototype."
            ),
            document_type="regulatory_lookup",
            source_uri=_build_search_uri(query),
            generic_name=query if entity_type == "molecule" else None,
            substance_names=[query] if entity_type == "molecule" else [],
        )
    ]


def resolve_echa_workspace(
    *,
    entity_type: EntityType,
    external_id: str,
    query: str | None = None,
) -> LiveWorkspaceResponse:
    active_query = query or external_id.split(":", 1)[-1].replace("-", " ")
    source_uri = _build_search_uri(active_query)

    sections = [
        LiveWorkspaceSection(
            key="regulatory_scope",
            title="Regulatory scope",
            content=[
                "Use this ECHA CHEM handoff to inspect harmonised classification, registration context, and regulatory substance records.",
                "This prototype exposes ECHA as a browser-driven regulatory source rather than a server-side parsed database because the upstream site limits automated access.",
            ],
        ),
        LiveWorkspaceSection(
            key="manual_review_steps",
            title="Manual review steps",
            content=[
                "Open the ECHA source page and confirm whether the searched substance has a direct infocard or registry hit.",
                "Capture any classification, DNEL, or hazard language that is relevant to the current RebaTox review workspace.",
            ],
        ),
    ]
    extracted_signals = [
        LiveWorkspaceExtractedSignal(
            key="regulatory_lookup",
            label="Regulatory lookup",
            value="ECHA should be used as a regulatory context source for hazard and registration review.",
            source_section_key="regulatory_scope",
            confidence="medium",
        ),
        LiveWorkspaceExtractedSignal(
            key="manual_follow_up",
            label="Manual follow-up required",
            value="Direct server-side parsing is not enabled for ECHA in this prototype, so reviewers should open the source page for final verification.",
            source_section_key="manual_review_steps",
            confidence="high",
        ),
    ]
    record = LiveSearchResult(
        entity_type=entity_type,
        provider="echa",
        external_id=external_id,
        title=f"ECHA CHEM lookup: {active_query}",
        subtitle="Regulatory lookup",
        summary="Manual regulatory lookup workspace generated from the current query.",
        document_type="regulatory_lookup",
        source_uri=source_uri,
        generic_name=active_query if entity_type == "molecule" else None,
        substance_names=[active_query] if entity_type == "molecule" else [],
    )

    return LiveWorkspaceResponse(
        entity_type=entity_type,
        query=query,
        record=record,
        sections=sections,
        extracted_signals=extracted_signals,
        pod_analysis=build_pod_analysis(
            record=record,
            sections=sections,
            extracted_signals=extracted_signals,
        ),
        review_cue=LiveWorkspaceReviewCue(
            title="Regulatory context lookup",
            description=(
                "Use this ECHA workspace as a regulatory handoff. It keeps the current query anchored in RebaTox while directing the reviewer to a public regulatory source."
            ),
        ),
        retrieved_at=datetime.now(timezone.utc),
    )
