from __future__ import annotations

from urllib.error import HTTPError
from urllib.request import Request

import pytest

from app.services.live_search import pubmed


class _FakeResponse:
    def __init__(self, payload: str) -> None:
        self.payload = payload

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return self.payload.encode("utf-8")


def test_read_pubmed_payload_retries_after_rate_limit(monkeypatch) -> None:
    calls = {"count": 0}

    def fake_urlopen(request: Request, timeout: int):  # noqa: ARG001
        calls["count"] += 1
        if calls["count"] < 3:
            raise HTTPError(
                request.full_url,
                429,
                "Too Many Requests",
                hdrs=None,
                fp=None,
            )
        return _FakeResponse('{"ok": true}')

    monkeypatch.setattr(pubmed, "urlopen", fake_urlopen)
    monkeypatch.setattr(pubmed.time, "sleep", lambda _: None)

    request = Request("https://example.test/pubmed")
    payload = pubmed._read_pubmed_payload(request)

    assert payload == '{"ok": true}'
    assert calls["count"] == 3


def test_read_pubmed_payload_raises_after_retry_exhaustion(monkeypatch) -> None:
    def fake_urlopen(request: Request, timeout: int):  # noqa: ARG001
        raise HTTPError(
            request.full_url,
            429,
            "Too Many Requests",
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr(pubmed, "urlopen", fake_urlopen)
    monkeypatch.setattr(pubmed.time, "sleep", lambda _: None)

    request = Request("https://example.test/pubmed")

    with pytest.raises(RuntimeError, match="PubMed request failed: Too Many Requests"):
        pubmed._read_pubmed_payload(request)


def test_search_pubmed_records_ranks_toxicology_records_above_analytical_method_records(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        pubmed,
        "_fetch_pubmed_ids",
        lambda **_kwargs: ["1", "2"],
    )
    monkeypatch.setattr(
        pubmed,
        "_fetch_pubmed_summary_records",
        lambda _ids: [
            {
                "uid": "1",
                "title": "NDMA impurity in valsartan and other pharmaceutical products: Analytical methods for the determination of N-nitrosamines.",
                "fulljournalname": "Journal of pharmaceutical and biomedical analysis",
                "pubdate": "2019 Feb",
                "authors": [{"name": "Parr MK"}],
            },
            {
                "uid": "2",
                "title": "Toxicological risk assessment of NDMA exposure after repeated oral dosing.",
                "fulljournalname": "Toxicology letters",
                "pubdate": "2021 Jan",
                "authors": [{"name": "Smith J"}],
            },
        ],
    )

    items = pubmed.search_pubmed_records(
        entity_type="degradant",
        query="ndma",
        limit=10,
    )

    assert items[0].external_id == "2"
    assert "Toxicological risk assessment" in items[0].title
