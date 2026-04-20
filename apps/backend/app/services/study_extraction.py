from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.models.document import DocumentChunk
from app.schemas.study_extraction import (
    ExtractedStudyField,
    ExtractionCitationSpan,
    StudyDetailExtractionResult,
)

SPECIES_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "Sprague-Dawley rat",
        re.compile(r"\bSprague[- ]Dawley rats?\b", re.IGNORECASE),
    ),
    ("Wistar rat", re.compile(r"\bWistar rats?\b", re.IGNORECASE)),
    ("rat", re.compile(r"\brats?\b", re.IGNORECASE)),
    ("mouse", re.compile(r"\bmice\b|\bmouse\b", re.IGNORECASE)),
    ("rabbit", re.compile(r"\brabbits?\b", re.IGNORECASE)),
    ("dog", re.compile(r"\bdogs?\b|\bcanine\b", re.IGNORECASE)),
    ("monkey", re.compile(r"\bmonkeys?\b|\bmacaques?\b", re.IGNORECASE)),
    ("minipig", re.compile(r"\bminipigs?\b", re.IGNORECASE)),
    ("human", re.compile(r"\bhuman(?:s)?\b|\bpatients?\b|\bsubjects?\b", re.IGNORECASE)),
)
ROUTE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("oral gavage", re.compile(r"\boral gavage\b", re.IGNORECASE)),
    ("oral", re.compile(r"\boral\b|\bPO\b", re.IGNORECASE)),
    ("intravenous", re.compile(r"\bintravenous\b|\bIV\b", re.IGNORECASE)),
    ("subcutaneous", re.compile(r"\bsubcutaneous\b|\bSC\b", re.IGNORECASE)),
    ("intramuscular", re.compile(r"\bintramuscular\b|\bIM\b", re.IGNORECASE)),
    ("inhalation", re.compile(r"\binhal(?:ed|ation)\b", re.IGNORECASE)),
    ("dermal", re.compile(r"\bdermal\b|\btopical\b|\btransdermal\b", re.IGNORECASE)),
    ("intranasal", re.compile(r"\bintranasal\b|\bnasal\b", re.IGNORECASE)),
    ("ocular", re.compile(r"\bocular\b|\bophthalmic\b", re.IGNORECASE)),
)
DURATION_PATTERN = re.compile(
    r"\b(?:single[- ]dose|acute|subchronic|chronic|\d+\s*[- ]?"
    r"(?:day|days|week|weeks|month|months|year|years))\b",
    re.IGNORECASE,
)
DOSE_PATTERN = re.compile(
    r"\b\d+(?:\.\d+)?(?:\s*,\s*\d+(?:\.\d+)?)*(?:\s*,?\s*and\s*\d+(?:\.\d+)?)?\s*"
    r"(?:mg|g|ug|mcg|ng)\s*(?:/kg(?:/day)?|/day|/animal/day|/person/day)?\b",
    re.IGNORECASE,
)
EXPOSURE_PATTERN = re.compile(
    r"\b(?:exposure|systemic exposure|AUC(?:0[- ]?\d+)?|Cmax|Cmin|AUCinf|AUCtau)\b",
    re.IGNORECASE,
)
STUDY_TYPE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "repeat-dose toxicology study",
        re.compile(r"\brepeat[- ]dose toxicology study\b", re.IGNORECASE),
    ),
    (
        "developmental toxicity study",
        re.compile(r"\bdevelopmental toxicity study\b", re.IGNORECASE),
    ),
    (
        "carcinogenicity study",
        re.compile(r"\bcarcinogenicity study\b", re.IGNORECASE),
    ),
    (
        "pharmacokinetic study",
        re.compile(r"\bpharmacokinetic study\b|\bPK study\b", re.IGNORECASE),
    ),
    (
        "randomized clinical trial",
        re.compile(r"\brandomized(?: controlled)? (?:clinical )?trial\b", re.IGNORECASE),
    ),
    ("cohort study", re.compile(r"\bcohort study\b", re.IGNORECASE)),
    ("case-control study", re.compile(r"\bcase-control study\b", re.IGNORECASE)),
    ("in vitro study", re.compile(r"\bin vitro study\b", re.IGNORECASE)),
)
POD_PATTERN = re.compile(
    r"\b(?:point of departure|POD|NOAEL|LOAEL|NOEL|LOEL|BMDL|BMCL|benchmark dose)\b",
    re.IGNORECASE,
)


def _sentence_bounds(text: str, start: int, end: int) -> tuple[int, int]:
    left = max(text.rfind(".", 0, start), text.rfind("\n", 0, start), text.rfind(";", 0, start))
    right_candidates = [index for index in (text.find(".", end), text.find("\n", end), text.find(";", end)) if index != -1]
    sentence_start = left + 1 if left != -1 else 0
    sentence_end = min(right_candidates) + 1 if right_candidates else len(text)
    return sentence_start, sentence_end


def _build_citation(
    *,
    chunk: DocumentChunk,
    start: int,
    end: int,
    label: str,
) -> ExtractionCitationSpan:
    return ExtractionCitationSpan(
        document_chunk_id=getattr(chunk, "id", None),
        chunk_index=chunk.chunk_index,
        start_offset=start,
        end_offset=end,
        quoted_text=chunk.content[start:end].strip(),
        page_number_start=chunk.page_number_start,
        page_number_end=chunk.page_number_end,
        label=label,
    )


def _build_field(
    *,
    chunk: DocumentChunk,
    start: int,
    end: int,
    value: str,
    label: str,
    extraction_method: str = "rule_based",
) -> ExtractedStudyField:
    return ExtractedStudyField(
        value=value.strip(),
        citations=[_build_citation(chunk=chunk, start=start, end=end, label=label)],
        extraction_method=extraction_method,
    )


def _first_pattern_match(
    chunks: Sequence[DocumentChunk],
    patterns: Sequence[tuple[str, re.Pattern[str]]],
    *,
    label: str,
) -> ExtractedStudyField | None:
    for chunk in chunks:
        for normalized_value, pattern in patterns:
            match = pattern.search(chunk.content)
            if match is None:
                continue

            return _build_field(
                chunk=chunk,
                start=match.start(),
                end=match.end(),
                value=normalized_value,
                label=label,
            )

    return None


def _first_text_span_match(
    chunks: Sequence[DocumentChunk],
    pattern: re.Pattern[str],
    *,
    label: str,
    use_sentence: bool = False,
) -> ExtractedStudyField | None:
    for chunk in chunks:
        match = pattern.search(chunk.content)
        if match is None:
            continue

        start, end = match.start(), match.end()
        if use_sentence:
            start, end = _sentence_bounds(chunk.content, start, end)

        return _build_field(
            chunk=chunk,
            start=start,
            end=end,
            value=chunk.content[start:end].strip(),
            label=label,
        )

    return None


def _all_sentence_matches(
    chunks: Sequence[DocumentChunk],
    pattern: re.Pattern[str],
    *,
    label: str,
) -> list[ExtractedStudyField]:
    results: list[ExtractedStudyField] = []
    seen: set[tuple[int, int, int]] = set()

    for chunk in chunks:
        for match in pattern.finditer(chunk.content):
            start, end = _sentence_bounds(chunk.content, match.start(), match.end())
            key = (chunk.chunk_index, start, end)
            if key in seen:
                continue

            seen.add(key)
            results.append(
                _build_field(
                    chunk=chunk,
                    start=start,
                    end=end,
                    value=chunk.content[start:end].strip(),
                    label=label,
                )
            )

    return results


class StudyExtractionReconciler(ABC):
    @abstractmethod
    def reconcile(
        self,
        *,
        rule_based_result: StudyDetailExtractionResult,
        document_chunks: Sequence[DocumentChunk],
    ) -> StudyDetailExtractionResult:
        """Reconcile rule-based extraction output with an LLM-backed reviewer."""


class PassthroughStudyExtractionReconciler(StudyExtractionReconciler):
    def reconcile(
        self,
        *,
        rule_based_result: StudyDetailExtractionResult,
        document_chunks: Sequence[DocumentChunk],
    ) -> StudyDetailExtractionResult:
        return rule_based_result.model_copy(
            update={
                "reconciliation_status": "skipped",
                "notes": [
                    *rule_based_result.notes,
                    "LLM reconciliation was not requested; returning rule-based extraction.",
                ],
            }
        )


class RuleBasedStudyDetailExtractor:
    def extract(
        self,
        *,
        document_chunks: Sequence[DocumentChunk],
    ) -> StudyDetailExtractionResult:
        ordered_chunks = sorted(document_chunks, key=lambda chunk: chunk.chunk_index)

        return StudyDetailExtractionResult(
            species=_first_pattern_match(ordered_chunks, SPECIES_PATTERNS, label="species"),
            route=_first_pattern_match(ordered_chunks, ROUTE_PATTERNS, label="route"),
            duration=_first_text_span_match(
                ordered_chunks,
                DURATION_PATTERN,
                label="duration",
            ),
            dose_text=_first_text_span_match(
                ordered_chunks,
                DOSE_PATTERN,
                label="dose_text",
                use_sentence=True,
            ),
            exposure_text=_first_text_span_match(
                ordered_chunks,
                EXPOSURE_PATTERN,
                label="exposure_text",
                use_sentence=True,
            ),
            study_type=_first_pattern_match(
                ordered_chunks,
                STUDY_TYPE_PATTERNS,
                label="study_type",
            ),
            explicit_pod_mentions=_all_sentence_matches(
                ordered_chunks,
                POD_PATTERN,
                label="explicit_pod_mentions",
            ),
        )


class HybridStudyDetailExtractionPipeline:
    def __init__(
        self,
        *,
        rule_based_extractor: RuleBasedStudyDetailExtractor | None = None,
        reconciler: StudyExtractionReconciler | None = None,
    ) -> None:
        self._rule_based_extractor = rule_based_extractor or RuleBasedStudyDetailExtractor()
        self._reconciler = reconciler or PassthroughStudyExtractionReconciler()

    def extract(
        self,
        *,
        document_chunks: Sequence[DocumentChunk],
    ) -> StudyDetailExtractionResult:
        rule_based_result = self._rule_based_extractor.extract(
            document_chunks=document_chunks,
        )
        return self._reconciler.reconcile(
            rule_based_result=rule_based_result,
            document_chunks=document_chunks,
        )
