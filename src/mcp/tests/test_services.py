"""services 계층 단위 테스트."""

from __future__ import annotations

import pytest

from app.models import MealDish
from app.services import (
    InputValidationError,
    map_meals,
    map_schools,
    parse_dishes,
    to_neis_ymd,
    validate_date_range,
    validate_school_name,
)
from tests.conftest import MEAL_SUCCESS, SCHOOL_SUCCESS


def _rows(payload: dict, service: str) -> list[dict]:
    for block in payload[service]:
        if "row" in block:
            return block["row"]
    return []


def test_validate_school_name_rejects_blank() -> None:
    with pytest.raises(InputValidationError):
        validate_school_name("   ")


def test_validate_date_range_ok() -> None:
    start, end = validate_date_range("2026-01-01", "2026-01-31")
    assert to_neis_ymd(start) == "20260101"
    assert to_neis_ymd(end) == "20260131"


def test_validate_date_range_rejects_reversed() -> None:
    with pytest.raises(InputValidationError):
        validate_date_range("2026-02-01", "2026-01-01")


def test_validate_date_range_rejects_invalid_format() -> None:
    with pytest.raises(InputValidationError):
        validate_date_range("2026/01/01", "2026-01-31")


def test_parse_dishes_extracts_allergies() -> None:
    dishes = parse_dishes("기장밥 (5.6.13)<br/>미역국 (5.9.)<br/>제육볶음")
    assert dishes == [
        MealDish(name="기장밥", allergies=[5, 6, 13]),
        MealDish(name="미역국", allergies=[5, 9]),
        MealDish(name="제육볶음", allergies=[]),
    ]


def test_map_schools() -> None:
    schools = map_schools(_rows(SCHOOL_SUCCESS, "schoolInfo"))
    assert len(schools) == 1
    school = schools[0]
    assert school.schoolName == "서울고등학교"
    assert school.eduOfficeCode == "B10"
    assert school.schoolCode == "7010569"
    assert school.region == "서울특별시"


def test_map_meals_sorts_by_date_and_parses_fields() -> None:
    meals = map_meals(_rows(MEAL_SUCCESS, "mealServiceDietInfo"))
    assert [meal.date for meal in meals] == ["2026-01-01", "2026-01-02"]

    first = meals[0]
    assert first.dishes[0].name == "백미밥"
    assert first.dishes[1].allergies == [5, 9, 10]
    assert first.mealCount == "498"

    second = meals[1]
    assert second.dishes[0].allergies == [5, 6, 13]
    assert second.calorie == "650.5 Kcal"
    assert second.origin == "쌀 : 국내산"


def test_map_meals_empty() -> None:
    assert map_meals([]) == []
