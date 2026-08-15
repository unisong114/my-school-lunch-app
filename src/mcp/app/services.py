"""비즈니스 로직 계층.

NEIS 원시 데이터를 MCP 도구 응답 모델로 가공하고, 날짜 범위 유효성 검사와
급식 메뉴 파싱을 담당합니다.
"""

from __future__ import annotations

import re
from datetime import date, datetime

from .exceptions import ToolInputError
from .models import DailyMeal, MealDish, School

_ALLERGY_PATTERN = re.compile(r"\(([\d.\s]+)\)\s*$")
_DISH_SEPARATOR = re.compile(r"<br\s*/?>", re.IGNORECASE)


def parse_date(value: str, field: str) -> date:
    """``YYYY-MM-DD`` 문자열을 ``date`` 로 변환합니다."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError) as exc:
        raise ToolInputError(
            f"{field} 값이 올바른 날짜(YYYY-MM-DD) 형식이 아닙니다: {value!r}"
        ) from exc


def validate_date_range(from_date: str, to_date: str) -> tuple[date, date]:
    """시작일과 종료일을 검증합니다.

    시작일이 종료일보다 이후이면 :class:`ToolInputError` 를 발생시킵니다.
    """
    start = parse_date(from_date, "시작일")
    end = parse_date(to_date, "종료일")
    if start > end:
        raise ToolInputError("시작일은 종료일보다 이후일 수 없습니다.")
    return start, end


def to_neis_ymd(value: date) -> str:
    """``date`` 를 NEIS 형식(``YYYYMMDD``)으로 변환합니다."""
    return value.strftime("%Y%m%d")


def _format_ymd(raw: str) -> str:
    """``YYYYMMDD`` 를 ``YYYY-MM-DD`` 로 변환합니다."""
    raw = (raw or "").strip()
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"
    return raw


def _stringify(raw: object) -> str | None:
    """NEIS 응답 값을 문자열로 정규화합니다.

    ``MLSV_FGR``(급식인원수) 등 일부 필드는 NEIS가 문자열이 아닌 숫자(int/float)로
    내려주는 경우가 있어, Pydantic 모델의 ``str`` 필드 검증 오류를 막기 위해
    명시적으로 문자열 변환한다. 정수값 float(예: ``635.0``)는 ``.0``을 제거해
    사람이 읽기 자연스러운 정수 표기로 변환한다.
    """
    if raw is None or raw == "":
        return None
    if isinstance(raw, float) and raw.is_integer():
        return str(int(raw))
    return str(raw)


def _parse_dishes(raw: str | None) -> list[MealDish]:
    """``DDISH_NM`` 문자열을 요리 목록으로 파싱합니다.

    각 요리는 ``<br/>`` 로 구분되며, 알레르기 유발 번호는 요리명 뒤 괄호 안에
    ``(5.6.)`` 형태로 표기됩니다.
    """
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


def map_schools(rows: list[dict]) -> list[School]:
    """NEIS 학교 row 목록을 :class:`School` 목록으로 변환합니다."""
    schools: list[School] = []
    for row in rows:
        schools.append(
            School(
                eduOfficeCode=str(row.get("ATPT_OFCDC_SC_CODE", "")).strip(),
                eduOfficeName=str(row.get("ATPT_OFCDC_SC_NM", "")).strip(),
                schoolCode=str(row.get("SD_SCHUL_CODE", "")).strip(),
                schoolName=str(row.get("SCHUL_NM", "")).strip(),
                schoolKind=(row.get("SCHUL_KND_SC_NM") or None),
                region=(row.get("LCTN_SC_NM") or None),
                address=(row.get("ORG_RDNMA") or None),
            )
        )
    return schools


def map_meals(rows: list[dict]) -> list[DailyMeal]:
    """NEIS 급식 row 목록을 날짜순 :class:`DailyMeal` 목록으로 변환합니다."""
    meals: list[DailyMeal] = []
    for row in rows:
        meals.append(
            DailyMeal(
                date=_format_ymd(str(row.get("MLSV_YMD", ""))),
                mealName=str(row.get("MMEAL_SC_NM") or "중식"),
                dishes=_parse_dishes(row.get("DDISH_NM")),
                calorie=(row.get("CAL_INFO") or None),
                nutrition=(row.get("NTR_INFO") or None),
                origin=(row.get("ORPLC_INFO") or None),
                mealCount=_stringify(row.get("MLSV_FGR")),
            )
        )
    meals.sort(key=lambda meal: meal.date)
    return meals
