from __future__ import annotations


def _build_saved_workspace_payload(
    *,
    title: str = "Aspirin workspace",
    external_id: str = "set-123",
    query: str | None = "aspirin",
) -> dict:
    return {
        "label": title,
        "notes": "Saved for stewardship review.",
        "workspace": {
            "entity_type": "molecule",
            "query": query,
            "record": {
                "entity_type": "molecule",
                "provider": "openfda",
                "external_id": external_id,
                "title": title,
                "subtitle": None,
                "summary": "Label-backed molecule workspace for review.",
                "document_type": "HUMAN OTC DRUG",
                "published_at": "2026-05-08",
                "source_uri": None,
                "identifiers": [
                    {"namespace": "set_id", "value": external_id},
                ],
                "generic_name": "aspirin",
                "brand_names": ["Aspirin"],
                "manufacturer_names": ["Example Labs"],
                "routes": ["ORAL"],
                "substance_names": ["ASPIRIN"],
                "product_type": "HUMAN OTC DRUG",
                "authors": [],
                "journal": None,
                "keywords": [],
            },
            "sections": [
                {
                    "key": "warnings",
                    "title": "Warnings",
                    "content": ["Use as directed."],
                }
            ],
            "extracted_signals": [
                {
                    "key": "route_signal",
                    "label": "Route",
                    "value": "ORAL",
                    "source_section_key": "warnings",
                    "confidence": "medium",
                }
            ],
            "review_cue": {
                "title": "Live review",
                "description": "Use this record to review the source evidence.",
            },
            "retrieval_mode": "live",
            "retrieved_at": "2026-05-08T00:00:00Z",
        },
    }


def test_save_workspace_route_persists_snapshot_and_returns_payload(client) -> None:
    response = client.post(
        "/api/v1/workspaces/save",
        json=_build_saved_workspace_payload(),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] == 1
    assert payload["label"] == "Aspirin workspace"
    assert payload["workspace"]["record"]["external_id"] == "set-123"
    assert payload["workspace"]["pod_worksheet"]["body_weight_kg"] == 50.0
    assert payload["workspace"]["pod_worksheet"]["uncertainty_factor"] == 100.0


def test_list_saved_workspaces_route_returns_recent_summaries(client) -> None:
    client.post(
        "/api/v1/workspaces/save",
        json=_build_saved_workspace_payload(
            title="Aspirin workspace",
            external_id="set-123",
            query="aspirin",
        ),
    )
    client.post(
        "/api/v1/workspaces/save",
        json=_build_saved_workspace_payload(
            title="Ibuprofen workspace",
            external_id="set-456",
            query="ibuprofen",
        ),
    )

    response = client.get("/api/v1/workspaces", params={"limit": 10})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_results"] == 2
    assert payload["items"][0]["label"] == "Ibuprofen workspace"
    assert payload["items"][0]["record_title"] == "Ibuprofen workspace"
    assert payload["items"][0]["extracted_signal_count"] == 1
    assert payload["items"][0]["section_count"] == 1
    assert payload["items"][1]["label"] == "Aspirin workspace"


def test_get_saved_workspace_route_returns_not_found(client) -> None:
    response = client.get("/api/v1/workspaces/999")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "saved_workspace_not_found"


def test_update_saved_workspace_route_persists_worksheet_state(client) -> None:
    save_response = client.post(
        "/api/v1/workspaces/save",
        json=_build_saved_workspace_payload(),
    )
    saved_id = save_response.json()["id"]
    saved_workspace = save_response.json()["workspace"]
    saved_workspace["pod_analysis"] = {
        "primary_candidate": {
            "dose_text": "5 mg/day",
            "dose_value": 5.0,
            "unit": "mg/day",
            "normalized_mg_per_kg_day": 0.1,
            "normalization_note": "Converted from mg/day to mg/kg/day using a 50 kg screening body weight.",
            "pod_term": "NOAEL",
            "species": "rat",
            "route": "oral",
            "duration": "28 days",
            "sentence": "A NOAEL of 5 mg/day was reported after 28 days of oral rat dosing.",
            "confidence": "high",
        },
        "candidates": [
            {
                "dose_text": "5 mg/day",
                "dose_value": 5.0,
                "unit": "mg/day",
                "normalized_mg_per_kg_day": 0.1,
                "normalization_note": "Converted from mg/day to mg/kg/day using a 50 kg screening body weight.",
                "pod_term": "NOAEL",
                "species": "rat",
                "route": "oral",
                "duration": "28 days",
                "sentence": "A NOAEL of 5 mg/day was reported after 28 days of oral rat dosing.",
                "confidence": "high",
            }
        ],
        "derived_calculations": [],
        "warnings": [],
    }
    saved_workspace["pod_worksheet"] = {
        "selected_candidate_index": 0,
        "body_weight_kg": 60.0,
        "uncertainty_factor": 30.0,
        "use_human_equivalent_dose": True,
        "reviewer_status": "reviewed",
        "reviewer_notes": "Promising candidate for initial stewardship curation.",
    }

    response = client.put(
        f"/api/v1/workspaces/{saved_id}",
        json={
            "label": "Reviewed aspirin workspace",
            "notes": "Updated after POD worksheet review.",
            "workspace": saved_workspace,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["label"] == "Reviewed aspirin workspace"
    assert payload["notes"] == "Updated after POD worksheet review."
    assert payload["workspace"]["pod_worksheet"]["body_weight_kg"] == 60.0
    assert payload["workspace"]["pod_worksheet"]["uncertainty_factor"] == 30.0
    assert payload["workspace"]["pod_worksheet"]["reviewer_status"] == "reviewed"
    assert (
        payload["workspace"]["pod_worksheet"]["reviewer_notes"]
        == "Promising candidate for initial stewardship curation."
    )
    assert payload["workspace"]["pod_worksheet"]["selected_basis_mg_per_kg_day"] == 0.016216216216216217
    assert payload["workspace"]["pod_worksheet"]["screening_intake_mg_day"] == 0.972972972972973
