from __future__ import annotations

import json
import re
import time
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any, Literal
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from app.schemas.live_search import (
    EntityType,
    LiveSearchResult,
    LiveWorkspaceExtractedSignal,
    LiveWorkspaceResponse,
    LiveWorkspaceReviewCue,
    LiveWorkspaceSection,
)
from app.schemas.source_ingestion import NormalizedSourceMetadata
from app.services.live_search.pod_analysis import build_pod_analysis
from app.services.source_ingestion.common import first_text
from app.services.source_ingestion.pubmed import parse_pubmed_metadata

PUBMED_ESEARCH_ENDPOINT = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_ESUMMARY_ENDPOINT = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
PUBMED_EFETCH_ENDPOINT = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
ROUTE_PATTERN = re.compile(
    r"\b(oral|oral gavage|intravenous|intraperitoneal|subcutaneous|inhalation|intratracheal|topical|dermal|intranasal|dietary|drinking water|gavage)\b",
    re.IGNORECASE,
)
DOSE_PATTERN = re.compile(
    r"\b\d+(?:\.\d+)?\s?(?:mg/kg(?:\s?(?:bw|body weight))?(?:/day|/d)?|mg/day|mg/d|mg/L|mg|ug/kg(?:\s?(?:bw|body weight))?(?:/day|/d)?|µg/kg(?:\s?(?:bw|body weight))?(?:/day|/d)?|ng/mL|ug/mL|µg/mL|uM|μM|nM|mM)\b",
    re.IGNORECASE,
)
POD_PATTERN = re.compile(
    r"\b(?:NOAEL|LOAEL|NOEL|LOEL|NOAEC|LOAEC|NOEC|LOEC|POD|point of departure|benchmark dose|BMDL|BMD|MTD|HNSTD)\b",
    re.IGNORECASE,
)
EXPOSURE_PATTERN = re.compile(
    r"\b(?:AUC|Cmax|exposure|systemic exposure|plasma concentration|clearance|half-life)\b",
    re.IGNORECASE,
)
SPECIES_PATTERN = re.compile(
    r"\b(?:rat|rats|mouse|mice|murine|rabbit|rabbits|dog|dogs|canine|beagle|monkey|monkeys|macaque|cynomolgus|primate|human|humans|healthy volunteers?|patients?|sprague-dawley|wistar|c57bl/6|balb/c)\b",
    re.IGNORECASE,
)
DURATION_PATTERN = re.compile(
    r"\b(?:for\s+)?\d+(?:\.\d+)?\s?(?:hours?|days?|weeks?|months?|years?)\b",
    re.IGNORECASE,
)
ENDPOINT_PATTERN = re.compile(
    r"\b(?:hepatotoxicity|cardiotoxicity|neurotoxicity|genotoxicity|carcinogenicity|reproductive toxicity|developmental toxicity|renal toxicity|liver toxicity|kidney toxicity|tumou?r|cytotoxicity|endocrine disruption|mutagenicity)\b",
    re.IGNORECASE,
)
PUBMED_RETRY_STATUS_CODES = {429, 500, 502, 503, 504}
PUBMED_MAX_ATTEMPTS = 3
PUBMED_RETRY_BACKOFF_SECONDS = 1.5


def _normalize_query(query: str) -> str:
    normalized = " ".join(query.split())
    if len(normalized) < 2:
        raise ValueError("Search queries must be at least 2 characters long.")

    return normalized


def _read_pubmed_payload(request: Request) -> str:
    last_error: Exception | None = None

    for attempt in range(1, PUBMED_MAX_ATTEMPTS + 1):
        try:
            with urlopen(request, timeout=20) as response:  # noqa: S310
                return response.read().decode("utf-8")
        except HTTPError as exc:
            last_error = exc
            if exc.code not in PUBMED_RETRY_STATUS_CODES or attempt >= PUBMED_MAX_ATTEMPTS:
                raise RuntimeError(f"PubMed request failed: {exc.reason}") from exc
        except URLError as exc:
            last_error = exc
            if attempt >= PUBMED_MAX_ATTEMPTS:
                raise RuntimeError(f"PubMed request failed: {exc.reason}") from exc

        time.sleep(PUBMED_RETRY_BACKOFF_SECONDS * attempt)

    if last_error is not None:
        raise RuntimeError("PubMed request failed after retries.") from last_error
    raise RuntimeError("PubMed request failed before a response was returned.")


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
        payload = json.loads(_read_pubmed_payload(request))
    except json.JSONDecodeError as exc:
        raise RuntimeError("PubMed returned malformed JSON.") from exc

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

    payload = _read_pubmed_payload(request)
    try:
        return ElementTree.fromstring(payload)
    except ElementTree.ParseError as exc:
        raise RuntimeError("PubMed returned malformed XML.") from exc


def _build_pubmed_search_expression(entity_type: EntityType, query: str) -> str:
    safe_query = _normalize_query(query).replace('"', "")
    quoted = f'"{safe_query}"'

    if entity_type == "molecule":
        return (
            f"({quoted}[Title/Abstract] OR {quoted}[MeSH Terms]) AND "
            "(toxicity[Title/Abstract] OR toxicology[Title/Abstract] OR dose[Title/Abstract] "
            "OR dosing[Title/Abstract] OR exposure[Title/Abstract] OR pharmacokinetic*[Title/Abstract] "
            'OR safety[Title/Abstract] OR noael[Title/Abstract] OR loael[Title/Abstract] '
            'OR noaec[Title/Abstract] OR loaec[Title/Abstract] OR "point of departure"[Title/Abstract] '
            'OR benchmark dose[Title/Abstract])'
        )

    if entity_type == "degradant":
        return (
            f"({quoted}[Title/Abstract]) AND "
            "(degradant[Title/Abstract] OR degradation[Title/Abstract] "
            "OR impurity[Title/Abstract] OR breakdown[Title/Abstract]) AND "
            "(toxicity[Title/Abstract] OR toxicology[Title/Abstract] OR dose[Title/Abstract] "
            'OR exposure[Title/Abstract] OR noael[Title/Abstract] OR loael[Title/Abstract] OR risk[Title/Abstract])'
        )

    return (
        f"({quoted}[Title/Abstract]) AND "
        '("extractables and leachables"[Title/Abstract] OR extractable[Title/Abstract] '
        'OR leachable[Title/Abstract] OR migrant[Title/Abstract] OR packaging[Title/Abstract]) AND '
        "(toxicity[Title/Abstract] OR toxicology[Title/Abstract] OR exposure[Title/Abstract] "
        'OR safety[Title/Abstract] OR risk[Title/Abstract] OR dose[Title/Abstract])'
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


def _infer_study_model(abstract_text: str, publication_types: list[str]) -> str | None:
    haystack = f"{abstract_text} {' '.join(publication_types)}".casefold()
    if any(token in haystack for token in ("patient", "clinical", "healthy volunteer", "human", "phase ")):
        return "Human / clinical"
    if any(token in haystack for token in ("rat", "mouse", "mice", "dog", "rabbit", "animal model")):
        return "Animal / nonclinical"
    if any(token in haystack for token in ("in vitro", "cell line", "cellular", "assay", "mechanistic")):
        return "In vitro / mechanistic"
    if publication_types:
        return publication_types[0]
    return None


def _infer_focus(entity_type: EntityType, abstract_text: str, query: str | None) -> str | None:
    haystack = abstract_text.casefold()
    if entity_type == "degradant":
        if any(token in haystack for token in ("degradant", "degradation", "impurity", "breakdown")):
            return "Degradant / impurity signal"
        return "Related degradant literature"
    if entity_type == "el":
        if any(token in haystack for token in ("extractable", "leachable", "packaging", "migrant")):
            return "E&L / packaging signal"
        return "Related E&L literature"
    if query and query.casefold() in haystack:
        return "Direct molecule literature"
    return "Molecule-related literature"


def _normalize_pod_term(value: str) -> str:
    upper_value = value.upper()
    if upper_value in {"NOAEL", "LOAEL", "POD", "BMD", "BMDL", "MTD"}:
        return upper_value
    return value.title()


def _build_pod_candidate_summary(sentence: str) -> str | None:
    pod_match = POD_PATTERN.search(sentence)
    if pod_match is None:
        return None

    pod_term = _normalize_pod_term(pod_match.group(0))
    dose_match = DOSE_PATTERN.search(sentence)
    if dose_match is not None:
        return f"{pod_term} candidate at {dose_match.group(0)}"

    return f"{pod_term} referenced in abstract"


def _first_match_text(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    if match is None:
        return None
    return " ".join(match.group(0).split())


def _build_evidence_quality_signal(
    *,
    has_pod_sentence: bool,
    has_dose_sentence: bool,
    has_route: bool,
    has_species: bool,
    has_duration: bool,
    study_model: str | None,
) -> tuple[str, str, Literal["high", "medium", "low"]]:
    if has_pod_sentence and has_dose_sentence and (has_species or study_model is not None):
        return (
            "High evidence quality",
            "The abstract contains explicit POD language, dose context, and enough study detail to support a meaningful first-pass toxicology curation review.",
            "high",
        )
    if (has_pod_sentence and has_dose_sentence) or (has_dose_sentence and has_route and study_model is not None):
        return (
            "Moderate evidence quality",
            "The abstract contains structured dose or POD cues, but still needs fuller confirmation before it should anchor a final curated POD decision.",
            "medium",
        )
    return (
        "Low evidence quality",
        "This record provides useful scientific context, but the abstract alone does not yet expose enough structured toxicology detail for confident POD curation.",
        "low",
    )


def _build_curation_readiness_signal(
    *,
    has_pod_sentence: bool,
    has_dose_sentence: bool,
    has_species: bool,
    has_duration: bool,
) -> tuple[str, str]:
    if has_pod_sentence and has_dose_sentence and has_species:
        return (
            "Ready for screening worksheet use",
            "This source has enough explicit dose and POD structure to justify a screening worksheet pass, although formal stewardship review may still require full-text confirmation.",
        )
    if has_dose_sentence or has_pod_sentence:
        return (
            "Requires confirmation before formal curation",
            "The source exposes at least one actionable toxicology cue, but it should still be treated as an intermediate evidence input rather than a final POD anchor.",
        )
    return (
        "Contextual evidence only",
        "Use this source mainly for background scientific context, not as the primary basis for a curated POD without stronger follow-up support.",
    )


def _build_pubmed_signals(
    *,
    entity_type: EntityType,
    detail_metadata: Mapping[str, object],
    query: str | None,
) -> list[LiveWorkspaceExtractedSignal]:
    signals: list[LiveWorkspaceExtractedSignal] = []

    abstract_paragraphs = [
        value for value in detail_metadata.get("abstract_paragraphs", []) if isinstance(value, str)
    ]
    abstract_text = " ".join(abstract_paragraphs)
    publication_types = [
        value for value in detail_metadata.get("publication_types", []) if isinstance(value, str)
    ]
    keywords = [value for value in detail_metadata.get("keywords", []) if isinstance(value, str)]
    abstract_sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", abstract_text)
        if sentence.strip()
    ]

    focus = _infer_focus(entity_type, abstract_text, query)
    if focus:
        signals.append(
            LiveWorkspaceExtractedSignal(
                key="evidence_focus",
                label="Evidence focus",
                value=focus,
                source_section_key="abstract",
                confidence="medium",
            )
        )

    study_model = _infer_study_model(abstract_text, publication_types)
    if study_model:
        signals.append(
            LiveWorkspaceExtractedSignal(
                key="study_model",
                label="Study model",
                value=study_model,
                source_section_key="publication_types" if publication_types else "abstract",
                confidence="medium",
            )
        )

    route_mentions = list(dict.fromkeys(match.group(1).lower() for match in ROUTE_PATTERN.finditer(abstract_text)))
    if route_mentions:
        signals.append(
            LiveWorkspaceExtractedSignal(
                key="route_mentions",
                label="Route mentions",
                value=", ".join(route_mentions),
                source_section_key="abstract",
                confidence="medium",
            )
        )

    species_signal = _first_match_text(SPECIES_PATTERN, abstract_text)
    if species_signal:
        signals.append(
            LiveWorkspaceExtractedSignal(
                key="species_signal",
                label="Species / population",
                value=species_signal,
                source_section_key="abstract",
                confidence="medium",
            )
        )

    duration_signal = _first_match_text(DURATION_PATTERN, abstract_text)
    if duration_signal:
        signals.append(
            LiveWorkspaceExtractedSignal(
                key="duration_signal",
                label="Study duration",
                value=duration_signal,
                source_section_key="abstract",
                confidence="medium",
            )
        )

    dose_mentions = list(dict.fromkeys(match.group(0) for match in DOSE_PATTERN.finditer(abstract_text)))
    if dose_mentions:
        signals.append(
            LiveWorkspaceExtractedSignal(
                key="dose_or_exposure_context",
                label="Dose / exposure context",
                value="; ".join(dose_mentions[:4]),
                source_section_key="abstract",
                confidence="medium",
            )
        )

    if dose_mentions:
        signals.append(
            LiveWorkspaceExtractedSignal(
                key="dose_regimen_summary",
                label="Dose regimen summary",
                value="; ".join(dose_mentions[:3]),
                source_section_key="abstract",
                confidence="medium",
            )
        )

    dose_sentence = next(
        (sentence for sentence in abstract_sentences if DOSE_PATTERN.search(sentence)),
        None,
    )
    if dose_sentence:
        signals.append(
            LiveWorkspaceExtractedSignal(
                key="dose_sentence",
                label="Dose sentence",
                value=dose_sentence,
                source_section_key="abstract",
                confidence="medium",
            )
        )

    pod_sentence = next(
        (sentence for sentence in abstract_sentences if POD_PATTERN.search(sentence)),
        None,
    )
    if pod_sentence:
        signals.append(
            LiveWorkspaceExtractedSignal(
                key="pod_signal",
                label="POD / toxicology signal",
                value=pod_sentence,
                source_section_key="abstract",
                confidence="medium",
            )
        )
        pod_candidate = _build_pod_candidate_summary(pod_sentence)
        if pod_candidate:
            signals.append(
                LiveWorkspaceExtractedSignal(
                    key="pod_candidate",
                    label="Potential POD candidate",
                    value=pod_candidate,
                    source_section_key="abstract",
                    confidence="high" if DOSE_PATTERN.search(pod_sentence) else "medium",
            )
        )

    endpoint_signal = _first_match_text(ENDPOINT_PATTERN, abstract_text)
    if endpoint_signal:
        signals.append(
            LiveWorkspaceExtractedSignal(
                key="endpoint_signal",
                label="Toxicology endpoint cue",
                value=endpoint_signal,
                source_section_key="abstract",
                confidence="medium",
            )
        )

    exposure_sentence = next(
        (sentence for sentence in abstract_sentences if EXPOSURE_PATTERN.search(sentence)),
        None,
    )
    if exposure_sentence:
        signals.append(
            LiveWorkspaceExtractedSignal(
                key="exposure_signal",
                label="Exposure signal",
                value=exposure_sentence,
                source_section_key="abstract",
                confidence="medium",
            )
        )

    evidence_quality_label, evidence_quality_value, evidence_quality_confidence = _build_evidence_quality_signal(
        has_pod_sentence=pod_sentence is not None,
        has_dose_sentence=dose_sentence is not None,
        has_route=bool(route_mentions),
        has_species=species_signal is not None,
        has_duration=duration_signal is not None,
        study_model=study_model,
    )
    signals.append(
        LiveWorkspaceExtractedSignal(
            key="evidence_quality",
            label=evidence_quality_label,
            value=evidence_quality_value,
            source_section_key="abstract",
            confidence=evidence_quality_confidence,
        )
    )

    curation_readiness_label, curation_readiness_value = _build_curation_readiness_signal(
        has_pod_sentence=pod_sentence is not None,
        has_dose_sentence=dose_sentence is not None,
        has_species=species_signal is not None,
        has_duration=duration_signal is not None,
    )
    signals.append(
        LiveWorkspaceExtractedSignal(
            key="curation_readiness",
            label=curation_readiness_label,
            value=curation_readiness_value,
            source_section_key="abstract",
            confidence="medium" if dose_sentence or pod_sentence else "low",
        )
    )

    signals.append(
        LiveWorkspaceExtractedSignal(
            key="inference_boundary",
            label="Inference boundary",
            value=(
                "These extracted cues are derived from the structured PubMed abstract and metadata only. Full-text or source-document review is still recommended before using the record as a final curated POD basis."
            ),
            source_section_key="abstract",
            confidence="high",
        )
    )

    if pod_sentence and dose_sentence:
        signals.append(
            LiveWorkspaceExtractedSignal(
                key="toxicology_takeaway",
                label="Toxicology takeaway",
                value=(
                    "Dose context and explicit POD language were both identified in the abstract, "
                    "which makes this article a stronger candidate for follow-up toxicology review."
                ),
                source_section_key="abstract",
                confidence="high",
            )
        )
    elif pod_sentence or dose_sentence:
        signals.append(
            LiveWorkspaceExtractedSignal(
                key="toxicology_takeaway",
                label="Toxicology takeaway",
                value=(
                    "The abstract contains at least one structured toxicology cue "
                    "(dose or POD language), but may still require a deeper full-text review."
                ),
                source_section_key="abstract",
                confidence="medium",
            )
        )

    if publication_types:
        signals.append(
            LiveWorkspaceExtractedSignal(
                key="publication_type",
                label="Publication type",
                value=", ".join(publication_types[:3]),
                source_section_key="publication_types",
                confidence="high",
            )
        )

    if keywords:
        signals.append(
            LiveWorkspaceExtractedSignal(
                key="keyword_signal",
                label="Keyword signal",
                value=", ".join(keywords[:5]),
                source_section_key="keywords",
                confidence="low",
            )
        )

    return signals


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

    record = search_result.model_copy(
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
    )
    extracted_signals = _build_pubmed_signals(
        entity_type=entity_type,
        detail_metadata=detail_metadata,
        query=query,
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
            title="Literature-backed evidence review",
            description=(
                "Use this live PubMed article as a query-time evidence input. "
                "For degradants and E&L topics, this is the fastest path to inspect "
                "mechanistic, safety, and route-relevant literature before saving a review workspace."
            ),
        ),
        retrieved_at=datetime.now(timezone.utc),
    )
