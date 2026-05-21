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
