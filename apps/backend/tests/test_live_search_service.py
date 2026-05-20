from __future__ import annotations

from datetime import datetime, timezone

from app.schemas.live_search import (
    LiveSearchResult,
    LiveWorkspaceResponse,
    LiveWorkspaceReviewCue,
    ResolveLiveWorkspaceRequest,
)
from app.schemas.source_ingestion import SourceRecordIdentifier
from app.services.cache import get_cache
from app.services.live_search import service


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
        source_uri=f"https://example.test/{provider}/{external_id}",
        identifiers=[
            SourceRecordIdentifier(namespace=provider, value=external_id),
        ],
    )


def _build_workspace(
    *,
    entity_type: str,
    provider: str,
    external_id: str,
    title: str,
) -> LiveWorkspaceResponse:
    return LiveWorkspaceResponse(
        entity_type=entity_type,  # type: ignore[arg-type]
        query="aspirin",
        record=_build_result(
            entity_type=entity_type,
            provider=provider,
            external_id=external_id,
            title=title,
        ),
        sections=[],
        review_cue=LiveWorkspaceReviewCue(
            title="Live review",
            description="Use this record to review the source evidence.",
        ),
        retrieved_at=datetime(2026, 5, 8, tzinfo=timezone.utc),
    )


def setup_function() -> None:
    get_cache().clear()


def test_search_live_records_returns_mixed_source_results(monkeypatch) -> None:
    def fake_openfda(*, entity_type: str, query: str, limit: int):
        assert entity_type == "molecule"
        assert query == "aspirin"
        assert limit == 2
        return [
            _build_result(
                entity_type="molecule",
                provider="openfda",
                external_id="set-1",
                title="Aspirin Label",
            )
        ]

    def fake_dailymed(*, entity_type: str, query: str, limit: int):
        assert entity_type == "molecule"
        assert query == "aspirin"
        assert limit == 2
        return [
            _build_result(
                entity_type="molecule",
                provider="dailymed",
                external_id="dm-set-1",
                title="Aspirin 325 mg",
            )
        ]

    def fake_pubmed(*, entity_type: str, query: str, limit: int):
        assert entity_type == "molecule"
        assert query == "aspirin"
        assert limit == 2
        return [
            _build_result(
                entity_type="molecule",
                provider="pubmed",
                external_id="12345",
                title="Aspirin review article",
            )
        ]

    monkeypatch.setattr(service, "search_openfda_records", fake_openfda)
    monkeypatch.setattr(service, "search_dailymed_records", fake_dailymed)
    monkeypatch.setattr(service, "search_pubmed_records", fake_pubmed)

    response = service.search_live_records(
        entity_type="molecule",
        query="aspirin",
        limit=6,
    )

    assert response.entity_type == "molecule"
    assert response.sources == ["openfda", "dailymed", "pubmed"]
    assert response.total_results == 3
    assert [item.provider for item in response.items] == [
        "openfda",
        "dailymed",
        "pubmed",
    ]


def test_search_live_records_returns_empty_response_when_no_source_hits(
    monkeypatch,
) -> None:
    monkeypatch.setattr(service, "search_pubmed_records", lambda **_: [])

    response = service.search_live_records(
        entity_type="degradant",
        query="ndma",
        limit=5,
    )

    assert response.entity_type == "degradant"
    assert response.sources == ["pubmed"]
    assert response.total_results == 0
    assert response.items == []


def test_search_live_records_uses_cache(monkeypatch) -> None:
    calls = {"count": 0}

    def fake_pubmed(**_: object):
        calls["count"] += 1
        return [
            _build_result(
                entity_type="el",
                provider="pubmed",
                external_id="pm-1",
                title="Packaging migrant review",
            )
        ]

    monkeypatch.setattr(service, "search_pubmed_records", fake_pubmed)

    first = service.search_live_records(entity_type="el", query="bisphenol a", limit=4)
    second = service.search_live_records(entity_type="el", query="bisphenol a", limit=4)

    assert calls["count"] == 1
    assert first.items[0].external_id == second.items[0].external_id


def test_resolve_live_workspace_routes_to_provider(monkeypatch) -> None:
    def fake_pubmed(*, entity_type: str, external_id: str, query: str | None):
        assert entity_type == "degradant"
        assert external_id == "98765"
        assert query == "ndma"
        return _build_workspace(
            entity_type="degradant",
            provider="pubmed",
            external_id="98765",
            title="NDMA degradant signal",
        )

    monkeypatch.setattr(service, "resolve_pubmed_workspace", fake_pubmed)

    workspace = service.resolve_live_workspace(
        ResolveLiveWorkspaceRequest(
            entity_type="degradant",
            provider="pubmed",
            external_id="98765",
            query="ndma",
        )
    )

    assert workspace.entity_type == "degradant"
    assert workspace.record.provider == "pubmed"
    assert workspace.record.title == "NDMA degradant signal"


def test_resolve_live_workspace_routes_to_dailymed(monkeypatch) -> None:
    def fake_dailymed(*, entity_type: str, external_id: str, query: str | None):
        assert entity_type == "molecule"
        assert external_id == "dm-set-1"
        assert query == "aspirin"
        return _build_workspace(
            entity_type="molecule",
            provider="dailymed",
            external_id="dm-set-1",
            title="Aspirin 325 mg",
        )

    monkeypatch.setattr(service, "resolve_dailymed_workspace", fake_dailymed)

    workspace = service.resolve_live_workspace(
        ResolveLiveWorkspaceRequest(
            entity_type="molecule",
            provider="dailymed",
            external_id="dm-set-1",
            query="aspirin",
        )
    )

    assert workspace.entity_type == "molecule"
    assert workspace.record.provider == "dailymed"
    assert workspace.record.title == "Aspirin 325 mg"
