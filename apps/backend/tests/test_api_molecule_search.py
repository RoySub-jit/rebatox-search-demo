from __future__ import annotations

from app.schemas.molecule_search import (
    MoleculeDetailResponse,
    MoleculeLabelSection,
    MoleculeSearchResponse,
    MoleculeSearchResult,
)
from app.schemas.source_ingestion import SourceRecordIdentifier


def test_molecule_search_route_returns_results(client, monkeypatch) -> None:
    def fake_search(*, query: str, limit: int = 10) -> MoleculeSearchResponse:
        assert query == "aspirin"
        assert limit == 5
        return MoleculeSearchResponse(
            query=query,
            limit=limit,
            total_results=1,
            items=[
                MoleculeSearchResult(
                    provider="openfda",
                    external_id="set-123",
                    title="Aspirin Label",
                    generic_name="aspirin",
                    brand_names=["Aspirin"],
                    manufacturer_names=["Example Labs"],
                    routes=["ORAL"],
                    substance_names=["ASPIRIN"],
                    product_type="HUMAN OTC DRUG",
                    summary="Used for symptom control.",
                    identifiers=[
                        SourceRecordIdentifier(namespace="set_id", value="set-123")
                    ],
                )
            ],
        )

    monkeypatch.setattr(
        "app.api.routes.molecule_search.search_molecules",
        fake_search,
    )

    response = client.get("/api/v1/molecule-search", params={"q": "aspirin", "limit": 5})

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "aspirin"
    assert payload["items"][0]["external_id"] == "set-123"
    assert payload["items"][0]["brand_names"] == ["Aspirin"]


def test_molecule_detail_route_returns_not_found(client, monkeypatch) -> None:
    def fake_detail(*, provider: str, external_id: str) -> MoleculeDetailResponse:
        raise LookupError(f"No molecule record was found for set id '{external_id}'.")

    monkeypatch.setattr(
        "app.api.routes.molecule_search.get_molecule_detail",
        fake_detail,
    )

    response = client.get("/api/v1/molecule-search/openfda/missing-set")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "molecule_detail_not_found"


def test_molecule_detail_route_returns_payload(client, monkeypatch) -> None:
    def fake_detail(*, provider: str, external_id: str) -> MoleculeDetailResponse:
        assert provider == "openfda"
        assert external_id == "set-123"
        return MoleculeDetailResponse(
            molecule=MoleculeSearchResult(
                provider="openfda",
                external_id="set-123",
                title="Aspirin Label",
                generic_name="aspirin",
                brand_names=["Aspirin"],
                manufacturer_names=["Example Labs"],
                routes=["ORAL"],
                substance_names=["ASPIRIN"],
                product_type="HUMAN OTC DRUG",
                summary="Used for symptom control.",
                identifiers=[
                    SourceRecordIdentifier(namespace="set_id", value="set-123")
                ],
            ),
            sections=[
                MoleculeLabelSection(
                    key="indications_and_usage",
                    title="Indications and usage",
                    content=["Indicated for pain relief."],
                )
            ],
        )

    monkeypatch.setattr(
        "app.api.routes.molecule_search.get_molecule_detail",
        fake_detail,
    )

    response = client.get("/api/v1/molecule-search/openfda/set-123")

    assert response.status_code == 200
    payload = response.json()
    assert payload["molecule"]["title"] == "Aspirin Label"
    assert payload["sections"][0]["key"] == "indications_and_usage"
