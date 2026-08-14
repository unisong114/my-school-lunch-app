"""급식 배틀 점수 계산."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Final, Literal


AREA_LABELS: Final[dict[str, str]] = {
    "nutritionBalance": "영양 균형",
    "healthiness": "건강성",
    "menuQuality": "식재료 및 메뉴 품질",
    "mealParticipation": "급식 참여도",
}

AREA_WEIGHTS: Final[dict[str, Decimal]] = {
    "nutritionBalance": Decimal("40"),
    "healthiness": Decimal("25"),
    "menuQuality": Decimal("20"),
    "mealParticipation": Decimal("15"),
}


def validate_area_scores(area_scores: dict[str, int]) -> None:
    """영역 점수의 필수 키와 범위를 검증합니다."""

    missing_areas = [area for area in AREA_WEIGHTS if area not in area_scores]
    if missing_areas:
        missing_labels = ", ".join(AREA_LABELS[area] for area in missing_areas)
        raise ValueError(f"필수 평가 영역 점수가 없습니다: {missing_labels}")

    for area, score in area_scores.items():
        if area not in AREA_WEIGHTS:
            raise ValueError(f"알 수 없는 평가 영역입니다: {area}")
        if not 1 <= score <= 5:
            raise ValueError(f"{AREA_LABELS[area]} 점수는 1~5 사이여야 합니다.")

    if sum(AREA_WEIGHTS.values()) != Decimal("100"):
        raise ValueError("평가 가중치 합이 100이 아닙니다.")


def calculate_weighted_score(score: int, weight: Decimal) -> float:
    """`(평점 / 5) × 가중치`를 소수 첫째 자리까지 계산합니다."""

    if not 1 <= score <= 5:
        raise ValueError("평점은 1~5 사이여야 합니다.")
    weighted = (Decimal(score) / Decimal("5")) * weight
    return float(weighted.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def calculate_school_scores(area_scores: dict[str, int]) -> tuple[dict[str, float], float]:
    """학교 한 곳의 영역별 환산 점수와 총점을 계산합니다."""

    validate_area_scores(area_scores)
    weighted_scores = {
        area: calculate_weighted_score(score, AREA_WEIGHTS[area])
        for area, score in area_scores.items()
    }
    total = float(sum(Decimal(str(value)) for value in weighted_scores.values()))
    return weighted_scores, round(total, 1)


def determine_winner(total_a: float, total_b: float) -> Literal["A", "B", "tie"]:
    """총점을 비교해 승패를 결정합니다."""

    score_a = Decimal(str(total_a))
    score_b = Decimal(str(total_b))
    if score_a == score_b:
        return "tie"
    return "A" if score_a > score_b else "B"
