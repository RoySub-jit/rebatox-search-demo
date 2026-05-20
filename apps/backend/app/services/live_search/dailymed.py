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
from app.schemas.source_ingestion import SourceRecordIdentifier
from app.services.source_ingestion.common import dedupe_texts, parse_date_value

DAILYMED_SPLS_ENDPOINT = "https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json"
DAILYMED_SPL_XML_ENDPOINT = "https://dailymed.nlm.nih.gov/dailymed/services/v2/spls/{setid}.xml"
HL7_NS = {"hl7": "urn:hl7-org:v3"}
SKIPPED_SECTION_CODES = {"48780-1", "51945-4"}


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
        raise RuntimeError(f"DailyMed request failed: {exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"DailyMed request failed: {exc.reason}") from exc

    if not isinstance(payload, dict):
        raise RuntimeError("DailyMed returned an unexpected response payload.")

    return payload


def _fetch_xml(setid: str) -> ElementTree.Element:
    request = Request(
        DAILYMED_SPL_XML_ENDPOINT.format(setid=setid),
        headers={
            "Accept": "application/xml",
            "User-Agent": "RebaTox/0.1",
        },
    )

    try:
        with urlopen(request, timeout=15) as response:  # noqa: S310
            payload = response.read().decode("utf-8")
    except HTTPError as exc:
        if exc.code == 404:
            raise LookupError(f"No DailyMed record was found for set id '{setid}'.") from exc
        raise RuntimeError(f"DailyMed request failed: {exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"DailyMed request failed: {exc.reason}") from exc

    try:
        return ElementTree.fromstring(payload)
    except ElementTree.ParseError as exc:
        raise RuntimeError("DailyMed returned malformed XML.") from exc


def _element_text(element: ElementTree.Element | None) -> str | None:
    if element is None:
        return None

    value = " ".join("".join(element.itertext()).split())
    return value or None


def _extract_paragraphs(text_node: ElementTree.Element | None) -> list[str]:
    if text_node is None:
        return []

    values: list[str] = []
    direct_text = " ".join((text_node.text or "").split())
    if direct_text:
        values.append(direct_text)

    for paragraph in text_node.findall(".//hl7:paragraph", HL7_NS):
        text = _element_text(paragraph)
        if text:
            values.append(text)

    for item in text_node.findall(".//hl7:item", HL7_NS):
        text = _element_text(item)
        if text:
            values.append(text)

    return dedupe_texts(values)


def _first_section_paragraph(
    sections: list[LiveWorkspaceSection],
    *,
    preferred_keys: tuple[str, ...],
) -> str | None:
    for key in preferred_keys:
        for section in sections:
            if section.key == key and section.content:
                return section.content[0]
    return None


def _extract_root_detail(root: ElementTree.Element) -> dict[str, object]:
    record_title = _element_text(root.find("hl7:title", HL7_NS))
    document_code = root.find("hl7:code", HL7_NS)
    document_type = document_code.attrib.get("displayName") if document_code is not None else None
    published_value = root.find("hl7:effectiveTime", HL7_NS)
    set_id = root.find("hl7:setId", HL7_NS)
    organization_name = _element_text(
        root.find(".//hl7:author/hl7:assignedEntity/hl7:representedOrganization/hl7:name", HL7_NS)
    )
    route_name = root.find(".//hl7:routeCode", HL7_NS)
    route_display = route_name.attrib.get("displayName") if route_name is not None else None
    product_name = _element_text(root.find(".//hl7:manufacturedProduct/hl7:name", HL7_NS))
    generic_name = _element_text(root.find(".//hl7:asEntityWithGeneric/hl7:genericMedicine/hl7:name", HL7_NS))

    substance_names = [
        text
        for ingredient in root.findall(".//hl7:ingredient/hl7:ingredientSubstance/hl7:name", HL7_NS)
        if (text := _element_text(ingredient)) is not None
    ]

    ndc_codes = [
        code.attrib.get("code")
        for code in root.findall(".//hl7:containerPackagedProduct/hl7:code", HL7_NS)
        if code.attrib.get("code")
    ]

    return {
        "title": record_title,
        "document_type": document_type,
        "published_at": parse_date_value(
            published_value.attrib.get("value") if published_value is not None else None
        ),
        "setid": set_id.attrib.get("root") if set_id is not None else None,
        "manufacturer_name": organization_name,
        "route": route_display,
        "product_name": product_name,
        "generic_name": generic_name,
        "substance_names": dedupe_texts([name for name in substance_names if name]),
        "ndcs": dedupe_texts([code for code in ndc_codes if code]),
    }


def _extract_sections(root: ElementTree.Element) -> list[LiveWorkspaceSection]:
    sections: list[LiveWorkspaceSection] = []

    for section in root.findall(".//hl7:structuredBody/hl7:component/hl7:section", HL7_NS):
        code_node = section.find("hl7:code", HL7_NS)
        code = code_node.attrib.get("code") if code_node is not None else None
        if code in SKIPPED_SECTION_CODES:
            continue

        title = _element_text(section.find("hl7:title", HL7_NS))
        if not title:
            continue

        content = _extract_paragraphs(section.find("hl7:text", HL7_NS))
        if not content:
            continue

        section_key = title.strip().lower().replace("&", "and").replace("/", " ").replace("?", "")
        section_key = "_".join(section_key.split())

        sections.append(
            LiveWorkspaceSection(
                key=section_key,
                title=title,
                content=content,
            )
        )

    return sections


def _build_result_from_detail(
    *,
    entity_type: EntityType,
    setid: str,
    detail: Mapping[str, object],
    source_uri: str,
    summary: str | None,
) -> LiveSearchResult:
    identifiers = [SourceRecordIdentifier(namespace="setid", value=setid)]
    for ndc in detail.get("ndcs", []):
        if isinstance(ndc, str):
            identifiers.append(SourceRecordIdentifier(namespace="ndc", value=ndc))

    manufacturer_name = detail.get("manufacturer_name")
    route = detail.get("route")
    generic_name = detail.get("generic_name")
    product_name = detail.get("product_name")
    substance_names = detail.get("substance_names", [])

    return LiveSearchResult(
        entity_type=entity_type,
        provider="dailymed",
        external_id=setid,
        title=(detail.get("title") or product_name or "DailyMed label"),  # type: ignore[arg-type]
        subtitle=detail.get("document_type"),  # type: ignore[arg-type]
        summary=summary,
        document_type=detail.get("document_type"),  # type: ignore[arg-type]
        published_at=detail.get("published_at"),  # type: ignore[arg-type]
        source_uri=source_uri,
        identifiers=identifiers,
        generic_name=generic_name if isinstance(generic_name, str) else None,
        brand_names=[product_name] if isinstance(product_name, str) else [],
        manufacturer_names=[manufacturer_name] if isinstance(manufacturer_name, str) else [],
        routes=[route] if isinstance(route, str) else [],
        substance_names=substance_names if isinstance(substance_names, list) else [],
        product_type=detail.get("document_type"),  # type: ignore[arg-type]
    )


def search_dailymed_records(
    *,
    entity_type: EntityType,
    query: str,
    limit: int,
) -> list[LiveSearchResult]:
    if entity_type != "molecule":
        return []

    normalized_query = _normalize_query(query)
    safe_limit = max(1, min(limit, 10))
    payload = _fetch_json(
        DAILYMED_SPLS_ENDPOINT,
        {
            "drug_name": normalized_query,
            "name_type": "both",
            "pagesize": str(safe_limit),
            "page": "1",
        },
    )

    records = payload.get("data")
    if not isinstance(records, list):
        return []

    results: list[LiveSearchResult] = []
    for record in records:
        if not isinstance(record, Mapping):
            continue

        setid = record.get("setid")
        if not isinstance(setid, str) or not setid.strip():
            continue

        source_uri = f"https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={setid}"
        try:
            root = _fetch_xml(setid)
            detail = _extract_root_detail(root)
            sections = _extract_sections(root)
            summary = _first_section_paragraph(
                sections,
                preferred_keys=("uses", "purpose", "active_ingredient", "directions"),
            )
            results.append(
                _build_result_from_detail(
                    entity_type=entity_type,
                    setid=setid,
                    detail=detail,
                    source_uri=source_uri,
                    summary=summary,
                )
            )
        except (LookupError, RuntimeError):
            published_at = parse_date_value(record.get("published_date"))
            title = record.get("title") if isinstance(record.get("title"), str) else "DailyMed label"
            results.append(
                LiveSearchResult(
                    entity_type=entity_type,
                    provider="dailymed",
                    external_id=setid,
                    title=title,
                    subtitle="drug_label",
                    summary=None,
                    document_type="drug_label",
                    published_at=published_at,
                    source_uri=source_uri,
                    identifiers=[SourceRecordIdentifier(namespace="setid", value=setid)],
                )
            )

    return results[:safe_limit]


def resolve_dailymed_workspace(
    *,
    entity_type: EntityType,
    external_id: str,
    query: str | None = None,
) -> LiveWorkspaceResponse:
    if entity_type != "molecule":
        raise ValueError("DailyMed live workspaces currently support molecule queries only.")

    root = _fetch_xml(external_id)
    detail = _extract_root_detail(root)
    sections = _extract_sections(root)
    summary = _first_section_paragraph(
        sections,
        preferred_keys=("uses", "purpose", "active_ingredient", "directions"),
    )
    source_uri = f"https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={external_id}"

    return LiveWorkspaceResponse(
        entity_type=entity_type,
        query=query,
        record=_build_result_from_detail(
            entity_type=entity_type,
            setid=external_id,
            detail=detail,
            source_uri=source_uri,
            summary=summary,
        ),
        sections=sections,
        review_cue=LiveWorkspaceReviewCue(
            title="DailyMed label review",
            description=(
                "Use this DailyMed label to compare current label structure, route, "
                "warnings, and dosing language alongside other live sources before moving into deeper review."
            ),
        ),
        retrieved_at=datetime.now(timezone.utc),
    )
