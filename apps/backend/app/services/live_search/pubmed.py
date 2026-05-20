from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from app.schemas.live_search import (
    EntityType,
    LiveSearchResult,
    LiveWorkspaceResponse,
    LiveWorkspaceReviewCue,
    LiveWorkspaceSection,
)
from app.schemas.source_ingestion import NormalizedSourceMetadata
from app.services.source_ingestion.common import first_text
from app.services.source_ingestion.pubmed import parse_pubmed_metadata

PUBMED_ESEARCH_ENDPOINT = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_ESUMMARY_ENDPOINT = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
PUBMED_EFETCH_ENDPOINT = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def _normalize_query(query: str) -> str:
    normalized = " ".join(query.split())
    if len(normalized) < 2:
        raise ValueError("Search queries must be at least 2 characters long.")

    return normalized


def _fetch_json(endpoint: str, params: Mapping[str, str]) -> dict[str, Any]:
    url = f"{endpoint}?{urlencode(params)}"
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "RebaTox/0.1",
        },
    )

    try:
        with urlopen(request, timeout=15) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"PubMed request failed: {exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"PubMed request failed: {exc.reason}") from exc

    if not isinstance(payload, dict):
        raise RuntimeError("PubMed returned an unexpected response payload.")

    return payload


def _fetch_xml(endpoint: str, params: Mapping[str, str]) -> ElementTree.Element:
    url = f"{endpoint}?{urlencode(params)}"
    request = Request(
        url,
        headers={
            "Accept": "application/xml",
            "User-Agent": "RebaTox/0.1",
        },
    )

    try:
        with urlopen(request, timeout=15) as response:  # noqa: S310
            payload = response.read().decode("utf-8")
    except HTTPError as exc:
        raise RuntimeError(f"PubMed request failed: {exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"PubMed request failed: {exc.reason}") from exc

    try:
        return ElementTree.fromstring(payload)
    except ElementTree.ParseError as exc:
        raise RuntimeError("PubMed returned malformed XML.") from exc


def _build_pubmed_search_expression(entity_type: EntityType, query: str) -> str:
    safe_query = _normalize_query(query).replace('"', "")
    quoted = f'"{safe_query}"'

    if entity_type == "molecule":
        return (
            f"({quoted}[Title/Abstract] OR {quoted}[MeSH Terms])"
        )

    if entity_type == "degradant":
        return (
            f"({quoted}[Title/Abstract]) AND "
            "(degradant[Title/Abstract] OR degradation[Title/Abstract] "
            "OR impurity[Title/Abstract] OR breakdown[Title/Abstract])"
        )

    return (
        f"({quoted}[Title/Abstract]) AND "
        '("extractables and leachables"[Title/Abstract] OR extractable[Title/Abstract] '
        'OR leachable[Title/Abstract] OR migrant[Title/Abstract] OR packaging[Title/Abstract])'
    )


def _fetch_pubmed_ids(*, entity_type: EntityType, query: str, limit: int) -> list[str]:
    payload = _fetch_json(
        PUBMED_ESEARCH_ENDPOINT,
        {
            "db": "pubmed",
            "retmode": "json",
            "retmax": str(limit),
            "sort": "relevance",
            "term": _build_pubmed_search_expression(entity_type, query),
        },
    )

    esearch = payload.get("esearchresult")
    if not isinstance(esearch, Mapping):
        return []

    ids = esearch.get("idlist")
    if not isinstance(ids, list):
        return []

    return [value for value in ids if isinstance(value, str)]


def _fetch_pubmed_summary_records(ids: list[str]) -> list[Mapping[str, Any]]:
    if not ids:
        return []

    payload = _fetch_json(
        PUBMED_ESUMMARY_ENDPOINT,
        {
            "db": "pubmed",
            "retmode": "json",
            "id": ",".join(ids),
        },
    )
    result = payload.get("result")
    if not isinstance(result, Mapping):
        return []

    records: list[Mapping[str, Any]] = []
    for uid in ids:
        record = result.get(uid)
        if isinstance(record, Mapping):
            records.append(record)
    return records


def _wrap_summary_record(record: Mapping[str, Any]) -> Mapping[str, Any]:
    uid = first_text(record.get("uid")) or first_text(record.get("pmid")) or ""
    return {"result": {"uids": [uid], uid: dict(record)}}


def _build_summary_text(metadata: NormalizedSourceMetadata) -> str | None:
    fragments: list[str] = []
    if metadata.journal:
        fragments.append(metadata.journal)
    if metadata.authors:
        fragments.append(f"Lead author: {metadata.authors[0]}")
    if metadata.published_at is not None:
        fragments.append(f"Published {metadata.published_at.isoformat()}")

    if not fragments:
        return None

    return " | ".join(fragments)


def _build_search_result(
    *,
    entity_type: EntityType,
    record: Mapping[str, Any],
) -> LiveSearchResult:
    metadata = parse_pubmed_metadata(_wrap_summary_record(record))

    return LiveSearchResult(
        entity_type=entity_type,
        provider="pubmed",
        external_id=metadata.external_id,
        title=metadata.title,
        subtitle=metadata.journal,
        summary=_build_summary_text(metadata),
        document_type=metadata.document_type,
        published_at=metadata.published_at,
        source_uri=metadata.source_uri,
        identifiers=metadata.identifiers,
        authors=metadata.authors,
        journal=metadata.journal,
        keywords=metadata.keywords,
    )


def search_pubmed_records(
    *,
    entity_type: EntityType,
    query: str,
    limit: int,
) -> list[LiveSearchResult]:
    ids = _fetch_pubmed_ids(entity_type=entity_type, query=query, limit=limit)
    records = _fetch_pubmed_summary_records(ids)
    return [
        _build_search_result(entity_type=entity_type, record=record)
        for record in records
    ]


def _extract_detail_metadata(root: ElementTree.Element) -> dict[str, object]:
    article = root.find(".//PubmedArticle")
    if article is None:
        raise LookupError("No PubMed article record was found for that identifier.")

    article_node = article.find(".//Article")
    if article_node is None:
        raise LookupError("The PubMed article payload did not contain article content.")

    title = " ".join(article_node.findtext("ArticleTitle", default="").split()) or None
    journal = article_node.findtext(".//Journal/Title")

    author_names: list[str] = []
    for author in article_node.findall(".//AuthorList/Author"):
        collective = author.findtext("CollectiveName")
        if collective:
            author_names.append(collective)
            continue

        last_name = author.findtext("LastName")
        initials = author.findtext("Initials")
        if last_name and initials:
            author_names.append(f"{last_name} {initials}")
        elif last_name:
            author_names.append(last_name)

    abstract_paragraphs: list[str] = []
    for abstract_node in article_node.findall(".//Abstract/AbstractText"):
        text = " ".join("".join(abstract_node.itertext()).split())
        if not text:
            continue

        label = abstract_node.attrib.get("Label")
        if label:
            abstract_paragraphs.append(f"{label}: {text}")
        else:
            abstract_paragraphs.append(text)

    keyword_values: list[str] = []
    for keyword in article.findall(".//KeywordList/Keyword"):
        text = " ".join("".join(keyword.itertext()).split())
        if text:
            keyword_values.append(text)

    publication_types: list[str] = []
    for pubtype in article_node.findall(".//PublicationTypeList/PublicationType"):
        text = " ".join("".join(pubtype.itertext()).split())
        if text:
            publication_types.append(text)

    return {
        "title": title,
        "journal": journal,
        "authors": author_names,
        "abstract_paragraphs": abstract_paragraphs,
        "keywords": keyword_values,
        "publication_types": publication_types,
    }


def resolve_pubmed_workspace(
    *,
    entity_type: EntityType,
    external_id: str,
    query: str | None = None,
) -> LiveWorkspaceResponse:
    records = _fetch_pubmed_summary_records([external_id])
    if not records:
        raise LookupError(f"No PubMed record was found for id '{external_id}'.")

    search_result = _build_search_result(entity_type=entity_type, record=records[0])
    detail_root = _fetch_xml(
        PUBMED_EFETCH_ENDPOINT,
        {
            "db": "pubmed",
            "id": external_id,
            "retmode": "xml",
        },
    )
    detail_metadata = _extract_detail_metadata(detail_root)

    sections: list[LiveWorkspaceSection] = []
    abstract_paragraphs = detail_metadata["abstract_paragraphs"]
    if isinstance(abstract_paragraphs, list) and abstract_paragraphs:
        sections.append(
            LiveWorkspaceSection(
                key="abstract",
                title="Abstract",
                content=[value for value in abstract_paragraphs if isinstance(value, str)],
            )
        )

    publication_types = detail_metadata["publication_types"]
    if isinstance(publication_types, list) and publication_types:
        sections.append(
            LiveWorkspaceSection(
                key="publication_types",
                title="Publication types",
                content=[
                    value for value in publication_types if isinstance(value, str)
                ],
            )
        )

    keyword_values = detail_metadata["keywords"]
    if isinstance(keyword_values, list) and keyword_values:
        sections.append(
            LiveWorkspaceSection(
                key="keywords",
                title="Keywords",
                content=[value for value in keyword_values if isinstance(value, str)],
            )
        )

    return LiveWorkspaceResponse(
        entity_type=entity_type,
        query=query,
        record=search_result.model_copy(
            update={
                "authors": detail_metadata["authors"]
                if isinstance(detail_metadata["authors"], list)
                else search_result.authors,
                "journal": detail_metadata["journal"]
                if isinstance(detail_metadata["journal"], str)
                else search_result.journal,
                "summary": search_result.summary
                or (
                    sections[0].content[0]
                    if sections and sections[0].content
                    else search_result.summary
                ),
                "keywords": detail_metadata["keywords"]
                if isinstance(detail_metadata["keywords"], list)
                else search_result.keywords,
            }
        ),
        sections=sections,
        review_cue=LiveWorkspaceReviewCue(
            title="Literature-backed evidence review",
            description=(
                "Use this live PubMed article as a query-time evidence input. "
                "For degradants and E&L topics, this is the fastest path to inspect "
                "mechanistic, safety, and route-relevant literature before saving a review workspace."
            ),
        ),
        retrieved_at=datetime.now(timezone.utc),
    )
