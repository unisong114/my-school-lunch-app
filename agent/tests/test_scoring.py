"""점수 계산 단위 테스트."""

from __future__ import annotations

import pytest

from app.scoring import AREA_WEIGHTS, calculate_school_scores, calculate_weighted_score, determine_winner


def test_weights_sum_to_100() -> None:
    assert sum(AREA_WEIGHTS.values()) == 100


@pytest.mark.parametrize(
    ("score", "weight", "expected"),
    [
        (5, AREA_WEIGHTS["nutritionBalance"], 40.0),
        (4, AREA_WEIGHTS["healthiness"], 20.0),
        (3, AREA_WEIGHTS["menuQuality"], 12.0),
        (2, AREA_WEIGHTS["mealParticipation"], 6.0),
        (1, AREA_WEIGHTS["mealParticipation"], 3.0),
    ],
)
def test_calculate_weighted_score(score: int, weight, expected: float) -> None:
    assert calculate_weighted_score(score, weight) == expected


def test_calculate_school_scores_returns_total_rounded_to_one_decimal() -> None:
    weighted, total = calculate_school_scores(
        {
            "nutritionBalance": 5,
            "healthiness": 4,
            "menuQuality": 3,
            "mealParticipation": 2,
        }
    )

    assert weighted == {
        "nutritionBalance": 40.0,
        "healthiness": 20.0,
        "menuQuality": 12.0,
        "mealParticipation": 6.0,
    }
    assert total == 78.0


def test_determine_winner_detects_a_b_and_tie() -> None:
    assert determine_winner(80.0, 79.9) == "A"
    assert determine_winner(79.9, 80.0) == "B"
    assert determine_winner(80.0, 80.0) == "tie"


def test_calculate_school_scores_raises_for_missing_area() -> None:
    with pytest.raises(ValueError, match="필수 평가 영역 점수가 없습니다"):
        calculate_school_scores(
            {
                "nutritionBalance": 5,
                "healthiness": 4,
                "menuQuality": 3,
            }
        )


def test_calculate_weighted_score_rejects_out_of_range_scores() -> None:
    with pytest.raises(ValueError, match="평점은 1~5 사이여야 합니다."):
        calculate_weighted_score(0, AREA_WEIGHTS["nutritionBalance"])
