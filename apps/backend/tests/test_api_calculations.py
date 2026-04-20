from __future__ import annotations

from decimal import Decimal


def test_run_calculation_returns_created_run_for_direct_calculator(client):
    response = client.post(
        "/api/v1/calculations/run",
        json={
            "run_type": "mg_per_kg_day_to_mg_per_day",
            "inputs": {
                "dose_mg_per_kg_day": "2.5",
                "body_weight_kg": "70",
            },
        },
    )

    assert response.status_code == 201

    payload = response.json()
    assert payload["id"] == 1
    assert payload["run_type"] == "mg_per_kg_day_to_mg_per_day"
    assert payload["status"] == "ok"
    assert payload["inputs"] == {
        "dose_mg_per_kg_day": "2.5",
        "body_weight_kg": "70",
    }
    assert payload["output"]["calculator"] == "mg_per_kg_day_to_mg_per_day"
    assert payload["output"]["status"] == "ok"
    assert Decimal(payload["output"]["result"]["value"]) == Decimal("175.0")
    assert payload["output"]["result"]["unit"] == "mg/day"
    assert payload["started_at"]
    assert payload["completed_at"]
    assert payload["created_at"]
    assert payload["updated_at"]


def test_run_calculation_returns_created_run_for_pde_shell(client):
    product_response = client.post(
        "/api/v1/products",
        json={
            "name": "Example Product",
            "slug": "example-product",
        },
    )
    product_id = product_response.json()["id"]

    response = client.post(
        "/api/v1/calculations/run",
        json={
            "run_type": "pde",
            "product_id": product_id,
            "inputs": {
                "point_of_departure_mg_per_kg_day": "5",
                "body_weight_kg": "50",
                "modifying_factor_f1": "2",
                "modifying_factor_f2": "5",
                "modifying_factor_f3": "10",
                "modifying_factor_f4": "1",
                "modifying_factor_f5": "1",
                "point_of_departure_label": "NOAEL",
                "result_unit": "mg/day",
            },
        },
    )

    assert response.status_code == 201

    payload = response.json()
    assert payload["run_type"] == "pde"
    assert payload["product_id"] == product_id
    assert payload["status"] == "ok"
    assert payload["output"]["calculator"] == "pde_calculator_shell"
    assert Decimal(payload["output"]["result"]["value"]) == Decimal("2.5")
    assert Decimal(payload["output"]["result"]["composite_modifying_factor"]) == Decimal(
        "100"
    )
    assert payload["output"]["result"]["point_of_departure_label"] == "NOAEL"


def test_run_calculation_returns_bad_request_and_does_not_persist_invalid_input(client):
    response = client.post(
        "/api/v1/calculations/run",
        json={
            "run_type": "margin_of_exposure",
            "inputs": {
                "point_of_departure": "100",
                "exposure": "0",
                "basis": "mg/kg/day",
            },
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": {
            "code": "calculation_invalid",
            "message": "Exposure must be greater than 0 to calculate margin of exposure.",
        }
    }

    get_response = client.get("/api/v1/calculations/1")
    assert get_response.status_code == 404


def test_run_calculation_returns_not_found_for_missing_linked_resource(client):
    response = client.post(
        "/api/v1/calculations/run",
        json={
            "run_type": "mg_per_day_to_mg_per_kg_day",
            "product_id": 999,
            "inputs": {
                "dose_mg_per_day": "100",
                "body_weight_kg": "50",
            },
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "code": "product_not_found",
            "message": "Product with id 999 was not found.",
        }
    }


def test_get_calculation_returns_persisted_run(client):
    create_response = client.post(
        "/api/v1/calculations/run",
        json={
            "run_type": "ade",
            "inputs": {
                "point_of_departure_mg_per_kg_day": "0.6",
                "body_weight_kg": "50",
                "modifying_factor_f1": "1",
                "modifying_factor_f2": "1",
                "modifying_factor_f3": "1",
                "modifying_factor_f4": "1",
                "modifying_factor_f5": "1",
                "point_of_departure_label": "POD",
                "result_unit": "mg/day",
            },
        },
    )
    calculation_id = create_response.json()["id"]

    response = client.get(f"/api/v1/calculations/{calculation_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == calculation_id
    assert payload["run_type"] == "ade"
    assert payload["status"] == "warning"
    assert payload["output"]["calculator"] == "ade_calculator_shell"
    assert payload["output"]["warnings"] == [
        "All modifying factors are 1, so no uncertainty adjustment has been applied."
    ]
    assert Decimal(payload["output"]["result"]["value"]) == Decimal("30.0")


def test_get_calculation_returns_not_found_for_missing_id(client):
    response = client.get("/api/v1/calculations/999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "code": "calculation_run_not_found",
            "message": "Calculation run with id 999 was not found.",
        }
    }
