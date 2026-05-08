from __future__ import annotations

from app.services import molecule_search


def test_search_molecules_normalizes_openfda_results(
    monkeypatch,
) -> None:
    def fake_fetch(_: dict[str, str]) -> dict[str, object]:
        return {
            "meta": {"results": {"total": 2}},
            "results": [
                {
                    "set_id": "alpha-set",
                    "effective_time": "20240115",
                    "purpose": ["Used for maintenance therapy."],
                    "openfda": {
                        "brand_name": ["AlphaRelief"],
                        "generic_name": ["aspirin"],
                        "manufacturer_name": ["Example Labs"],
                        "route": ["ORAL"],
                        "substance_name": ["ASPIRIN"],
                        "product_type": ["HUMAN PRESCRIPTION DRUG"],
                        "spl_set_id": ["alpha-set"],
                    },
                },
                {
                    "set_id": "alpha-set",
                    "effective_time": "20240115",
                    "purpose": ["Duplicate record should be removed."],
                    "openfda": {
                        "brand_name": ["AlphaRelief"],
                        "generic_name": ["aspirin"],
                        "manufacturer_name": ["Example Labs"],
                        "route": ["ORAL"],
                        "substance_name": ["ASPIRIN"],
                        "product_type": ["HUMAN PRESCRIPTION DRUG"],
                        "spl_set_id": ["alpha-set"],
                    },
                },
            ],
        }

    monkeypatch.setattr(molecule_search, "_fetch_openfda_payload", fake_fetch)

    response = molecule_search.search_molecules(query="aspirin", limit=10)

    assert response.query == "aspirin"
    assert response.total_results == 1
    assert len(response.items) == 1
    assert response.items[0].external_id == "alpha-set"
    assert response.items[0].generic_name == "aspirin"
    assert response.items[0].routes == ["ORAL"]
    assert response.items[0].manufacturer_names == ["Example Labs"]


def test_get_molecule_detail_builds_label_sections(monkeypatch) -> None:
    def fake_fetch(_: dict[str, str]) -> dict[str, object]:
        return {
            "results": [
                {
                    "set_id": "beta-set",
                    "effective_time": "20240302",
                    "purpose": ["Provides symptom control."],
                    "indications_and_usage": ["Indicated for symptom control."],
                    "warnings_and_cautions": ["Monitor liver enzymes."],
                    "openfda": {
                        "brand_name": ["BetaThera"],
                        "generic_name": ["ibuprofen"],
                        "manufacturer_name": ["Safety Pharma"],
                        "route": ["ORAL"],
                        "substance_name": ["IBUPROFEN"],
                        "product_type": ["HUMAN OTC DRUG"],
                        "spl_set_id": ["beta-set"],
                    },
                }
            ]
        }

    monkeypatch.setattr(molecule_search, "_fetch_openfda_payload", fake_fetch)

    response = molecule_search.get_molecule_detail(
        provider="openfda",
        external_id="beta-set",
    )

    assert response.molecule.external_id == "beta-set"
    assert response.molecule.brand_names == ["BetaThera"]
    assert [section.key for section in response.sections] == [
        "purpose",
        "indications_and_usage",
        "warnings_and_cautions",
    ]


def test_get_molecule_detail_rejects_unsupported_providers() -> None:
    try:
        molecule_search.get_molecule_detail(provider="pubmed", external_id="12345")
    except ValueError as exc:
        assert "not yet supported" in str(exc)
    else:
        raise AssertionError("Expected unsupported provider lookup to fail.")
