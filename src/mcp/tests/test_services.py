"""services 계층 단위 테스트."""

from __future__ import annotations

import pytest

from app.exceptions import ToolInputError
from app.services import (
    map_meals,
    map_schools,
    to_neis_ymd,
    validate_date_range,
)
from tests.conftest import MEAL_SUCCESS, SCHOOL_SUCCESS


def _rows(payload: dict, service: str) -> list[dict]:
    for block in payload[service]:
        if "row" in block:
            return block["row"]
    return []


def test_validate_date_range_ok() -> None:
    start, end = validate_date_range("2026-01-01", "2026-01-31")
    assert to_neis_ymd(start) == "20260101"
    assert to_neis_ymd(end) == "20260131"


def test_validate_date_range_rejects_reversed() -> None:
    with pytest.raises(ToolInputError):
        validate_date_range("2026-02-01", "2026-01-01")


def test_validate_date_range_rejects_invalid_format() -> None:
    with pytest.raises(ToolInputError):
        validate_date_range("2026/01/01", "2026-01-31")


def test_map_schools() -> None:
    schools = map_schools(_rows(SCHOOL_SUCCESS, "schoolInfo"))
    assert len(schools) == 1
    school = schools[0]
    assert school.schoolName == "서울고등학교"
    assert school.eduOfficeCode == "B10"
    assert school.schoolCode == "7010569"
    assert school.region == "서울특별시"


def test_map_meals_sorts_by_date_and_parses_dishes() -> None:
    meals = map_meals(_rows(MEAL_SUCCESS, "mealServiceDietInfo"))
    assert [m.date for m in meals] == ["2026-01-01", "2026-01-02"]

    first = meals[0]
    assert first.date == "2026-01-01"
    assert first.dishes[0].name == "백미밥"
    assert first.dishes[0].allergies == []
    assert first.dishes[1].name == "김치찌개"
    assert first.dishes[1].allergies == [5, 9, 10]
    assert first.mealCount == "498"

    second = meals[1]
    assert [d.name for d in second.dishes] == ["기장밥", "미역국", "제육볶음"]
    assert second.dishes[0].allergies == [5, 6]
    assert second.calorie == "650.5 Kcal"
    assert second.mealCount == "512"


def test_map_meals_empty() -> None:
    assert map_meals([]) == []
