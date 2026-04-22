from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import re
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.errors import raise_api_error
from app.models.catalog import Comparator, Product
from app.models.document import CitationSpan, DocumentChunk, SourceDocument
from app.models.research import (
    CalculationRun,
    CandidatePOD,
    ExpertReview,
    Finding,
    Limitation,
    Recommendation,
    Study,
)
from app.schemas.reports import (
    CandidatePODAssessmentItem,
    CandidatePODAssessmentSection,
    CalculationSummaryItem,
    ComparatorSummaryItem,
    ComparatorSummarySection,
    EvidenceFindingItem,
    EvidenceStudyItem,
    EvidenceSummarySection,
    ExpertReviewItem,
    ExpertReviewSection,
    LimitationsSection,
    ProductOverviewSection,
    ProductReportRead,
    ReportCitation,
    ReportLimitationItem,
    SuggestedExperimentItem,
    SuggestedNextExperimentsSection,
)
from app.schemas.comparator_scoring import ComparatorScoringInput
from app.schemas.limitations import GeneratedLimitation
from app.schemas.pod_support import CandidatePODSupportResult
from app.services.comparator_scoring import score_comparator
from app.services.limitations import generate_rule_based_limitations
from app.services.pod_support import generate_pod_recommendations, score_candidate_pod_support

LIMITATION_EXPERIMENT_MAP: dict[str, tuple[str, str, str]] = {
    "missing_route": (
        "Run a route-matched bridge study",
        "A route-matched study would make the current evidence more comparable to the intended product use scenario.",
        "high",
    ),
    "missing_species_relevance": (
        "Add a species relevance or translational bridge experiment",
        "Translational support would strengthen why the current species or population should inform the product decision.",
        "high",
    ),
    "no_explicit_pod": (
        "Design a dose-ranging study to establish an explicit POD",
        "An explicit NOAEL, LOAEL, or benchmark-dose anchor would materially improve downstream calculations and review defensibility.",
        "high",
    ),
    "sparse_dose_context": (
        "Expand dose-ranging and exposure characterization",
        "Additional dose and exposure context would make the candidate POD easier to interpret and compare.",
        "medium",
    ),
    "low_confidence_extraction": (
        "Perform manual source verification and targeted re-extraction",
        "Source verification reduces the chance that a key quantitative input was captured incorrectly.",
        "medium",
    ),
    "analog_only_evidence": (
        "Generate direct product-specific confirmatory evidence",
        "Direct evidence would reduce dependence on analog or bridge assumptions in the report narrative.",
        "high",
    ),
}

COMPARATOR_SIGNAL_PATTERNS: dict[str, re.Pattern[str]] = {
    "same_target": re.compile(
        r"\b(same[_ -]?target|target[- ]matched|target[- ]aligned)\b",
        re.IGNORECASE,
    ),
    "same_modality": re.compile(
        r"\b(same[_ -]?modality|matched modality|shared modality)\b",
        re.IGNORECASE,
    ),
    "same_route": re.compile(
        r"\b(same[_ -]?route|route[- ]matched|route[- ]aligned)\b",
        re.IGNORECASE,
    ),
    "same_indication": re.compile(
        r"\b(same[_ -]?indication|indication[- ]matched|shared indication)\b",
        re.IGNORECASE,
    ),
    "same_scaffold": re.compile(
        r"\b(same[_ -]?scaffold|shared scaffold|same backbone)\b",
        re.IGNORECASE,
    ),
}

DEFAULT_CALCULATION_FORMULA_VERSION = "1.0"


def _fallback_source_document_citation(
    source_document: SourceDocument,
    *,
    label: str | None = None,
) -> ReportCitation:
    return ReportCitation(
        source_document_id=source_document.id,
        source_document_title=source_document.title,
        label=label,
    )


def _citation_from_span(citation_span: CitationSpan) -> ReportCitation:
    chunk = citation_span.document_chunk
    source_document = chunk.source_document if chunk is not None else None
    quoted_text = citation_span.quoted_text

    if quoted_text is None and chunk is not None:
        quoted_text = chunk.content[citation_span.start_offset : citation_span.end_offset]

    return ReportCitation(
        source_document_id=source_document.id if source_document is not None else None,
        source_document_title=(
            source_document.title if source_document is not None else "Unknown source document"
        ),
        citation_span_id=citation_span.id,
        label=citation_span.label,
        quoted_text=quoted_text,
        chunk_index=chunk.chunk_index if chunk is not None else None,
        page_number_start=chunk.page_number_start if chunk is not None else None,
        page_number_end=chunk.page_number_end if chunk is not None else None,
    )


def _citation_key(citation: ReportCitation) -> tuple[int | None, int | None, str | None, str | None]:
    return (
        citation.citation_span_id,
        citation.source_document_id,
        citation.label,
        citation.quoted_text,
    )


def _dedupe_citations(citations: list[ReportCitation]) -> list[ReportCitation]:
    seen: set[tuple[int | None, int | None, str | None, str | None]] = set()
    deduped: list[ReportCitation] = []

    for citation in citations:
        key = _citation_key(citation)
        if key in seen:
            continue

        seen.add(key)
        deduped.append(citation)

    return deduped


def _section_citations(
    *,
    item_citations: list[ReportCitation],
    extra_citations: list[ReportCitation] | None = None,
) -> list[ReportCitation]:
    seen = {_citation_key(citation) for citation in _dedupe_citations(item_citations)}
    section_citations: list[ReportCitation] = []

    for citation in _dedupe_citations(extra_citations or []):
        key = _citation_key(citation)
        if key in seen:
            continue

        seen.add(key)
        section_citations.append(citation)

    return section_citations


def _citations_for_finding(finding: Finding | None) -> list[ReportCitation]:
    if finding is None:
        return []

    citations = [_citation_from_span(citation_span) for citation_span in finding.citation_spans]
    if citations:
        return _dedupe_citations(citations)

    source_document = finding.study.source_document
    if source_document is not None:
        return [_fallback_source_document_citation(source_document, label="source_document")]

    return []


def _citations_for_study(study: Study | None) -> list[ReportCitation]:
    if study is None:
        return []

    citations: list[ReportCitation] = []
    for finding in study.findings:
        citations.extend(_citations_for_finding(finding))

    if citations:
        return _dedupe_citations(citations)

    if study.source_document is not None:
        return [_fallback_source_document_citation(study.source_document, label="source_document")]

    return []


def _citations_for_candidate_pod(candidate_pod: CandidatePOD | None) -> list[ReportCitation]:
    if candidate_pod is None:
        return []

    citations = _citations_for_finding(candidate_pod.finding)
    if citations:
        return citations

    return []


def _citations_for_recommendation(recommendation: Recommendation) -> list[ReportCitation]:
    if recommendation.finding is not None:
        citations = _citations_for_finding(recommendation.finding)
        if citations:
            return citations

    if recommendation.candidate_pod is not None:
        citations = _citations_for_candidate_pod(recommendation.candidate_pod)
        if citations:
            return citations

    if recommendation.study is not None:
        return _citations_for_study(recommendation.study)

    return []


def _citations_for_expert_review(review: ExpertReview) -> list[ReportCitation]:
    if review.finding is not None:
        citations = _citations_for_finding(review.finding)
        if citations:
            return citations

    if review.candidate_pod is not None:
        citations = _citations_for_candidate_pod(review.candidate_pod)
        if citations:
            return citations

    calculation_run = review.calculation_run
    if calculation_run is not None:
        if calculation_run.candidate_pod is not None:
            citations = _citations_for_candidate_pod(calculation_run.candidate_pod)
            if citations:
                return citations

        if calculation_run.study is not None:
            return _citations_for_study(calculation_run.study)

    return []


def _citations_for_calculation_run(calculation_run: CalculationRun) -> list[ReportCitation]:
    if calculation_run.candidate_pod is not None:
        citations = _citations_for_candidate_pod(calculation_run.candidate_pod)
        if citations:
            return citations

    if calculation_run.study is not None:
        citations = _citations_for_study(calculation_run.study)
        if citations:
            return citations

    return []


def _titleize_identifier(identifier: str) -> str:
    return identifier.replace("_", " ").title()


def _build_comparator_scoring_input(comparator: Comparator) -> ComparatorScoringInput:
    comparator_text = " ".join(
        part.strip()
        for part in (comparator.name, comparator.category, comparator.description)
        if part and part.strip()
    )

    return ComparatorScoringInput(
        comparator_name=comparator.name,
        same_target=bool(COMPARATOR_SIGNAL_PATTERNS["same_target"].search(comparator_text)),
        same_modality=bool(COMPARATOR_SIGNAL_PATTERNS["same_modality"].search(comparator_text)),
        same_route=bool(COMPARATOR_SIGNAL_PATTERNS["same_route"].search(comparator_text)),
        same_indication=bool(
            COMPARATOR_SIGNAL_PATTERNS["same_indication"].search(comparator_text)
        ),
        same_scaffold=bool(COMPARATOR_SIGNAL_PATTERNS["same_scaffold"].search(comparator_text)),
    )


def _normalize_limitation_key(title: str) -> str:
    return title.strip().lower().replace("-", "_").replace(" ", "_")


def _why_it_matters_for_persisted_limitation(limitation: Limitation) -> str:
    if limitation.finding is not None:
        return (
            f"This limitation affects interpretation of the finding '{limitation.finding.title}' "
            "and should be addressed before final sign-off."
        )

    return (
        "This limitation was captured directly in the study record and may weaken the current evidence package if it remains unresolved."
    )


def _resolution_for_persisted_limitation(limitation: Limitation) -> str:
    if limitation.finding is not None:
        return (
            "Clarify the limitation in the study narrative, add supporting context, and confirm whether it changes the associated finding or candidate POD."
        )

    return (
        "Document the mitigation plan or collect follow-up evidence to reduce the impact of this limitation in the next report revision."
    )


def _limitation_is_blocking(severity: str | None) -> bool:
    return (severity or "").strip().lower() == "high"


def _looks_like_experiment_recommendation(recommendation: Recommendation) -> bool:
    recommendation_type = (recommendation.recommendation_type or "").lower()
    recommendation_text = recommendation.recommendation_text.lower()

    if recommendation_type in {"next_experiment", "experiment", "follow_up"}:
        return True

    return any(
        token in recommendation_text
        for token in ("experiment", "study", "assay", "bridge", "confirm", "dose-ranging")
    )


def _collect_recommendations(product: Product) -> list[Recommendation]:
    recommendations_by_id: dict[int, Recommendation] = {}

    for study in product.studies:
        for recommendation in study.recommendations:
            recommendations_by_id[recommendation.id] = recommendation

        for finding in study.findings:
            for recommendation in finding.recommendations:
                recommendations_by_id[recommendation.id] = recommendation

    for candidate_pod in product.candidate_pods:
        for recommendation in candidate_pod.recommendations:
            recommendations_by_id[recommendation.id] = recommendation

    return list(recommendations_by_id.values())


def _collect_expert_reviews(product: Product) -> list[ExpertReview]:
    reviews_by_id: dict[int, ExpertReview] = {}

    for study in product.studies:
        for finding in study.findings:
            for review in finding.expert_reviews:
                reviews_by_id[review.id] = review

    for candidate_pod in product.candidate_pods:
        for review in candidate_pod.expert_reviews:
            reviews_by_id[review.id] = review

    for calculation_run in product.calculation_runs:
        for review in calculation_run.expert_reviews:
            reviews_by_id[review.id] = review

    return list(reviews_by_id.values())


def _review_sort_key(review: ExpertReview) -> tuple[datetime, int]:
    return (
        review.reviewed_at
        or review.updated_at
        or review.created_at
        or datetime.min.replace(tzinfo=timezone.utc),
        review.id,
    )


def _latest_expert_reviews_by_candidate_pod(
    product: Product,
) -> dict[int, ExpertReview]:
    latest_reviews: dict[int, ExpertReview] = {}

    for review in _collect_expert_reviews(product):
        if review.candidate_pod_id is None:
            continue

        current = latest_reviews.get(review.candidate_pod_id)
        if current is None or _review_sort_key(review) > _review_sort_key(current):
            latest_reviews[review.candidate_pod_id] = review

    return latest_reviews


def _collect_calculation_runs(product: Product) -> list[CalculationRun]:
    calculation_runs_by_id: dict[int, CalculationRun] = {}

    for calculation_run in product.calculation_runs:
        calculation_runs_by_id[calculation_run.id] = calculation_run

    for study in product.studies:
        for calculation_run in study.calculation_runs:
            calculation_runs_by_id[calculation_run.id] = calculation_run

    for candidate_pod in product.candidate_pods:
        for calculation_run in candidate_pod.calculation_runs:
            calculation_runs_by_id[calculation_run.id] = calculation_run

    return sorted(
        calculation_runs_by_id.values(),
        key=lambda item: (
            item.completed_at or item.started_at or item.created_at,
            item.id,
        ),
        reverse=True,
    )


def _score_comparators(product: Product) -> dict[int, float]:
    comparator_map: dict[int, Comparator] = {}

    for study in product.studies:
        if study.comparator is not None:
            comparator_map[study.comparator.id] = study.comparator

    for candidate_pod in product.candidate_pods:
        if candidate_pod.comparator is not None:
            comparator_map[candidate_pod.comparator.id] = candidate_pod.comparator

    return {
        comparator_id: score_comparator(_build_comparator_scoring_input(comparator)).relevance_score
        for comparator_id, comparator in comparator_map.items()
    }


def _generated_limitations_by_candidate_pod(
    product: Product,
) -> dict[int, list[GeneratedLimitation]]:
    generated_limitations: dict[int, list[GeneratedLimitation]] = {}

    for candidate_pod in product.candidate_pods:
        study = candidate_pod.finding.study if candidate_pod.finding is not None else None
        generated_limitations[candidate_pod.id] = generate_rule_based_limitations(
            study=study,
            candidate_pod=candidate_pod,
        )

    return generated_limitations


def _support_result_for_candidate_pod(
    *,
    candidate_pod: CandidatePOD,
    comparator_scores: dict[int, float],
    generated_limitations: dict[int, list[GeneratedLimitation]],
    latest_expert_reviews: dict[int, ExpertReview],
) -> CandidatePODSupportResult:
    study = candidate_pod.finding.study if candidate_pod.finding is not None else None
    comparator_score = (
        comparator_scores.get(candidate_pod.comparator.id)
        if candidate_pod.comparator is not None
        else None
    )
    support_result = score_candidate_pod_support(
        study=study,
        candidate_pod=candidate_pod,
        limitations=generated_limitations.get(candidate_pod.id, []),
        comparator_relevance_score=comparator_score,
    )
    latest_review = latest_expert_reviews.get(candidate_pod.id)
    if latest_review is None:
        return support_result

    support_category = (
        latest_review.override_support_category or support_result.support_category
    )
    support_score = (
        float(latest_review.override_support_score)
        if latest_review.override_support_score is not None
        else support_result.support_score
    )
    expert_review_required = (
        False
        if latest_review.expert_review_required_resolved
        else support_result.expert_review_required
    )

    expert_updates: list[str] = []
    if latest_review.accepted_current_assessment:
        expert_updates.append("expert accepted the current assessment")
    if latest_review.override_support_category is not None:
        expert_updates.append(
            f"support category overridden to {support_category.replace('_', ' ')}"
        )
    if latest_review.override_support_score is not None:
        expert_updates.append(f"support score overridden to {support_score:.1f}")
    if latest_review.expert_review_required_resolved:
        expert_updates.append("expert review requirement marked resolved")

    rationale = support_result.confidence_rationale
    if expert_updates:
        rationale = (
            f"{rationale} Latest expert review update: {'; '.join(expert_updates)}."
        )

    return CandidatePODSupportResult(
        support_category=support_category,
        support_score=support_score,
        confidence_rationale=rationale,
        expert_review_required=expert_review_required,
    )


def _build_product_overview(product: Product) -> ProductOverviewSection:
    citations = _dedupe_citations(
        [
            citation
            for study in product.studies
            for citation in _citations_for_study(study)
        ]
    )

    return ProductOverviewSection(
        name=product.name,
        slug=product.slug,
        manufacturer=product.manufacturer,
        description=product.description,
        study_count=len(product.studies),
        finding_count=sum(len(study.findings) for study in product.studies),
        candidate_pod_count=len(product.candidate_pods),
        citations=citations,
    )


def _build_comparator_summary(
    product: Product,
    *,
    comparator_scores: dict[int, float],
) -> ComparatorSummarySection:
    comparator_map: dict[int, Comparator] = {}
    comparator_citations: defaultdict[int, list[ReportCitation]] = defaultdict(list)
    study_counts: defaultdict[int, int] = defaultdict(int)
    candidate_counts: defaultdict[int, int] = defaultdict(int)

    for study in product.studies:
        if study.comparator is None:
            continue
        comparator_map[study.comparator.id] = study.comparator
        study_counts[study.comparator.id] += 1
        comparator_citations[study.comparator.id].extend(_citations_for_study(study))

    for candidate_pod in product.candidate_pods:
        if candidate_pod.comparator is None:
            continue
        comparator_map[candidate_pod.comparator.id] = candidate_pod.comparator
        candidate_counts[candidate_pod.comparator.id] += 1
        comparator_citations[candidate_pod.comparator.id].extend(
            _citations_for_candidate_pod(candidate_pod)
        )

    items: list[ComparatorSummaryItem] = []
    for comparator in sorted(comparator_map.values(), key=lambda item: item.name.lower()):
        comparator_score = score_comparator(_build_comparator_scoring_input(comparator))
        items.append(
            ComparatorSummaryItem(
                comparator_id=comparator.id,
                name=comparator.name,
                category=comparator.category,
                description=comparator.description,
                relevance_score=comparator_scores.get(comparator.id, comparator_score.relevance_score),
                relevance_rationale=comparator_score.rationale,
                linked_study_count=study_counts[comparator.id],
                linked_candidate_pod_count=candidate_counts[comparator.id],
                citations=_dedupe_citations(comparator_citations[comparator.id]),
            )
        )

    item_citations = [citation for item in items for citation in item.citations]

    return ComparatorSummarySection(
        items=items,
        citations=_section_citations(item_citations=item_citations),
    )


def _formula_version_for_calculation_run(calculation_run: CalculationRun) -> str:
    result_json = calculation_run.result_json or {}
    formula_version = result_json.get("formula_version")

    if isinstance(formula_version, str) and formula_version.strip():
        return formula_version

    return DEFAULT_CALCULATION_FORMULA_VERSION


def _build_evidence_summary(product: Product) -> EvidenceSummarySection:
    studies = [
        EvidenceStudyItem(
            study_id=study.id,
            title=study.title,
            study_design=study.study_design,
            status=study.status,
            source_document_title=study.source_document.title if study.source_document else None,
            published_at=study.published_at,
            citations=_citations_for_study(study),
        )
        for study in sorted(product.studies, key=lambda item: item.title.lower())
    ]

    findings = [
        EvidenceFindingItem(
            finding_id=finding.id,
            study_id=finding.study_id,
            study_title=finding.study.title,
            title=finding.title,
            summary=finding.summary,
            finding_type=finding.finding_type,
            evidence_direction=finding.evidence_direction,
            effect_estimate=finding.effect_estimate,
            citations=_citations_for_finding(finding),
        )
        for study in product.studies
        for finding in sorted(study.findings, key=lambda item: item.title.lower())
    ]

    calculations = [
        CalculationSummaryItem(
            calculation_id=calculation_run.id,
            calculation_type=calculation_run.run_type,
            status=calculation_run.status,
            formula_version=_formula_version_for_calculation_run(calculation_run),
            inputs=calculation_run.parameters_json or {},
            outputs=(calculation_run.result_json or {}).get("result") or {},
            assumptions=list((calculation_run.result_json or {}).get("assumptions") or []),
            warnings=list((calculation_run.result_json or {}).get("warnings") or []),
            citations=_citations_for_calculation_run(calculation_run),
        )
        for calculation_run in _collect_calculation_runs(product)
    ]

    item_citations = [citation for item in studies for citation in item.citations] + [
        citation for item in findings for citation in item.citations
    ] + [citation for item in calculations for citation in item.citations]

    return EvidenceSummarySection(
        study_count=len(studies),
        finding_count=len(findings),
        studies=studies,
        findings=findings,
        calculations=calculations,
        citations=_section_citations(item_citations=item_citations),
    )


def _build_candidate_pod_assessment(
    product: Product,
    *,
    comparator_scores: dict[int, float],
    generated_limitations: dict[int, list[GeneratedLimitation]],
    latest_expert_reviews: dict[int, ExpertReview],
) -> CandidatePODAssessmentSection:
    items: list[CandidatePODAssessmentItem] = []
    for candidate_pod in sorted(product.candidate_pods, key=lambda item: item.title.lower()):
        support_result = _support_result_for_candidate_pod(
            candidate_pod=candidate_pod,
            comparator_scores=comparator_scores,
            generated_limitations=generated_limitations,
            latest_expert_reviews=latest_expert_reviews,
        )
        items.append(
            CandidatePODAssessmentItem(
                candidate_pod_id=candidate_pod.id,
                title=candidate_pod.title,
                claim_text=candidate_pod.claim_text,
                rationale=candidate_pod.rationale,
                status=candidate_pod.status,
                confidence_score=candidate_pod.confidence_score,
                support_category=support_result.support_category,
                support_score=support_result.support_score,
                confidence_rationale=support_result.confidence_rationale,
                expert_review_required=support_result.expert_review_required,
                comparator_name=(
                    candidate_pod.comparator.name if candidate_pod.comparator is not None else None
                ),
                linked_finding_title=(
                    candidate_pod.finding.title if candidate_pod.finding is not None else None
                ),
                citations=_citations_for_candidate_pod(candidate_pod),
            )
        )

    item_citations = [citation for item in items for citation in item.citations]

    return CandidatePODAssessmentSection(
        items=items,
        citations=_section_citations(item_citations=item_citations),
    )


def _build_limitations(
    product: Product,
    *,
    generated_limitations: dict[int, list[GeneratedLimitation]],
) -> LimitationsSection:
    items: list[ReportLimitationItem] = []

    for study in product.studies:
        for limitation in study.limitations:
            items.append(
                ReportLimitationItem(
                    source="persisted",
                    title="Recorded limitation",
                    description=limitation.description,
                    severity=limitation.severity,
                    why_it_matters=_why_it_matters_for_persisted_limitation(limitation),
                    resolution_suggestion=_resolution_for_persisted_limitation(limitation),
                    is_blocking=_limitation_is_blocking(limitation.severity),
                    study_title=study.title,
                    finding_title=(
                        limitation.finding.title if limitation.finding is not None else None
                    ),
                    citations=(
                        _citations_for_finding(limitation.finding)
                        or _citations_for_study(study)
                    ),
                )
            )

    for candidate_pod in product.candidate_pods:
        study = candidate_pod.finding.study if candidate_pod.finding is not None else None
        if study is None:
            continue

        for generated in generated_limitations.get(candidate_pod.id, []):
            items.append(
                ReportLimitationItem(
                    source="generated",
                    title=generated.title,
                    description=generated.description,
                    severity=generated.severity,
                    why_it_matters=generated.why_it_matters,
                    resolution_suggestion=generated.resolution_suggestion,
                    is_blocking=generated.is_blocking,
                    study_title=study.title,
                    finding_title=(
                        candidate_pod.finding.title if candidate_pod.finding is not None else None
                    ),
                    candidate_pod_title=candidate_pod.title,
                    citations=(
                        _citations_for_candidate_pod(candidate_pod)
                        or _citations_for_study(study)
                    ),
                )
            )

    item_citations = [citation for item in items for citation in item.citations]

    return LimitationsSection(
        items=items,
        citations=_section_citations(item_citations=item_citations),
    )


def _build_suggested_next_experiments(
    *,
    product: Product,
    limitations: LimitationsSection,
    comparator_scores: dict[int, float],
    generated_limitations: dict[int, list[GeneratedLimitation]],
    latest_expert_reviews: dict[int, ExpertReview],
) -> SuggestedNextExperimentsSection:
    items: list[SuggestedExperimentItem] = []
    seen_titles: set[str] = set()

    for recommendation in _collect_recommendations(product):
        if not _looks_like_experiment_recommendation(recommendation):
            continue

        title = (
            _titleize_identifier(recommendation.recommendation_type or "")
            if recommendation.recommendation_type
            else "Suggested next experiment"
        )
        title = title if title.strip() else "Suggested next experiment"

        unique_key = f"recommendation:{recommendation.id}"
        if unique_key in seen_titles:
            continue

        seen_titles.add(unique_key)
        items.append(
            SuggestedExperimentItem(
                source="recommendation",
                title=title,
                rationale=recommendation.recommendation_text,
                priority=recommendation.priority,
                recommendation_status=recommendation.status,
                citations=_citations_for_recommendation(recommendation),
            )
        )

    for limitation in limitations.items:
        if limitation.source != "generated":
            continue

        limitation_key = _normalize_limitation_key(limitation.title)
        experiment_template = LIMITATION_EXPERIMENT_MAP.get(limitation_key)
        if experiment_template is None:
            continue

        title, rationale, priority = experiment_template
        if title in seen_titles:
            continue

        seen_titles.add(title)
        items.append(
            SuggestedExperimentItem(
                source="generated",
                title=title,
                rationale=rationale,
                priority=priority,
                linked_limitation_title=limitation.title,
                recommendation_status="suggested",
                citations=limitation.citations,
            )
        )

    for candidate_pod in sorted(product.candidate_pods, key=lambda item: item.title.lower()):
        support_result = _support_result_for_candidate_pod(
            candidate_pod=candidate_pod,
            comparator_scores=comparator_scores,
            generated_limitations=generated_limitations,
            latest_expert_reviews=latest_expert_reviews,
        )
        comparator_score = (
            comparator_scores.get(candidate_pod.comparator.id)
            if candidate_pod.comparator is not None
            else None
        )
        generated_recommendations = generate_pod_recommendations(
            candidate_pod=candidate_pod,
            support_result=support_result,
            limitations=generated_limitations.get(candidate_pod.id, []),
            comparator_relevance_score=comparator_score,
        )

        for recommendation in generated_recommendations:
            unique_key = f"pod:{candidate_pod.id}:{recommendation.title}"
            if unique_key in seen_titles:
                continue

            seen_titles.add(unique_key)
            items.append(
                SuggestedExperimentItem(
                    source="generated",
                    title=recommendation.title,
                    rationale=recommendation.rationale,
                    priority=recommendation.priority,
                    linked_limitation_title=recommendation.linked_limitation_title,
                    recommendation_status=recommendation.recommendation_status,
                    citations=_citations_for_candidate_pod(candidate_pod),
                )
            )

    item_citations = [citation for item in items for citation in item.citations]

    return SuggestedNextExperimentsSection(
        items=items,
        citations=_section_citations(item_citations=item_citations),
    )


def _build_expert_review_section(product: Product) -> ExpertReviewSection:
    reviews = sorted(
        _collect_expert_reviews(product),
        key=_review_sort_key,
        reverse=True,
    )

    items = [
        ExpertReviewItem(
            expert_review_id=review.id,
            reviewer_name=review.reviewer_name,
            reviewer_email=review.reviewer_email,
            linked_candidate_pod_id=review.candidate_pod_id,
            verdict=review.verdict,
            score=review.score,
            accepted_current_assessment=review.accepted_current_assessment,
            expert_review_required_resolved=review.expert_review_required_resolved,
            override_support_category=review.override_support_category,
            override_support_score=review.override_support_score,
            notes=review.notes,
            reviewed_at=review.reviewed_at,
            linked_finding_title=review.finding.title if review.finding is not None else None,
            linked_candidate_pod_title=(
                review.candidate_pod.title if review.candidate_pod is not None else None
            ),
            citations=_citations_for_expert_review(review),
        )
        for review in reviews
    ]

    scores = [item.score for item in items if item.score is not None]
    average_score = sum(scores) / len(scores) if scores else None

    item_citations = [citation for item in items for citation in item.citations]

    return ExpertReviewSection(
        review_count=len(items),
        average_score=average_score,
        items=items,
        citations=_section_citations(item_citations=item_citations),
    )


def _load_product_for_report(*, db: Session, product_id: int) -> Product | None:
    statement = (
        select(Product)
        .where(Product.id == product_id)
        .options(
            selectinload(Product.studies).selectinload(Study.source_document),
            selectinload(Product.studies).selectinload(Study.comparator),
            selectinload(Product.studies)
            .selectinload(Study.findings)
            .selectinload(Finding.citation_spans)
            .selectinload(CitationSpan.document_chunk)
            .selectinload(DocumentChunk.source_document),
            selectinload(Product.studies).selectinload(Study.findings).selectinload(Finding.expert_reviews),
            selectinload(Product.studies).selectinload(Study.calculation_runs),
            selectinload(Product.studies).selectinload(Study.limitations).selectinload(Limitation.finding),
            selectinload(Product.studies).selectinload(Study.recommendations).selectinload(Recommendation.finding),
            selectinload(Product.studies).selectinload(Study.recommendations).selectinload(Recommendation.candidate_pod),
            selectinload(Product.candidate_pods).selectinload(CandidatePOD.comparator),
            selectinload(Product.candidate_pods)
            .selectinload(CandidatePOD.finding)
            .selectinload(Finding.citation_spans)
            .selectinload(CitationSpan.document_chunk)
            .selectinload(DocumentChunk.source_document),
            selectinload(Product.candidate_pods).selectinload(CandidatePOD.finding).selectinload(Finding.study),
            selectinload(Product.candidate_pods).selectinload(CandidatePOD.calculation_runs),
            selectinload(Product.candidate_pods).selectinload(CandidatePOD.recommendations).selectinload(Recommendation.finding),
            selectinload(Product.candidate_pods).selectinload(CandidatePOD.expert_reviews).selectinload(ExpertReview.finding),
            selectinload(Product.candidate_pods).selectinload(CandidatePOD.expert_reviews).selectinload(ExpertReview.candidate_pod),
            selectinload(Product.calculation_runs).selectinload(CalculationRun.study),
            selectinload(Product.calculation_runs).selectinload(CalculationRun.candidate_pod),
            selectinload(Product.calculation_runs).selectinload(CalculationRun.expert_reviews),
            selectinload(Product.calculation_runs)
            .selectinload(CalculationRun.expert_reviews)
            .selectinload(ExpertReview.finding),
            selectinload(Product.calculation_runs)
            .selectinload(CalculationRun.expert_reviews)
            .selectinload(ExpertReview.candidate_pod),
        )
    )
    return db.execute(statement).scalar_one_or_none()


def generate_product_report(*, db: Session, product_id: int) -> ProductReportRead:
    product = _load_product_for_report(db=db, product_id=product_id)
    if product is None:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="product_not_found",
            message=f"Product with id {product_id} was not found.",
        )

    product_overview = _build_product_overview(product)
    comparator_scores = _score_comparators(product)
    generated_limitations = _generated_limitations_by_candidate_pod(product)
    latest_expert_reviews = _latest_expert_reviews_by_candidate_pod(product)
    comparator_summary = _build_comparator_summary(
        product,
        comparator_scores=comparator_scores,
    )
    evidence_summary = _build_evidence_summary(product)
    candidate_pod_assessment = _build_candidate_pod_assessment(
        product,
        comparator_scores=comparator_scores,
        generated_limitations=generated_limitations,
        latest_expert_reviews=latest_expert_reviews,
    )
    limitations = _build_limitations(
        product,
        generated_limitations=generated_limitations,
    )
    suggested_next_experiments = _build_suggested_next_experiments(
        product=product,
        limitations=limitations,
        comparator_scores=comparator_scores,
        generated_limitations=generated_limitations,
        latest_expert_reviews=latest_expert_reviews,
    )
    expert_review_section = _build_expert_review_section(product)

    return ProductReportRead(
        product_id=product.id,
        generated_at=datetime.now(timezone.utc),
        product_overview=product_overview,
        comparator_summary=comparator_summary,
        evidence_summary=evidence_summary,
        candidate_pod_assessment=candidate_pod_assessment,
        limitations=limitations,
        suggested_next_experiments=suggested_next_experiments,
        expert_review_section=expert_review_section,
    )
