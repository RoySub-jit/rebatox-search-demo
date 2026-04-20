from __future__ import annotations

from app.models.document import DocumentChunk
from app.schemas.study_extraction import ExtractedStudyField
from app.services.study_extraction import (
    HybridStudyDetailExtractionPipeline,
    StudyExtractionReconciler,
)


def build_chunk(
    *,
    chunk_index: int,
    content: str,
    page_number_start: int = 1,
    page_number_end: int = 1,
) -> DocumentChunk:
    return DocumentChunk(
        source_document_id=1,
        chunk_index=chunk_index,
        content=content,
        page_number_start=page_number_start,
        page_number_end=page_number_end,
    )


def test_hybrid_pipeline_extracts_rule_based_study_fields_with_citations():
    chunks = [
        build_chunk(
            chunk_index=0,
            content=(
                "In a 28-day oral gavage Sprague-Dawley rat repeat-dose toxicology study, "
                "animals received 5, 15, and 45 mg/kg/day. "
                "Systemic exposure (AUC0-24) increased proportionally with dose. "
                "A NOAEL of 5 mg/kg/day was identified as the point of departure."
            ),
        )
    ]

    result = HybridStudyDetailExtractionPipeline().extract(document_chunks=chunks)

    assert result.reconciliation_status == "skipped"
    assert result.species is not None
    assert result.species.value == "Sprague-Dawley rat"
    assert result.species.citations[0].chunk_index == 0
    assert result.species.citations[0].quoted_text == "Sprague-Dawley rat"
    assert result.route is not None
    assert result.route.value == "oral gavage"
    assert result.duration is not None
    assert result.duration.value == "28-day"
    assert result.dose_text is not None
    assert "5, 15, and 45 mg/kg/day" in result.dose_text.value
    assert result.exposure_text is not None
    assert "Systemic exposure (AUC0-24)" in result.exposure_text.value
    assert result.study_type is not None
    assert result.study_type.value == "repeat-dose toxicology study"
    assert len(result.explicit_pod_mentions) == 1
    assert "point of departure" in result.explicit_pod_mentions[0].value
    assert result.explicit_pod_mentions[0].citations[0].label == "explicit_pod_mentions"


class FakeLLMReconciler(StudyExtractionReconciler):
    def reconcile(self, *, rule_based_result, document_chunks):
        assert rule_based_result.route is not None
        return rule_based_result.model_copy(
            update={
                "route": ExtractedStudyField(
                    value="oral route confirmed by LLM reconciliation",
                    citations=rule_based_result.route.citations,
                    extraction_method="llm_reconciled",
                ),
                "reconciliation_status": "completed",
                "notes": [
                    *rule_based_result.notes,
                    f"Reconciled across {len(document_chunks)} chunks.",
                ],
            }
        )


def test_hybrid_pipeline_calls_reconciler_after_rule_based_extraction():
    chunks = [
        build_chunk(
            chunk_index=0,
            content=(
                "This randomized clinical trial evaluated oral dosing over 12 weeks. "
                "The NOAEL of 10 mg/kg/day was retained."
            ),
        )
    ]

    result = HybridStudyDetailExtractionPipeline(
        reconciler=FakeLLMReconciler(),
    ).extract(document_chunks=chunks)

    assert result.reconciliation_status == "completed"
    assert result.route is not None
    assert result.route.value == "oral route confirmed by LLM reconciliation"
    assert result.route.extraction_method == "llm_reconciled"
    assert result.route.citations[0].quoted_text == "oral"
    assert result.notes == ["Reconciled across 1 chunks."]


def test_pipeline_collects_multiple_explicit_pod_mentions_across_chunks():
    chunks = [
        build_chunk(
            chunk_index=0,
            content=(
                "A LOAEL of 30 mg/kg/day was observed in the range-finding phase."
            ),
        ),
        build_chunk(
            chunk_index=1,
            content=(
                "In the definitive study, the NOAEL of 10 mg/kg/day was selected as the POD."
            ),
            page_number_start=2,
            page_number_end=2,
        ),
    ]

    result = HybridStudyDetailExtractionPipeline().extract(document_chunks=chunks)

    assert [field.citations[0].chunk_index for field in result.explicit_pod_mentions] == [0, 1]
    assert "LOAEL of 30 mg/kg/day" in result.explicit_pod_mentions[0].value
    assert "NOAEL of 10 mg/kg/day" in result.explicit_pod_mentions[1].value
