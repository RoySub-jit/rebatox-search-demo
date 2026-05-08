from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.schemas.molecule_search import (
    MoleculeDetailResponse,
    MoleculeLabelSection,
    MoleculeSearchResponse,
    MoleculeSearchResult,
)
from app.schemas.source_ingestion import SourceProviderName
from app.services.source_ingestion.common import first_text, mapping_list, text_list
from app.services.source_ingestion.openfda import parse_openfda_metadata

OPENFDA_LABEL_ENDPOINT = "https://api.fda.gov/drug/label.json"
OPENFDA_SEARCH_FIELDS = (
    "openfda.brand_name",
    "openfda.generic_name",
    "openfda.substance_name",
)
OPENFDA_SECTION_FIELDS = (
    ("purpose", "Purpose"),
    ("indications_and_usage", "Indications and usage"),
    ("dosage_and_administration", "Dosage and administration"),
    ("boxed_warning", "Boxed warning"),
    ("warnings", "Warnings"),
    ("warnings_and_cautions", "Warnings and cautions"),
    ("contraindications", "Contraindications"),
    ("adverse_reactions", "Adverse reactions"),
    ("drug_interactions", "Drug interactions"),
    ("clinical_pharmacology", "Clinical pharmacology"),
)


def _normalize_query(query: str) -> str:
    normalized = " ".join(query.split())
    if len(normalized) < 2:
        raise ValueError("Search queries must be at least 2 characters long.")

    return normalized


def _build_openfda_search_expression(field: str, query: str) -> str:
    safe_query = _normalize_query(query).replace('"', "")
    if " " in safe_query:
        return f'{field}:"{safe_query}"'

    return f"{field}:{safe_query}"


def _extract_error_message(payload_text: str) -> str | None:
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError:
        return None

    error = payload.get("error")
    if isinstance(error, Mapping):
        message = first_text(error.get("message"))
        if message is not None:
            return message

    return None


def _fetch_openfda_payload(params: Mapping[str, str]) -> dict[str, Any]:
    url = f"{OPENFDA_LABEL_ENDPOINT}?{urlencode(params)}"
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "RebaTox/0.1",
        },
    )

    try:
        with urlopen(request, timeout=10) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        payload_text = exc.read().decode("utf-8", errors="replace")
        message = _extract_error_message(payload_text) or exc.reason or "openFDA error"
        if exc.code == 404:
            raise LookupError(message) from exc
        raise RuntimeError(f"openFDA request failed: {message}") from exc
    except URLError as exc:
        raise RuntimeError(f"openFDA request failed: {exc.reason}") from exc

    if not isinstance(payload, dict):
        raise RuntimeError("openFDA returned an unexpected response payload.")

    return payload


def _openfda_record(record: Mapping[str, Any]) -> Mapping[str, Any]:
    openfda = record.get("openfda")
    return openfda if isinstance(openfda, Mapping) else {}


def _build_search_result(record: Mapping[str, Any]) -> MoleculeSearchResult:
    metadata = parse_openfda_metadata(record)
    openfda_record = _openfda_record(record)

    return MoleculeSearchResult(
        provider="openfda",
        external_id=metadata.external_id,
        title=metadata.title,
        generic_name=first_text(openfda_record.get("generic_name")),
        brand_names=text_list(openfda_record.get("brand_name")),
        manufacturer_names=text_list(openfda_record.get("manufacturer_name")),
        routes=text_list(openfda_record.get("route")),
        substance_names=text_list(openfda_record.get("substance_name")),
        product_type=first_text(openfda_record.get("product_type")),
        published_at=metadata.published_at,
        summary=metadata.summary,
        source_uri=metadata.source_uri,
        identifiers=metadata.identifiers,
    )


def search_molecules(*, query: str, limit: int = 10) -> MoleculeSearchResponse:
    normalized_query = _normalize_query(query)
    safe_limit = max(1, min(limit, 20))

    items: list[MoleculeSearchResult] = []
    seen_external_ids: set[str] = set()
    for field in OPENFDA_SEARCH_FIELDS:
        try:
            payload = _fetch_openfda_payload(
                {
                    "search": _build_openfda_search_expression(field, normalized_query),
                    "limit": str(safe_limit),
                    "sort": "effective_time:desc",
                }
            )
        except LookupError:
            continue

        for record in mapping_list(payload.get("results")):
            item = _build_search_result(record)
            if item.external_id in seen_external_ids:
                continue

            seen_external_ids.add(item.external_id)
            items.append(item)
            if len(items) >= safe_limit:
                break

        if len(items) >= safe_limit:
            break

    return MoleculeSearchResponse(
        query=normalized_query,
        limit=safe_limit,
        total_results=len(items),
        items=items,
    )


def get_molecule_detail(
    *,
    provider: SourceProviderName,
    external_id: str,
) -> MoleculeDetailResponse:
    if provider != "openfda":
        raise ValueError(
            f"Provider '{provider}' is not yet supported for live molecule detail lookup."
        )

    payload = _fetch_openfda_payload(
        {
            "search": f'set_id:"{external_id}"',
            "limit": "1",
        }
    )
    records = mapping_list(payload.get("results"))
    if not records:
        raise LookupError(f"No molecule record was found for set id '{external_id}'.")

    record = records[0]
    sections: list[MoleculeLabelSection] = []
    for key, title in OPENFDA_SECTION_FIELDS:
        content = text_list(record.get(key))
        if not content:
            continue

        sections.append(MoleculeLabelSection(key=key, title=title, content=content))

    return MoleculeDetailResponse(
        molecule=_build_search_result(record),
        sections=sections,
    )
