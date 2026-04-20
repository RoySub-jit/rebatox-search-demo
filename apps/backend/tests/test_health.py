from __future__ import annotations


def test_health_endpoint_returns_application_status(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["service"] == "Spatial Platform API"
    assert payload["version"] == "0.1.0"
    assert payload["environment"] == "test"
    assert payload["database"]["ok"] is True
