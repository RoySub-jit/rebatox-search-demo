from __future__ import annotations


def _workspace_payload() -> dict[str, object]:
    return {
        "workspace": {
            "entity_type": "molecule",
            "query": "aspirin",
            "record": {
                "entity_type": "molecule",
                "provider": "dailymed",
                "external_id": "dm-set-1",
                "title": "Aspirin 325 mg",
                "subtitle": "drug_label",
                "summary": "Used to reduce fever and relieve minor aches.",
                "document_type": "drug_label",
                "published_at": "2026-05-08",
                "source_uri": "https://example.test/dailymed/dm-set-1",
                "identifiers": [
                    {"namespace": "setid", "value": "dm-set-1"},
                ],
                "generic_name": "aspirin",
                "brand_names": ["Aspirin"],
                "manufacturer_names": ["Example Labs"],
                "routes": ["ORAL"],
                "substance_names": ["aspirin"],
                "product_type": "drug_label",
                "authors": [],
                "journal": None,
                "keywords": [],
            },
            "sections": [
                {
                    "key": "uses",
                    "title": "Uses",
                    "content": ["Used to reduce fever and relieve minor aches."],
                }
            ],
            "extracted_signals": [
                {
                    "key": "route",
                    "label": "Route",
                    "value": "ORAL",
                    "source_section_key": None,
                    "confidence": "high",
                }
            ],
            "review_cue": {
                "title": "DailyMed label review",
                "description": "Review this label before moving into broader assessment.",
            },
            "retrieval_mode": "live",
            "retrieved_at": "2026-05-08T00:00:00Z",
        }
    }


def test_save_workspace_roundtrip(client) -> None:
    create_response = client.post(
        "/api/v1/workspaces/save",
        json=_workspace_payload(),
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["label"] == "Aspirin 325 mg"
    assert created["workspace"]["record"]["provider"] == "dailymed"
    assert created["workspace"]["extracted_signals"][0]["key"] == "route"

    fetch_response = client.get(f"/api/v1/workspaces/{created['id']}")

    assert fetch_response.status_code == 200
    fetched = fetch_response.json()
    assert fetched["id"] == created["id"]
    assert fetched["workspace"]["query"] == "aspirin"
    assert fetched["workspace"]["sections"][0]["key"] == "uses"


def test_get_saved_workspace_returns_not_found(client) -> None:
    response = client.get("/api/v1/workspaces/999")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "saved_workspace_not_found"
