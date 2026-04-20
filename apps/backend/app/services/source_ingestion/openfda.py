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
    parse_date_value,
    require_metadata_field,
    text_list,
)


def _extract_openfda_record(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    results = payload.get("results")

    if isinstance(results, list) and results and isinstance(results[0], Mapping):
        return results[0]

    return payload


def parse_openfda_metadata(payload: Mapping[str, Any]) -> NormalizedSourceMetadata:
    record = _extract_openfda_record(payload)
    openfda = record.get("openfda")
    openfda_record = openfda if isinstance(openfda, Mapping) else {}

    external_id = require_metadata_field(
        first_text(record.get("set_id"))
        or first_text(record.get("id"))
        or first_text(openfda_record.get("spl_set_id")),
        provider="openfda",
        field_name="external_id",
    )
    title = require_metadata_field(
        first_text(openfda_record.get("brand_name"))
        or first_text(record.get("title"))
        or first_text(openfda_record.get("generic_name")),
        provider="openfda",
        field_name="title",
    )
    document_type = first_text(openfda_record.get("product_type")) or "drug_label"

    identifiers: list[SourceRecordIdentifier] = [
        SourceRecordIdentifier(namespace="set_id", value=external_id)
    ]
    for namespace, value in (
        ("application_number", openfda_record.get("application_number")),
        ("product_ndc", openfda_record.get("product_ndc")),
        ("spl_id", openfda_record.get("spl_id")),
    ):
        identifier = build_identifier(namespace, value)
        if identifier is not None:
            identifiers.append(identifier)

    keywords = dedupe_texts(
        [
            *text_list(openfda_record.get("route")),
            *text_list(openfda_record.get("substance_name")),
            *text_list(openfda_record.get("pharm_class_epc")),
        ]
    )

    return NormalizedSourceMetadata(
        provider="openfda",
        external_id=external_id,
        title=title,
        document_type=document_type,
        source_uri=(
            first_text(record.get("source_url"))
            or f"https://api.fda.gov/drug/label.json?search=set_id:{external_id}"
        ),
        published_at=parse_date_value(record.get("effective_time")),
        summary=first_text(record.get("purpose"))
        or first_text(record.get("indications_and_usage")),
        organizations=text_list(openfda_record.get("manufacturer_name")),
        identifiers=dedupe_identifiers(identifiers),
        keywords=keywords,
        raw_metadata=dict(record),
    )


class OpenFDAMetadataProvider(SourceMetadataProvider):
    source_name = "openfda"

    def parse_metadata(self, payload: Mapping[str, Any]) -> NormalizedSourceMetadata:
        return parse_openfda_metadata(payload)
