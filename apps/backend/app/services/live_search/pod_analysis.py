from __future__ import annotations

import re
from collections.abc import Iterable

from app.schemas.live_search import (
    LiveSearchResult,
    LiveWorkspaceDerivedCalculation,
    LiveWorkspaceDoseCandidate,
    LiveWorkspaceExtractedSignal,
    LiveWorkspacePodAnalysis,
    LiveWorkspaceSection,
)

DOSE_PATTERN = re.compile(
    r"\b(?P<value>\d+(?:\.\d+)?)\s?(?P<unit>mg/kg/day|mg/kg|mg/day|mg/L|mg|ug/kg/day|ug/kg|µg/kg/day|µg/kg|ng/mL|ug/mL|µg/mL|uM|μM|nM|mM)\b",
    re.IGNORECASE,
)
POD_TERM_PATTERN = re.compile(
    r"\b(?:NOAEL|LOAEL|NOEL|LOEL|BMDL|BMD|MTD|point of departure|POD)\b",
    re.IGNORECASE,
)
ROUTE_PATTERN = re.compile(
    r"\b(oral|oral gavage|intravenous|i\.?v\.?|intraperitoneal|i\.?p\.?|subcutaneous|s\.?c\.?|inhalation|intratracheal|topical|dermal|intranasal|p\.?o\.?)\b",
    re.IGNORECASE,
)
DURATION_PATTERN = re.compile(
    r"\b(?:for\s+)?(\d+(?:\.\d+)?)\s?(?:-|)?\s?(day|days|week|weeks|month|months|year|years)\b",
    re.IGNORECASE,
)

SPECIES_PATTERNS: dict[str, tuple[str, ...]] = {
    "mouse": (" mouse ", " mice ", " murine ", " c57bl/6 ", " balb/c "),
    "rat": (" rat ", " rats ", " rodent ", " sprague-dawley ", " wistar "),
    "rabbit": (" rabbit ", " rabbits "),
    "dog": (" dog ", " dogs ", " canine ", " beagle "),
    "monkey": (" monkey ", " monkeys ", " macaque ", " primate ", " cynomolgus "),
    "human": (" human ", " humans ", " patient ", " patients ", " healthy volunteer ", " healthy volunteers "),
}

POD_PRIORITY: dict[str, int] = {
    "NOAEL": 7,
    "NOEL": 6,
    "BMDL": 5,
    "BMD": 4,
    "LOAEL": 3,
    "LOEL": 2,
    "MTD": 1,
    "POD": 0,
}

KM_FACTORS: dict[str, float] = {
    "mouse": 3.0,
    "rat": 6.0,
    "rabbit": 12.0,
    "dog": 20.0,
    "monkey": 12.0,
    "human": 37.0,
}
HUMAN_KM_FACTOR = 37.0


def _normalize_text(value: str | None) -> str:
    return f" {value.casefold()} " if value else " "


def _detect_species(sentence: str) -> str | None:
    haystack = _normalize_text(sentence)
    for label, tokens in SPECIES_PATTERNS.items():
        if any(token in haystack for token in tokens):
            return label
    return None


def _detect_route(sentence: str) -> str | None:
    match = ROUTE_PATTERN.search(sentence)
    if match is None:
        return None

    value = match.group(1).casefold().replace(".", "")
    return {
        "iv": "intravenous",
        "ip": "intraperitoneal",
        "sc": "subcutaneous",
        "po": "oral",
    }.get(value, value)


def _detect_duration(sentence: str) -> str | None:
    match = DURATION_PATTERN.search(sentence)
    if match is None:
        return None
    return f"{match.group(1)} {match.group(2)}"


def _normalize_pod_term(value: str | None) -> str | None:
    if value is None:
        return None
    upper_value = value.upper()
    if upper_value in {"NOAEL", "NOEL", "LOAEL", "LOEL", "BMD", "BMDL", "MTD", "POD"}:
        return upper_value
    if upper_value == "POINT OF DEPARTURE":
        return "POD"
    return value.title()


def _normalize_unit(unit: str | None) -> str | None:
    if unit is None:
        return None
    return (
        unit.casefold()
        .replace("μ", "µ")
        .replace("ug", "µg")
        .replace(" ", "")
    )


def _normalize_mg_per_kg_day(
    *,
    value: float | None,
    unit: str | None,
) -> tuple[float | None, str | None]:
    if value is None or unit is None:
        return None, None

    normalized_unit = _normalize_unit(unit)
    if normalized_unit == "mg/kg/day":
        return value, "Direct mg/kg/day basis from the source text."
    if normalized_unit == "µg/kg/day":
        return value / 1000.0, "Converted from µg/kg/day to mg/kg/day."
    if normalized_unit == "mg/day":
        return value / 50.0, "Converted from mg/day to mg/kg/day using a 50 kg screening body weight."

    return None, None


def _confidence_for_candidate(
    *,
    pod_term: str | None,
    unit: str,
    species: str | None,
    route: str | None,
    duration: str | None,
    normalized_mg_per_kg_day: float | None,
) -> str:
    normalized_unit = _normalize_unit(unit) or unit.lower()
    if pod_term and normalized_mg_per_kg_day is not None and species and route:
        return "high"
    if pod_term and normalized_mg_per_kg_day is not None:
        return "high"
    if pod_term or species or route or duration or normalized_unit in {"mg/kg/day", "mg/day", "µg/kg/day"}:
        return "medium"
    return "low"


def _candidate_sort_key(candidate: LiveWorkspaceDoseCandidate) -> tuple[int, int, float]:
    priority = POD_PRIORITY.get(candidate.pod_term or "", -1)
    normalized_unit = _normalize_unit(candidate.unit)
    unit_score = (
        3
        if candidate.normalized_mg_per_kg_day is not None
        else 2
        if normalized_unit == "mg/kg/day"
        else 1
        if normalized_unit == "mg/kg"
        else 0
    )
    confidence_score = {"high": 2.0, "medium": 1.0, "low": 0.0}[candidate.confidence]
    richness_score = (
        (1.0 if candidate.species else 0.0)
        + (1.0 if candidate.route else 0.0)
        + (0.5 if candidate.duration else 0.0)
    )
    return (priority, unit_score, confidence_score + richness_score)


def _iter_candidate_sentences(
    *,
    sections: Iterable[LiveWorkspaceSection],
    extracted_signals: Iterable[LiveWorkspaceExtractedSignal],
) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()

    for section in sections:
        for paragraph in section.content:
            sentence = " ".join(paragraph.split())
            if sentence and sentence not in seen:
                seen.add(sentence)
                values.append(sentence)

    for signal in extracted_signals:
        sentence = " ".join(signal.value.split())
        if sentence and sentence not in seen:
            seen.add(sentence)
            values.append(sentence)

    return values


def _build_candidates(
    *,
    record: LiveSearchResult,
    sections: list[LiveWorkspaceSection],
    extracted_signals: list[LiveWorkspaceExtractedSignal],
) -> list[LiveWorkspaceDoseCandidate]:
    route_fallback = record.routes[0].lower() if record.routes else None
    candidates: list[LiveWorkspaceDoseCandidate] = []
    seen: set[tuple[str, str, str | None]] = set()

    for sentence in _iter_candidate_sentences(sections=sections, extracted_signals=extracted_signals):
        pod_match = POD_TERM_PATTERN.search(sentence)
        pod_term = _normalize_pod_term(pod_match.group(0) if pod_match else None)
        species = _detect_species(sentence)
        route = _detect_route(sentence) or route_fallback
        duration = _detect_duration(sentence)

        for match in DOSE_PATTERN.finditer(sentence):
            dose_text = match.group(0)
            unit = match.group("unit")
            value = float(match.group("value"))
            normalized_mg_per_kg_day, normalization_note = _normalize_mg_per_kg_day(
                value=value,
                unit=unit,
            )
            key = (dose_text, sentence, pod_term)
            if key in seen:
                continue
            seen.add(key)

            candidates.append(
                LiveWorkspaceDoseCandidate(
                    dose_text=dose_text,
                    dose_value=value,
                    unit=unit,
                    normalized_mg_per_kg_day=normalized_mg_per_kg_day,
                    normalization_note=normalization_note,
                    pod_term=pod_term,
                    species=species,
                    route=route,
                    duration=duration,
                    sentence=sentence,
                    confidence=_confidence_for_candidate(
                        pod_term=pod_term,
                        unit=unit,
                        species=species,
                        route=route,
                        duration=duration,
                        normalized_mg_per_kg_day=normalized_mg_per_kg_day,
                    ),
                )
            )

    candidates.sort(key=_candidate_sort_key, reverse=True)
    return candidates


def _build_derived_calculations(
    primary_candidate: LiveWorkspaceDoseCandidate | None,
) -> tuple[list[LiveWorkspaceDerivedCalculation], list[str]]:
    if primary_candidate is None or primary_candidate.dose_value is None or not primary_candidate.unit:
        return [], ["No dose-bearing POD candidate was available for derived calculations."]

    calculations: list[LiveWorkspaceDerivedCalculation] = []
    warnings: list[str] = []
    normalized_basis = primary_candidate.normalized_mg_per_kg_day
    if normalized_basis is None:
        warnings.append(
            "Derived screening calculations currently require a normalized mg/kg/day basis. "
            f"The selected candidate was reported as {primary_candidate.unit}."
        )
        return calculations, warnings

    if primary_candidate.normalization_note:
        calculations.append(
            LiveWorkspaceDerivedCalculation(
                key="normalized_basis",
                label="Normalized screening basis",
                formula="Normalized basis = reported dose converted to mg/kg/day when needed",
                result_text=f"{normalized_basis:.3g} mg/kg/day",
                unit="mg/kg/day",
                assumptions=[primary_candidate.normalization_note],
            )
        )

    screening_mg_day = normalized_basis * 50.0
    calculations.append(
        LiveWorkspaceDerivedCalculation(
            key="screening_mg_day_50kg",
            label="50 kg screening conversion",
            formula="mg/day = mg/kg/day × 50 kg",
            result_text=f"{screening_mg_day:.3g} mg/day",
            unit="mg/day",
            assumptions=[
                "Uses a 50 kg adult screening body weight.",
                "This is a dose-basis conversion only and not a regulatory PDE/ADE conclusion.",
            ],
        )
    )

    if primary_candidate.species and primary_candidate.species in KM_FACTORS and primary_candidate.species != "human":
        animal_km = KM_FACTORS[primary_candidate.species]
        hed_value = normalized_basis * (animal_km / HUMAN_KM_FACTOR)
        calculations.append(
            LiveWorkspaceDerivedCalculation(
                key="screening_hed_mg_per_kg_day",
                label="Screening human equivalent dose",
                formula=f"HED (mg/kg/day) = animal POD × ({animal_km:g} / {HUMAN_KM_FACTOR:g})",
                result_text=f"{hed_value:.3g} mg/kg/day",
                unit="mg/kg/day",
                assumptions=[
                    f"Applies a standard Km-based screening conversion for {primary_candidate.species}.",
                    "This is intended for rapid curation support and does not replace formal toxicological judgment.",
                ],
            )
        )
        calculations.append(
            LiveWorkspaceDerivedCalculation(
                key="screening_hed_mg_day_50kg",
                label="50 kg HED screening conversion",
                formula="mg/day = HED (mg/kg/day) × 50 kg",
                result_text=f"{hed_value * 50.0:.3g} mg/day",
                unit="mg/day",
                assumptions=[
                    "Derived from the screening human equivalent dose.",
                    "Uses a 50 kg adult screening body weight.",
                ],
            )
        )

    adjusted_screening_intake = screening_mg_day / 100.0
    calculations.append(
        LiveWorkspaceDerivedCalculation(
            key="illustrative_uf100_screen",
            label="Illustrative UF100 screening intake",
            formula="screening intake (mg/day) = normalized basis × 50 kg / 100",
            result_text=f"{adjusted_screening_intake:.3g} mg/day",
            unit="mg/day",
            assumptions=[
                "Uses the normalized mg/kg/day basis and a 50 kg adult screening body weight.",
                "Applies a composite uncertainty factor of 100 as a rough curation screen only.",
                "This is not a formal PDE/ADE or health-based exposure limit.",
            ],
        )
    )

    return calculations, warnings


def build_pod_analysis(
    *,
    record: LiveSearchResult,
    sections: list[LiveWorkspaceSection],
    extracted_signals: list[LiveWorkspaceExtractedSignal],
) -> LiveWorkspacePodAnalysis:
    candidates = _build_candidates(
        record=record,
        sections=sections,
        extracted_signals=extracted_signals,
    )
    primary_candidate = candidates[0] if candidates else None
    calculations, warnings = _build_derived_calculations(primary_candidate)

    if primary_candidate is None:
        warnings = [
            "No explicit dose-bearing POD candidate was extracted from the current source.",
            "The current workspace may still be useful for route, hazard, or literature context.",
        ]
    elif primary_candidate.pod_term is None:
        warnings.append(
            "The leading dose candidate did not include explicit POD language, so it should be treated as contextual rather than definitive."
        )
    elif primary_candidate.normalized_mg_per_kg_day is None:
        warnings.append(
            "The leading candidate could not be normalized to an mg/kg/day basis, so any worksheet math remains limited."
        )

    if record.provider == "pubmed":
        warnings.append(
            "PubMed-derived POD candidates are abstract-level cues unless the full article is reviewed."
        )
    if record.provider == "echa":
        warnings.append(
            "ECHA workspaces are regulatory lookup stubs in this prototype because direct server-side enrichment is limited by upstream protections."
        )

    return LiveWorkspacePodAnalysis(
        primary_candidate=primary_candidate,
        candidates=candidates[:6],
        derived_calculations=calculations,
        warnings=warnings,
    )
