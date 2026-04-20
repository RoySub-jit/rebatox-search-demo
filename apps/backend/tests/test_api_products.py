from __future__ import annotations


def test_create_product_returns_created_product(client):
    response = client.post(
        "/api/v1/products",
        json={
            "name": "Acetaminophen",
            "slug": "acetaminophen",
            "manufacturer": "Example Labs",
            "description": "Analgesic product",
        },
    )

    assert response.status_code == 201

    payload = response.json()
    assert payload["id"] == 1
    assert payload["name"] == "Acetaminophen"
    assert payload["slug"] == "acetaminophen"
    assert payload["manufacturer"] == "Example Labs"
    assert payload["description"] == "Analgesic product"
    assert payload["created_at"]
    assert payload["updated_at"]


def test_create_product_returns_conflict_for_duplicate_slug(client):
    first_response = client.post(
        "/api/v1/products",
        json={
            "name": "Acetaminophen",
            "slug": "acetaminophen",
        },
    )
    assert first_response.status_code == 201

    second_response = client.post(
        "/api/v1/products",
        json={
            "name": "Acetaminophen Extended Release",
            "slug": "acetaminophen",
        },
    )

    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": {
            "code": "product_slug_conflict",
            "message": "Product slug 'acetaminophen' already exists.",
        }
    }


def test_get_product_returns_product_by_id(client):
    create_response = client.post(
        "/api/v1/products",
        json={
            "name": "Ibuprofen",
            "slug": "ibuprofen",
        },
    )
    product_id = create_response.json()["id"]

    response = client.get(f"/api/v1/products/{product_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == product_id
    assert payload["name"] == "Ibuprofen"
    assert payload["slug"] == "ibuprofen"


def test_get_product_returns_not_found_for_missing_id(client):
    response = client.get("/api/v1/products/999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "code": "product_not_found",
            "message": "Product with id 999 was not found.",
        }
    }
