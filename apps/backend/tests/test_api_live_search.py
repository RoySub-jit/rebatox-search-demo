from __future__ import annotations

from datetime import datetime, timezone

from app.schemas.live_search import (
    LiveSearchResponse,
    LiveSearchResult,
    LiveWorkspaceResponse,
    LiveWorkspaceReviewCue,
)
from app.schemas.source_ingestion import SourceRecordIdentifier


def _build_result(
    *,
    entity_type: str,
    provider: str,
    external_id: str,
    title: str,
) -> LiveSearchResult:
    return LiveSearchResult(
        entity_type=entity_type,  # type: ignore[arg-type]
        provider=provider,  # type: ignore[arg-type]
        external_id=external_id,
        title=title,
        identifiers=[
            SourceRecordIdentifier(namespace=provider, value=external_id),
        ],
    )


def test_live_search_route_returns_mixed_results(client, monkeypatch) -> None:
    def fake_search(
        *,
        entity_type: str,
        query: str,
        limit: int,
        requested_sources,
    ) -> LiveSearchResponse:
        assert entity_type == "molecule"
        assert query == "aspirin"
        assert limit == 6
        assert requested_sources is None
        return LiveSearchResponse(
            entity_type="molecule",
            query=query,
            sources=["openfda", "dailymed", "pubmed"],
            limit=limit,
            total_results=3,
            items=[
                _build_result(
                    entity_type="molecule",
                    provider="openfda",
                    external_id="set-1",
                    title="Aspirin Label",
                ),
                _build_result(
                    entity_type="molecule",
                    provider="dailymed",
                    external_id="dm-set-1",
                    title="Aspirin 325 mg",
                ),
                _build_result(
                    entity_type="molecule",
                    provider="pubmed",
                    external_id="12345",
                    title="Aspirin literature note",
                ),
            ],
        )

    monkeypatch.setattr("app.api.routes.search.search_live_records", fake_search)

    response = client.get(
        "/api/v1/search",
        params={"entity_type": "molecule", "q": "aspirin", "limit": 6},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["sources"] == ["openfda", "dailymed", "pubmed"]
    assert payload["items"][1]["provider"] == "dailymed"
    assert payload["items"][2]["provider"] == "pubmed"


def test_live_search_route_returns_error_for_invalid_source(client) -> None:
    response = client.get(
        "/api/v1/search",
        params={
            "entity_type": "degradant",
            "q": "ndma",
            "sources": "openfda",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "live_search_invalid_request"


def test_live_workspace_resolve_route_returns_payload(client, monkeypatch) -> None:
    def fake_resolve(request) -> LiveWorkspaceResponse:
        assert request.entity_type == "el"
        assert request.provider == "pubmed"
        assert request.external_id == "11111"
        return LiveWorkspaceResponse(
            entity_type="el",
            query=request.query,
            record=_build_result(
                entity_type="el",
                provider="pubmed",
                external_id="11111",
                title="Leachables literature signal",
            ),
            sections=[],
            review_cue=LiveWorkspaceReviewCue(
                title="Literature-backed evidence review",
                description="Review the live source result before saving it.",
            ),
            retrieved_at=datetime(2026, 5, 8, tzinfo=timezone.utc),
        )

    monkeypatch.setattr(
        "app.api.routes.workspaces.resolve_live_workspace",
        fake_resolve,
    )

    response = client.post(
        "/api/v1/workspaces/resolve",
        json={
            "entity_type": "el",
            "provider": "pubmed",
            "external_id": "11111",
            "query": "bisphenol a",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["record"]["title"] == "Leachables literature signal"
    assert payload["review_cue"]["title"] == "Literature-backed evidence review"


def test_live_workspace_resolve_route_supports_dailymed(client, monkeypatch) -> None:
    def fake_resolve(request) -> LiveWorkspaceResponse:
        assert request.entity_type == "molecule"
        assert request.provider == "dailymed"
        assert request.external_id == "dm-set-1"
        return LiveWorkspaceResponse(
            entity_type="molecule",
            query=request.query,
            record=_build_result(
                entity_type="molecule",
                provider="dailymed",
                external_id="dm-set-1",
                title="Aspirin 325 mg",
            ),
            sections=[],
            review_cue=LiveWorkspaceReviewCue(
                title="DailyMed label review",
                description="Review the live label before saving it.",
            ),
            retrieved_at=datetime(2026, 5, 8, tzinfo=timezone.utc),
        )

    monkeypatch.setattr(
        "app.api.routes.workspaces.resolve_live_workspace",
        fake_resolve,
    )

    response = client.post(
        "/api/v1/workspaces/resolve",
        json={
            "entity_type": "molecule",
            "provider": "dailymed",
            "external_id": "dm-set-1",
            "query": "aspirin",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["record"]["provider"] == "dailymed"
    assert payload["review_cue"]["title"] == "DailyMed label review"


def test_live_workspace_resolve_route_returns_not_found(client, monkeypatch) -> None:
    def fake_resolve(request):
        raise LookupError(f"No record was found for {request.external_id}.")

    monkeypatch.setattr(
        "app.api.routes.workspaces.resolve_live_workspace",
        fake_resolve,
    )

    response = client.post(
        "/api/v1/workspaces/resolve",
        json={
            "entity_type": "molecule",
            "provider": "openfda",
            "external_id": "missing-id",
            "query": "aspirin",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "live_workspace_not_found"
