from __future__ import annotations

from datetime import date

import pytest

from app.services.source_ingestion import (
    SourceIngestionService,
    parse_dailymed_metadata,
    parse_openfda_metadata,
    parse_pubmed_metadata,
)


def test_parse_dailymed_metadata_normalizes_core_fields():
    payload = {
        "data": {
            "setid": "dm-set-123",
            "title": "Cardiovex XR prescribing information",
            "published_date": "2024-03-15",
            "product_type": "HUMAN PRESCRIPTION DRUG",
            "indications_and_usage": "Used for long-term symptomatic control.",
            "route": ["ORAL"],
            "generic_name": ["cardiovex"],
            "spl_version": "7",
            "packager": [{"name": "Example Labs"}],
        }
    }

    metadata = parse_dailymed_metadata(payload)

    assert metadata.provider == "dailymed"
    assert metadata.external_id == "dm-set-123"
    assert metadata.title == "Cardiovex XR prescribing information"
    assert metadata.document_type == "HUMAN PRESCRIPTION DRUG"
    assert metadata.source_uri == (
        "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=dm-set-123"
    )
    assert metadata.published_at == date(2024, 3, 15)
    assert metadata.summary == "Used for long-term symptomatic control."
    assert metadata.organizations == ["Example Labs"]
    assert metadata.keywords == ["ORAL", "HUMAN PRESCRIPTION DRUG", "cardiovex"]
    assert [(identifier.namespace, identifier.value) for identifier in metadata.identifiers] == [
        ("setid", "dm-set-123"),
        ("spl_version", "7"),
    ]


def test_parse_openfda_metadata_normalizes_core_fields():
    payload = {
        "results": [
            {
                "set_id": "ofda-set-456",
                "effective_time": "20240201",
                "purpose": ["Supports controlled exposure management."],
                "openfda": {
                    "brand_name": ["Cardiovex XR"],
                    "generic_name": ["cardiovex"],
                    "manufacturer_name": ["Example Labs"],
                    "product_type": ["HUMAN PRESCRIPTION DRUG"],
                    "route": ["ORAL"],
                    "substance_name": ["CARDIOVEX HYDROCHLORIDE"],
                    "application_number": ["NDA123456"],
                },
            }
        ]
    }

    metadata = parse_openfda_metadata(payload)

    assert metadata.provider == "openfda"
    assert metadata.external_id == "ofda-set-456"
    assert metadata.title == "Cardiovex XR"
    assert metadata.document_type == "HUMAN PRESCRIPTION DRUG"
    assert metadata.source_uri == (
        "https://api.fda.gov/drug/label.json?search=set_id:ofda-set-456"
    )
    assert metadata.published_at == date(2024, 2, 1)
    assert metadata.summary == "Supports controlled exposure management."
    assert metadata.organizations == ["Example Labs"]
    assert metadata.keywords == ["ORAL", "CARDIOVEX HYDROCHLORIDE"]
    assert [(identifier.namespace, identifier.value) for identifier in metadata.identifiers] == [
        ("set_id", "ofda-set-456"),
        ("application_number", "NDA123456"),
    ]


def test_parse_pubmed_metadata_normalizes_core_fields():
    payload = {
        "result": {
            "uids": ["12345678"],
            "12345678": {
                "uid": "12345678",
                "title": "Risk framing for Cardiovex XR in a comparative safety package",
                "sortpubdate": "2024/01/31 00:00",
                "fulljournalname": "Journal of Applied Safety Science",
                "abstract": "This study examines deterministic safety framing inputs.",
                "keywords": ["risk assessment", "exposure"],
                "pubtype": ["Journal Article"],
                "authors": [
                    {"name": "Smith J"},
                    {"name": "Lee A"},
                ],
                "articleids": [
                    {"idtype": "pubmed", "value": "12345678"},
                    {"idtype": "doi", "value": "10.1000/cardiovex.2024.01"},
                ],
            },
        }
    }

    metadata = parse_pubmed_metadata(payload)

    assert metadata.provider == "pubmed"
    assert metadata.external_id == "12345678"
    assert metadata.title == (
        "Risk framing for Cardiovex XR in a comparative safety package"
    )
    assert metadata.document_type == "Journal Article"
    assert metadata.source_uri == "https://pubmed.ncbi.nlm.nih.gov/12345678/"
    assert metadata.published_at == date(2024, 1, 31)
    assert metadata.summary == "This study examines deterministic safety framing inputs."
    assert metadata.journal == "Journal of Applied Safety Science"
    assert metadata.authors == ["Smith J", "Lee A"]
    assert metadata.keywords == ["risk assessment", "exposure"]
    assert [(identifier.namespace, identifier.value) for identifier in metadata.identifiers] == [
        ("pubmed", "12345678"),
        ("doi", "10.1000/cardiovex.2024.01"),
    ]


def test_source_ingestion_service_routes_to_provider_parser():
    payload = {
        "results": [
            {
                "set_id": "ofda-set-999",
                "openfda": {
                    "brand_name": ["Comparator Label"],
                    "product_type": ["HUMAN OTC DRUG"],
                },
            }
        ]
    }
    service = SourceIngestionService()

    metadata = service.parse_metadata(provider="openfda", payload=payload)

    assert metadata.provider == "openfda"
    assert metadata.external_id == "ofda-set-999"
    assert metadata.title == "Comparator Label"


@pytest.mark.parametrize(
    ("provider", "identifier"),
    [
        ("dailymed", "dm-set-123"),
        ("openfda", "ofda-set-456"),
        ("pubmed", "12345678"),
    ],
)
def test_source_ingestion_fetch_is_explicitly_not_implemented(provider, identifier):
    service = SourceIngestionService()

    with pytest.raises(NotImplementedError, match=provider):
        service.fetch_metadata(provider=provider, identifier=identifier)


@pytest.mark.parametrize(
    ("parser", "payload", "expected_error"),
    [
        (
            parse_dailymed_metadata,
            {"data": {"title": "Missing id label"}},
            "dailymed metadata payload did not include a usable external_id.",
        ),
        (
            parse_openfda_metadata,
            {"results": [{"set_id": "ofda-set-456"}]},
            "openfda metadata payload did not include a usable title.",
        ),
        (
            parse_pubmed_metadata,
            {"result": {"uids": ["123"], "123": {"uid": "123"}}},
            "pubmed metadata payload did not include a usable title.",
        ),
    ],
)
def test_metadata_parsers_raise_clear_errors_for_missing_required_fields(
    parser,
    payload,
    expected_error,
):
    with pytest.raises(ValueError, match=expected_error):
        parser(payload)
