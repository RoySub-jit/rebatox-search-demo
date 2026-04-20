from __future__ import annotations

from app.schemas.comparator_scoring import ComparatorScoringInput
from app.services.comparator_scoring import rank_comparators, score_comparator


def test_score_comparator_returns_full_score_for_strong_match():
    result = score_comparator(
        ComparatorScoringInput(
            comparator_name="Comparator Alpha",
            same_target=True,
            same_modality=True,
            same_route=True,
            same_indication=True,
            same_scaffold=True,
        )
    )

    assert result.comparator_name == "Comparator Alpha"
    assert result.relevance_score == 100.0
    assert "strong comparator match" in result.rationale
    assert "same target (+35%)" in result.rationale
    assert "same scaffold (+5%)" in result.rationale


def test_score_comparator_returns_partial_score_for_partial_match():
    result = score_comparator(
        ComparatorScoringInput(
            comparator_name="Comparator Beta",
            same_target=True,
            same_modality=False,
            same_route=True,
            same_indication=True,
            same_scaffold=False,
        )
    )

    assert result.relevance_score == 70.0
    assert "partial comparator match" in result.rationale
    assert "same target (+35%)" in result.rationale
    assert "Remaining gaps" in result.rationale
    assert "same modality" in result.rationale


def test_score_comparator_returns_low_score_for_weak_match():
    result = score_comparator(
        ComparatorScoringInput(
            comparator_name="Comparator Gamma",
            same_scaffold=True,
        )
    )

    assert result.relevance_score == 5.0
    assert "weak comparator match" in result.rationale
    assert "same scaffold (+5%)" in result.rationale


def test_score_comparator_handles_missing_comparator():
    result = score_comparator(None)

    assert result.comparator_name is None
    assert result.relevance_score == 0.0
    assert result.rationale == (
        "No comparator was provided, so no biologics relevance score could be assigned."
    )


def test_rank_comparators_orders_results_by_relevance_score():
    ranked = rank_comparators(
        [
            ComparatorScoringInput(comparator_name="Comparator Gamma", same_scaffold=True),
            ComparatorScoringInput(
                comparator_name="Comparator Alpha",
                same_target=True,
                same_modality=True,
                same_route=True,
                same_indication=True,
                same_scaffold=True,
            ),
            ComparatorScoringInput(
                comparator_name="Comparator Beta",
                same_target=True,
                same_route=True,
                same_indication=True,
            ),
        ]
    )

    assert [item.comparator_name for item in ranked] == [
        "Comparator Alpha",
        "Comparator Beta",
        "Comparator Gamma",
    ]
    assert [item.relevance_score for item in ranked] == [100.0, 70.0, 5.0]
