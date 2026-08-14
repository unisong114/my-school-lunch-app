"""MCP 서버 비즈니스 로직."""

from __future__ import annotations

import re
from datetime import date, datetime

from .models import DailyMeal, MealDish, School

_ALLERGY_PATTERN = re.compile(r"\(([\d.\s]+)\)\s*$")
_DISH_SEPARATOR = re.compile(r"<br\s*/?>", re.IGNORECASE)


class InputValidationError(ValueError):
    """입력값 검증 예외."""


def validate_required_text(value: str, field_name: str) -> str:
    """필수 문자열을 검증하고 공백을 제거합니다."""
    text = value.strip()
    if not text:
        raise InputValidationError(f"{field_name}은(는) 비워 둘 수 없습니다.")
    return text


def validate_school_name(name: str) -> str:
    """학교 검색어를 검증합니다."""
    return validate_required_text(name, "학교 이름")


def parse_date(value: str, field_name: str) -> date:
    """YYYY-MM-DD 문자열을 date로 변환합니다."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError) as exc:
        raise InputValidationError(f"{field_name}은(는) YYYY-MM-DD 형식이어야 합니다.") from exc


def validate_date_range(from_date: str, to_date: str) -> tuple[date, date]:
    """시작일과 종료일을 검증합니다."""
    start = parse_date(from_date, "시작일")
    end = parse_date(to_date, "종료일")
    if start > end:
        raise InputValidationError("시작일은 종료일보다 늦을 수 없습니다.")
    return start, end


def to_neis_ymd(value: date) -> str:
    """date를 NEIS YYYYMMDD 형식으로 변환합니다."""
    return value.strftime("%Y%m%d")


def _optional_text(value: object) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _format_ymd(raw: str) -> str:
    raw = (raw or "").strip()
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"
    return raw


def parse_dishes(raw: str | None) -> list[MealDish]:
    """DDISH_NM 문자열을 요리 목록으로 파싱합니다."""
    if not raw:
        return []

    dishes: list[MealDish] = []
    for chunk in _DISH_SEPARATOR.split(raw):
        text = chunk.strip()
        if not text:
            continue

        allergies: list[int] = []
        match = _ALLERGY_PATTERN.search(text)
        if match:
            allergies = [
                int(token)
                for token in re.split(r"[.\s]+", match.group(1))
                if token.strip().isdigit()
            ]
            text = text[: match.start()].strip()

        if text:
            dishes.append(MealDish(name=text, allergies=allergies))
    return dishes


def map_schools(rows: list[dict[str, object]]) -> list[School]:
    """NEIS 학교 row를 School 목록으로 변환합니다."""
    return [
        School(
            eduOfficeCode=str(row.get("ATPT_OFCDC_SC_CODE", "")).strip(),
            eduOfficeName=str(row.get("ATPT_OFCDC_SC_NM", "")).strip(),
            schoolCode=str(row.get("SD_SCHUL_CODE", "")).strip(),
            schoolName=str(row.get("SCHUL_NM", "")).strip(),
            schoolKind=_optional_text(row.get("SCHUL_KND_SC_NM")),
            region=_optional_text(row.get("LCTN_SC_NM")),
            address=_optional_text(row.get("ORG_RDNMA")),
        )
        for row in rows
    ]


def map_meals(rows: list[dict[str, object]]) -> list[DailyMeal]:
    """NEIS 급식 row를 DailyMeal 목록으로 변환합니다."""
    meals = [
        DailyMeal(
            date=_format_ymd(str(row.get("MLSV_YMD", ""))),
            mealName=_optional_text(row.get("MMEAL_SC_NM")) or "중식",
            dishes=parse_dishes(_optional_text(row.get("DDISH_NM"))),
            calorie=_optional_text(row.get("CAL_INFO")),
            nutrition=_optional_text(row.get("NTR_INFO")),
            origin=_optional_text(row.get("ORPLC_INFO")),
            mealCount=_optional_text(row.get("MLSV_FGR")),
        )
        for row in rows
    ]
    meals.sort(key=lambda meal: meal.date)
    return meals
