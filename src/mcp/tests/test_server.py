"""MCP 도구(search_schools, get_meals) 통합 테스트.

FastMCP의 ``@mcp.tool()`` 데코레이터는 원본 함수를 그대로 반환하므로, 도구
함수를 직접 호출해 입력 검증, NEIS 클라이언트 연동, 오류 응답을 검증합니다.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.exceptions import NeisUpstreamError, ToolInputError, ToolNoResultError
from app.server import get_meals, search_schools


class FakeNeisClient:
    """의존성 주입으로 교체할 가짜 NEIS 클라이언트."""

    def __init__(
        self,
        *,
        schools: list[dict[str, Any]] | None = None,
        meals: list[dict[str, Any]] | None = None,
        error: Exception | None = None,
    ) -> None:
        self._schools = schools or []
        self._meals = meals or []
        self._error = error
        self.calls: dict[str, Any] = {}

    async def search_schools(self, name: str) -> list[dict[str, Any]]:
        self.calls["search"] = name
        if self._error:
            raise self._error
        return self._schools

    async def fetch_meals(self, **kwargs: Any) -> list[dict[str, Any]]:
        self.calls["meals"] = kwargs
        if self._error:
            raise self._error
        return self._meals


def _set_fake(monkeypatch: pytest.MonkeyPatch, fake: FakeNeisClient) -> None:
    """``app.server`` 모듈이 참조하는 NEIS 클라이언트 팩토리를 가짜로 교체합니다."""
    monkeypatch.setattr("app.server.get_neis_client", lambda: fake)


async def test_search_schools_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeNeisClient(
        schools=[
            {
                "ATPT_OFCDC_SC_CODE": "B10",
                "ATPT_OFCDC_SC_NM": "서울특별시교육청",
                "SD_SCHUL_CODE": "7010569",
                "SCHUL_NM": "서울고등학교",
                "LCTN_SC_NM": "서울특별시",
            }
        ]
    )
    _set_fake(monkeypatch, fake)

    result = await search_schools(school_name="서울")

    assert len(result.schools) == 1
    assert result.schools[0].schoolName == "서울고등학교"
    assert fake.calls["search"] == "서울"


async def test_search_schools_requires_name(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_fake(monkeypatch, FakeNeisClient())
    with pytest.raises(ToolInputError):
        await search_schools(school_name="  ")


async def test_search_schools_no_result_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_fake(monkeypatch, FakeNeisClient(schools=[]))
    with pytest.raises(ToolNoResultError):
        await search_schools(school_name="존재하지않는학교")


async def test_search_schools_upstream_error_is_sanitized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeNeisClient(
        error=NeisUpstreamError("NEIS API 호출에 실패했습니다. 잠시 후 다시 시도해 주세요.")
    )
    _set_fake(monkeypatch, fake)
    with pytest.raises(RuntimeError) as exc_info:
        await search_schools(school_name="서울")
    assert "test-key" not in str(exc_info.value)
    assert "KEY=" not in str(exc_info.value)


async def test_get_meals_ok_lunch_only(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeNeisClient(
        meals=[
            {
                "MLSV_YMD": "20260101",
                "MMEAL_SC_NM": "중식",
                "DDISH_NM": "백미밥<br/>김치찌개 (5.9.)",
                "CAL_INFO": "700 Kcal",
            }
        ]
    )
    _set_fake(monkeypatch, fake)

    result = await get_meals(
        edu_office_code="B10",
        school_code="7010569",
        from_date="2026-01-01",
        to_date="2026-01-31",
    )

    assert result.schoolCode == "7010569"
    assert len(result.meals) == 1
    assert result.meals[0].dishes[1].allergies == [5, 9]
    assert fake.calls["meals"]["meal_code"] == "2"


async def test_get_meals_includes_meal_count(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeNeisClient(
        meals=[
            {
                "MLSV_YMD": "20260101",
                "MMEAL_SC_NM": "중식",
                "DDISH_NM": "백미밥",
                "MLSV_FGR": "512",
            }
        ]
    )
    _set_fake(monkeypatch, fake)

    result = await get_meals(
        edu_office_code="B10",
        school_code="7010569",
        from_date="2026-01-01",
        to_date="2026-01-31",
    )

    assert result.meals[0].mealCount == "512"


async def test_get_meals_invalid_date_range(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_fake(monkeypatch, FakeNeisClient())
    with pytest.raises(ToolInputError):
        await get_meals(
            edu_office_code="B10",
            school_code="7010569",
            from_date="2026-02-01",
            to_date="2026-01-01",
        )


async def test_get_meals_requires_school_code(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_fake(monkeypatch, FakeNeisClient())
    with pytest.raises(ToolInputError):
        await get_meals(
            edu_office_code="B10",
            school_code="  ",
            from_date="2026-01-01",
            to_date="2026-01-31",
        )


async def test_get_meals_no_result_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_fake(monkeypatch, FakeNeisClient(meals=[]))
    with pytest.raises(ToolNoResultError):
        await get_meals(
            edu_office_code="B10",
            school_code="7010569",
            from_date="2026-01-01",
            to_date="2026-01-31",
        )


async def test_get_meals_upstream_error_is_sanitized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeNeisClient(
        error=NeisUpstreamError("NEIS API 호출에 실패했습니다. 잠시 후 다시 시도해 주세요.")
    )
    _set_fake(monkeypatch, fake)
    with pytest.raises(RuntimeError) as exc_info:
        await get_meals(
            edu_office_code="B10",
            school_code="7010569",
            from_date="2026-01-01",
            to_date="2026-01-31",
        )
    assert "test-key" not in str(exc_info.value)
    assert "KEY=" not in str(exc_info.value)
