from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from app.schemas.live_search import (
    EntityType,
    LiveSearchResult,
    LiveWorkspaceExtractedSignal,
    LiveWorkspaceResponse,
    LiveWorkspaceReviewCue,
    LiveWorkspaceSection,
)
from app.schemas.source_ingestion import SourceRecordIdentifier
from app.services.live_search.pod_analysis import build_pod_analysis
from app.services.source_ingestion.common import dedupe_texts

PUBCHEM_CID_SEARCH_ENDPOINT = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{query}/cids/JSON"
PUBCHEM_PROPERTY_ENDPOINT = (
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cids}/property/"
    "Title,MolecularFormula,MolecularWeight,IUPACName,ConnectivitySMILES,InChIKey,XLogP,TPSA/JSON"
)
PUBCHEM_SYNONYMS_ENDPOINT = (
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/synonyms/JSON"
)
PUBCHEM_VIEW_ENDPOINT = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON"
PUBCHEM_DETAIL_HEADINGS = (
    "Drug and Medication Information",
    "Safety and Hazards",
    "Toxicity",
    "Pharmacology and Biochemistry",
)


def _fetch_json(url: str) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "RebaTox/0.1",
        },
    )

    try:
        with urlopen(request, timeout=20) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 404:
            raise LookupError("No PubChem record was found for that identifier.") from exc
        raise RuntimeError(f"PubChem request failed: {exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"PubChem request failed: {exc.reason}") from exc

    if not isinstance(payload, dict):
        raise RuntimeError("PubChem returned an unexpected response payload.")

    return payload


def _normalize_query(query: str) -> str:
    normalized = " ".join(query.split())
    if len(normalized) < 2:
        raise ValueError("Search queries must be at least 2 characters long.")
    return normalized


def _fetch_cids(query: str) -> list[int]:
    payload = _fetch_json(PUBCHEM_CID_SEARCH_ENDPOINT.format(query=quote(query)))
    cid_list = payload.get("IdentifierList", {}).get("CID", [])
    if not isinstance(cid_list, list):
        return []
    return [int(value) for value in cid_list[:12]]


def _fetch_properties(cids: list[int]) -> list[Mapping[str, Any]]:
    if not cids:
        return []
    payload = _fetch_json(
        PUBCHEM_PROPERTY_ENDPOINT.format(cids=",".join(str(cid) for cid in cids))
    )
    properties = payload.get("PropertyTable", {}).get("Properties", [])
    if not isinstance(properties, list):
        return []
    return [value for value in properties if isinstance(value, Mapping)]


def _fetch_synonyms(cid: int) -> list[str]:
    payload = _fetch_json(PUBCHEM_SYNONYMS_ENDPOINT.format(cid=cid))
    items = payload.get("InformationList", {}).get("Information", [])
    if not isinstance(items, list) or not items:
        return []
    synonyms = items[0].get("Synonym", [])
    if not isinstance(synonyms, list):
        return []
    return [value for value in synonyms if isinstance(value, str)]


def _fetch_view_payload(cid: int) -> dict[str, Any]:
    return _fetch_json(PUBCHEM_VIEW_ENDPOINT.format(cid=cid))


def _property_summary(record: Mapping[str, Any]) -> str:
    fragments: list[str] = []
    formula = record.get("MolecularFormula")
    weight = record.get("MolecularWeight")
    iupac = record.get("IUPACName")

    if isinstance(formula, str) and formula:
        fragments.append(f"Formula {formula}")
    if weight is not None:
        fragments.append(f"MW {weight}")
    if isinstance(iupac, str) and iupac:
        fragments.append(iupac)

    return " | ".join(fragments)


def _build_result(
    *,
    entity_type: EntityType,
    record: Mapping[str, Any],
    synonyms: list[str] | None = None,
) -> LiveSearchResult:
    cid = int(record["CID"])
    title = str(record.get("Title") or f"PubChem compound {cid}")
    synonyms = synonyms or []
    subtitle = str(record.get("IUPACName") or "PubChem compound record")
    summary = _property_summary(record) or "PubChem compound record"

    return LiveSearchResult(
        entity_type=entity_type,
        provider="pubchem",
        external_id=str(cid),
        title=title,
        subtitle=subtitle,
        summary=summary,
        document_type="chemical_record",
        source_uri=f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}",
        identifiers=[
            SourceRecordIdentifier(namespace="cid", value=str(cid)),
            *(
                [SourceRecordIdentifier(namespace="inchikey", value=record["InChIKey"])]
                if isinstance(record.get("InChIKey"), str) and record.get("InChIKey")
                else []
            ),
        ],
        generic_name=title,
        brand_names=dedupe_texts(synonyms[:5]),
        substance_names=dedupe_texts([title, *(synonyms[:8])]),
    )


def _extract_strings_from_value(value: Any) -> list[str]:
    results: list[str] = []

    if isinstance(value, Mapping):
        string_markup = value.get("StringWithMarkup")
        if isinstance(string_markup, list):
            for item in string_markup:
                if not isinstance(item, Mapping):
                    continue
                text = item.get("String")
                if isinstance(text, str) and text.strip():
                    results.append(" ".join(text.split()))
        string_value = value.get("String")
        if isinstance(string_value, str) and string_value.strip():
            results.append(" ".join(string_value.split()))
        num_value = value.get("Number")
        if num_value is not None:
            results.append(str(num_value))

    return results


def _flatten_view_section(section: Mapping[str, Any]) -> list[str]:
    values: list[str] = []

    information = section.get("Information")
    if isinstance(information, list):
        for item in information:
            if not isinstance(item, Mapping):
                continue
            name = item.get("Name")
            fragments = _extract_strings_from_value(item.get("Value"))
            if not fragments:
                continue
            text = " ".join(fragments)
            if isinstance(name, str) and name.strip():
                values.append(f"{name}: {text}")
            else:
                values.append(text)

    nested_sections = section.get("Section")
    if isinstance(nested_sections, list):
        for nested in nested_sections:
            if not isinstance(nested, Mapping):
                continue
            nested_heading = nested.get("TOCHeading")
            nested_values = _flatten_view_section(nested)
            if isinstance(nested_heading, str) and nested_heading and nested_values:
                values.append(f"{nested_heading}: {nested_values[0]}")
            values.extend(nested_values[1:])

    return dedupe_texts(values)


def _build_sections(view_payload: Mapping[str, Any], property_record: Mapping[str, Any], synonyms: list[str]) -> list[LiveWorkspaceSection]:
    sections: list[LiveWorkspaceSection] = []

    chemical_profile = [
        f"Molecular formula: {property_record['MolecularFormula']}"
        if property_record.get("MolecularFormula")
        else None,
        f"Molecular weight: {property_record['MolecularWeight']}"
        if property_record.get("MolecularWeight")
        else None,
        f"IUPAC name: {property_record['IUPACName']}"
        if property_record.get("IUPACName")
        else None,
        f"Connectivity SMILES: {property_record['ConnectivitySMILES']}"
        if property_record.get("ConnectivitySMILES")
        else None,
        f"XLogP: {property_record['XLogP']}"
        if property_record.get("XLogP") is not None
        else None,
        f"TPSA: {property_record['TPSA']}"
        if property_record.get("TPSA") is not None
        else None,
    ]
    sections.append(
        LiveWorkspaceSection(
            key="chemical_profile",
            title="Chemical profile",
            content=[value for value in chemical_profile if isinstance(value, str)],
        )
    )

    if synonyms:
        sections.append(
            LiveWorkspaceSection(
                key="synonyms",
                title="Common names and synonyms",
                content=synonyms[:12],
            )
        )

    record = view_payload.get("Record", {})
    view_sections = record.get("Section", []) if isinstance(record, Mapping) else []
    if isinstance(view_sections, list):
        for heading in PUBCHEM_DETAIL_HEADINGS:
            raw_section = next(
                (
                    section
                    for section in view_sections
                    if isinstance(section, Mapping) and section.get("TOCHeading") == heading
                ),
                None,
            )
            if raw_section is None:
                continue
            content = _flatten_view_section(raw_section)
            if content:
                sections.append(
                    LiveWorkspaceSection(
                        key=heading.lower().replace(" ", "_").replace("&", "and"),
                        title=heading,
                        content=content[:6],
                    )
                )

    return sections


def _build_signals(
    *,
    property_record: Mapping[str, Any],
    sections: list[LiveWorkspaceSection],
) -> list[LiveWorkspaceExtractedSignal]:
    signals: list[LiveWorkspaceExtractedSignal] = []

    if property_record.get("MolecularFormula"):
        signals.append(
            LiveWorkspaceExtractedSignal(
                key="molecular_formula",
                label="Molecular formula",
                value=str(property_record["MolecularFormula"]),
                source_section_key="chemical_profile",
                confidence="high",
            )
        )
    if property_record.get("MolecularWeight"):
        signals.append(
            LiveWorkspaceExtractedSignal(
                key="molecular_weight",
                label="Molecular weight",
                value=str(property_record["MolecularWeight"]),
                source_section_key="chemical_profile",
                confidence="high",
            )
        )
    if property_record.get("XLogP") is not None:
        signals.append(
            LiveWorkspaceExtractedSignal(
                key="lipophilicity",
                label="Lipophilicity (XLogP)",
                value=str(property_record["XLogP"]),
                source_section_key="chemical_profile",
                confidence="medium",
            )
        )

    toxicity_section = next((section for section in sections if section.key == "toxicity"), None)
    if toxicity_section and toxicity_section.content:
        signals.append(
            LiveWorkspaceExtractedSignal(
                key="toxicity_signal",
                label="PubChem toxicity cue",
                value=toxicity_section.content[0],
                source_section_key="toxicity",
                confidence="medium",
            )
        )

    return signals


def search_pubchem_records(
    *,
    entity_type: EntityType,
    query: str,
    limit: int,
) -> list[LiveSearchResult]:
    if entity_type != "molecule":
        return []

    normalized_query = _normalize_query(query)
    safe_limit = max(1, min(limit, 8))
    cids = _fetch_cids(normalized_query)[:safe_limit]
    records = _fetch_properties(cids)
    return [
        _build_result(entity_type=entity_type, record=record)
        for record in records[:safe_limit]
    ]


def resolve_pubchem_workspace(
    *,
    entity_type: EntityType,
    external_id: str,
    query: str | None = None,
) -> LiveWorkspaceResponse:
    if entity_type != "molecule":
        raise ValueError("PubChem live workspaces currently support molecule queries only.")

    cid = int(external_id)
    property_records = _fetch_properties([cid])
    if not property_records:
        raise LookupError(f"No PubChem compound record was found for cid '{external_id}'.")

    property_record = property_records[0]
    synonyms = _fetch_synonyms(cid)
    view_payload = _fetch_view_payload(cid)
    record = _build_result(
        entity_type=entity_type,
        record=property_record,
        synonyms=synonyms,
    )
    sections = _build_sections(view_payload, property_record, synonyms)
    extracted_signals = _build_signals(property_record=property_record, sections=sections)

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
            title="Chemical identity and hazard review",
            description=(
                "Use this PubChem workspace to anchor chemical identity, computed properties, and public hazard context before deeper POD or stewardship review."
            ),
        ),
        retrieved_at=datetime.now(timezone.utc),
    )
