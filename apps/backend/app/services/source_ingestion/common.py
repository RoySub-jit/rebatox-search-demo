from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date, datetime
from typing import Any

from app.schemas.source_ingestion import SourceRecordIdentifier


def first_text(value: Any) -> str | None:
    if value is None:
        return None

    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None

    if isinstance(value, Mapping):
        for key in ("name", "title", "value", "text"):
            nested = first_text(value.get(key))
            if nested is not None:
                return nested
        return None

    if isinstance(value, Iterable) and not isinstance(value, bytes):
        for item in value:
            nested = first_text(item)
            if nested is not None:
                return nested

    return None


def text_list(value: Any) -> list[str]:
    if value is None:
        return []

    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []

    if isinstance(value, Mapping):
        nested = first_text(value)
        return [nested] if nested is not None else []

    if isinstance(value, Iterable) and not isinstance(value, bytes):
        items: list[str] = []
        for item in value:
            items.extend(text_list(item))
        return dedupe_texts(items)

    return []


def mapping_list(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        return [value]

    if isinstance(value, list):
        return [item for item in value if isinstance(item, Mapping)]

    return []


def dedupe_texts(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []

    for value in values:
        stripped = value.strip()
        if not stripped or stripped in seen:
            continue

        seen.add(stripped)
        deduped.append(stripped)

    return deduped


def dedupe_identifiers(
    identifiers: list[SourceRecordIdentifier],
) -> list[SourceRecordIdentifier]:
    seen: set[tuple[str, str]] = set()
    deduped: list[SourceRecordIdentifier] = []

    for identifier in identifiers:
        key = (identifier.namespace, identifier.value)
        if key in seen:
            continue

        seen.add(key)
        deduped.append(identifier)

    return deduped


def parse_date_value(value: Any) -> date | None:
    text_value = first_text(value)
    if text_value is None:
        return None

    candidate = text_value
    if "T" in candidate:
        try:
            return datetime.fromisoformat(candidate.replace("Z", "+00:00")).date()
        except ValueError:
            pass

    if " " in candidate and "/" in candidate:
        candidate = candidate.split(" ", maxsplit=1)[0]

    for date_format in (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y%m%d",
        "%Y %b %d",
        "%Y %B %d",
        "%Y %b",
        "%Y %B",
        "%Y",
    ):
        try:
            return datetime.strptime(candidate, date_format).date()
        except ValueError:
            continue

    return None


def build_identifier(namespace: str, value: Any) -> SourceRecordIdentifier | None:
    text_value = first_text(value)
    if text_value is None:
        return None

    return SourceRecordIdentifier(namespace=namespace, value=text_value)


def require_metadata_field(value: str | None, *, provider: str, field_name: str) -> str:
    if value is None:
        raise ValueError(
            f"{provider} metadata payload did not include a usable {field_name}."
        )

    return value
