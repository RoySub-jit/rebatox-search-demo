from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.schemas.source_ingestion import NormalizedSourceMetadata, SourceRecordIdentifier
from app.services.source_ingestion.base import SourceMetadataProvider
from app.services.source_ingestion.common import (
    build_identifier,
    dedupe_identifiers,
    dedupe_texts,
    first_text,
    mapping_list,
    parse_date_value,
    require_metadata_field,
    text_list,
)


def _extract_dailymed_record(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    data = payload.get("data")

    if isinstance(data, Mapping):
        return data

    if isinstance(data, list) and data and isinstance(data[0], Mapping):
        return data[0]

    return payload


def parse_dailymed_metadata(payload: Mapping[str, Any]) -> NormalizedSourceMetadata:
    record = _extract_dailymed_record(payload)

    external_id = require_metadata_field(
        first_text(record.get("setid")) or first_text(record.get("set_id")),
        provider="dailymed",
        field_name="external_id",
    )
    title = require_metadata_field(
        first_text(record.get("title")),
        provider="dailymed",
        field_name="title",
    )
    document_type = (
        first_text(record.get("document_type"))
        or first_text(record.get("product_type"))
        or "drug_label"
    )

    organizations = dedupe_texts(
        [
            *[
                name
                for packager in mapping_list(record.get("packager"))
                if (name := first_text(packager.get("name"))) is not None
            ],
            *text_list(record.get("labeler")),
        ]
    )

    identifiers: list[SourceRecordIdentifier] = [
        SourceRecordIdentifier(namespace="setid", value=external_id)
    ]
    for namespace, value in (
        ("spl_version", record.get("spl_version")),
        ("ndc", record.get("ndc")),
        ("rxcui", record.get("rxcui")),
    ):
        identifier = build_identifier(namespace, value)
        if identifier is not None:
            identifiers.append(identifier)

    keywords = dedupe_texts(
        [
            *text_list(record.get("route")),
            *text_list(record.get("product_type")),
            *text_list(record.get("generic_name")),
        ]
    )

    return NormalizedSourceMetadata(
        provider="dailymed",
        external_id=external_id,
        title=title,
        document_type=document_type,
        source_uri=(
            first_text(record.get("source_url"))
            or first_text(record.get("url"))
            or f"https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={external_id}"
        ),
        published_at=parse_date_value(
            record.get("published_date")
            or record.get("published")
            or record.get("effective_time")
        ),
        summary=first_text(record.get("indications_and_usage"))
        or first_text(record.get("purpose")),
        organizations=organizations,
        identifiers=dedupe_identifiers(identifiers),
        keywords=keywords,
        raw_metadata=dict(record),
    )


class DailyMedMetadataProvider(SourceMetadataProvider):
    source_name = "dailymed"

    def parse_metadata(self, payload: Mapping[str, Any]) -> NormalizedSourceMetadata:
        return parse_dailymed_metadata(payload)
