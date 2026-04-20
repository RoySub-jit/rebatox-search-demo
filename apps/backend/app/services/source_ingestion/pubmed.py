from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.schemas.source_ingestion import NormalizedSourceMetadata, SourceRecordIdentifier
from app.services.source_ingestion.base import SourceMetadataProvider
from app.services.source_ingestion.common import (
    dedupe_identifiers,
    dedupe_texts,
    first_text,
    mapping_list,
    parse_date_value,
    require_metadata_field,
    text_list,
)


def _extract_pubmed_record(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    result = payload.get("result")
    if not isinstance(result, Mapping):
        return payload

    uids = result.get("uids")
    if isinstance(uids, list):
        for uid in uids:
            if isinstance(uid, str):
                record = result.get(uid)
                if isinstance(record, Mapping):
                    return record

    return result


def parse_pubmed_metadata(payload: Mapping[str, Any]) -> NormalizedSourceMetadata:
    record = _extract_pubmed_record(payload)

    external_id = require_metadata_field(
        first_text(record.get("uid"))
        or first_text(record.get("pmid")),
        provider="pubmed",
        field_name="external_id",
    )
    title = require_metadata_field(
        first_text(record.get("title")),
        provider="pubmed",
        field_name="title",
    )
    document_type = first_text(record.get("pubtype")) or "journal_article"

    authors = dedupe_texts(
        [
            name
            for author in mapping_list(record.get("authors"))
            if (name := first_text(author.get("name"))) is not None
        ]
    )

    identifiers: list[SourceRecordIdentifier] = [
        SourceRecordIdentifier(namespace="pubmed", value=external_id)
    ]
    for article_id in mapping_list(record.get("articleids")):
        namespace = first_text(article_id.get("idtype"))
        value = first_text(article_id.get("value"))
        if namespace is None or value is None:
            continue

        identifiers.append(SourceRecordIdentifier(namespace=namespace, value=value))

    return NormalizedSourceMetadata(
        provider="pubmed",
        external_id=external_id,
        title=title,
        document_type=document_type,
        source_uri=(
            first_text(record.get("source_url"))
            or f"https://pubmed.ncbi.nlm.nih.gov/{external_id}/"
        ),
        published_at=parse_date_value(
            record.get("sortpubdate") or record.get("pubdate")
        ),
        summary=first_text(record.get("abstract")),
        journal=first_text(record.get("fulljournalname"))
        or first_text(record.get("source")),
        authors=authors,
        identifiers=dedupe_identifiers(identifiers),
        keywords=dedupe_texts(text_list(record.get("keywords"))),
        raw_metadata=dict(record),
    )


class PubMedMetadataProvider(SourceMetadataProvider):
    source_name = "pubmed"

    def parse_metadata(self, payload: Mapping[str, Any]) -> NormalizedSourceMetadata:
        return parse_pubmed_metadata(payload)
