from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock
from time import time
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class _CacheEntry(Generic[T]):
    value: T
    expires_at: float


class SimpleTtlCache:
    def __init__(self) -> None:
        self._entries: dict[str, _CacheEntry[object]] = {}
        self._lock = Lock()

    def get(self, key: str) -> object | None:
        now = time()
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None

            if entry.expires_at <= now:
                self._entries.pop(key, None)
                return None

            return entry.value

    def set(self, key: str, value: object, ttl_seconds: int) -> object:
        with self._lock:
            self._entries[key] = _CacheEntry(
                value=value,
                expires_at=time() + max(ttl_seconds, 1),
            )
        return value

    def get_or_set(
        self,
        key: str,
        *,
        ttl_seconds: int,
        loader: Callable[[], T],
    ) -> T:
        cached_value = self.get(key)
        if cached_value is not None:
            return cached_value  # type: ignore[return-value]

        value = loader()
        self.set(key, value, ttl_seconds)
        return value

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


_cache = SimpleTtlCache()


def get_cache() -> SimpleTtlCache:
    return _cache
