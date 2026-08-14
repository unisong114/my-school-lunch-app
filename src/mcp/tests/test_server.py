"""FastMCP 도구 통합 테스트."""

from __future__ import annotations

import json
from typing import Any

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from app.exceptions import NeisUpstreamError
from app.server import create_mcp_server


class FakeNeisClient:
    """테스트용 가짜 NEIS 클라이언트."""

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


def _text(result: Any) -> str:
    return result.content[0].text


@pytest.mark.asyncio
async def test_list_tools_exposes_exact_names() -> None:
    server = create_mcp_server(FakeNeisClient())
    async with create_connected_server_and_client_session(server) as session:
        tools = await session.list_tools()

    tool_map = {tool.name: tool for tool in tools.tools}
    assert set(tool_map) == {"search_schools", "get_meals"}
    assert "name" in tool_map["search_schools"].inputSchema["properties"]
    assert set(tool_map["get_meals"].inputSchema["properties"]) == {
        "edu_office_code",
        "school_code",
        "from_date",
        "to_date",
    }


@pytest.mark.asyncio
async def test_search_schools_returns_json_array() -> None:
    fake = FakeNeisClient(
        schools=[
            {
                "ATPT_OFCDC_SC_CODE": "B10",
                "ATPT_OFCDC_SC_NM": "서울특별시교육청",
                "SD_SCHUL_CODE": "7010569",
                "SCHUL_NM": "서울고등학교",
                "SCHUL_KND_SC_NM": "고등학교",
                "LCTN_SC_NM": "서울특별시",
                "ORG_RDNMA": "서울특별시 서초구 남부순환로",
            }
        ]
    )
    server = create_mcp_server(fake)
    async with create_connected_server_and_client_session(server) as session:
        result = await session.call_tool("search_schools", {"name": " 서울 "})

    assert result.isError is False
    payload = json.loads(_text(result))
    assert fake.calls["search"] == "서울"
    assert payload == [
        {
            "eduOfficeCode": "B10",
            "eduOfficeName": "서울특별시교육청",
            "schoolCode": "7010569",
            "schoolName": "서울고등학교",
            "schoolKind": "고등학교",
            "region": "서울특별시",
            "address": "서울특별시 서초구 남부순환로",
        }
    ]


@pytest.mark.asyncio
async def test_search_schools_maps_blank_input_to_mcp_error() -> None:
    server = create_mcp_server(FakeNeisClient())
    async with create_connected_server_and_client_session(server) as session:
        result = await session.call_tool("search_schools", {"name": "   "})

    assert result.isError is True
    assert _text(result) == "학교 이름은(는) 비워 둘 수 없습니다."


@pytest.mark.asyncio
async def test_search_schools_maps_no_data_to_mcp_error() -> None:
    server = create_mcp_server(FakeNeisClient(schools=[]))
    async with create_connected_server_and_client_session(server) as session:
        result = await session.call_tool("search_schools", {"name": "없는학교"})

    assert result.isError is True
    assert _text(result) == "조건에 맞는 학교를 찾을 수 없습니다."


@pytest.mark.asyncio
async def test_get_meals_returns_json_object_and_lunch_only() -> None:
    fake = FakeNeisClient(
        meals=[
            {
                "MLSV_YMD": "20260102",
                "MMEAL_SC_NM": "중식",
                "DDISH_NM": "기장밥 (5.6.13)<br/>미역국 (5.9.)",
                "CAL_INFO": "650.5 Kcal",
                "NTR_INFO": "탄수화물(g) : 90.0",
                "ORPLC_INFO": "쌀 : 국내산",
                "MLSV_FGR": "512",
            }
        ]
    )
    server = create_mcp_server(fake)
    async with create_connected_server_and_client_session(server) as session:
        result = await session.call_tool(
            "get_meals",
            {
                "edu_office_code": "B10",
                "school_code": "7010569",
                "from_date": "2026-01-01",
                "to_date": "2026-01-31",
            },
        )

    assert result.isError is False
    assert fake.calls["meals"]["meal_code"] == "2"
    assert fake.calls["meals"]["from_ymd"] == "20260101"
    payload = json.loads(_text(result))
    assert payload["schoolCode"] == "7010569"
    assert payload["meals"][0]["dishes"][0]["allergies"] == [5, 6, 13]
    assert payload["meals"][0]["mealCount"] == "512"
    assert result.structuredContent == payload


@pytest.mark.asyncio
async def test_get_meals_maps_invalid_date_to_mcp_error() -> None:
    server = create_mcp_server(FakeNeisClient())
    async with create_connected_server_and_client_session(server) as session:
        result = await session.call_tool(
            "get_meals",
            {
                "edu_office_code": "B10",
                "school_code": "7010569",
                "from_date": "2026-02-01",
                "to_date": "2026-01-01",
            },
        )

    assert result.isError is True
    assert _text(result) == "시작일은 종료일보다 늦을 수 없습니다."


@pytest.mark.asyncio
async def test_get_meals_maps_no_data_to_mcp_error() -> None:
    server = create_mcp_server(FakeNeisClient(meals=[]))
    async with create_connected_server_and_client_session(server) as session:
        result = await session.call_tool(
            "get_meals",
            {
                "edu_office_code": "B10",
                "school_code": "7010569",
                "from_date": "2026-01-01",
                "to_date": "2026-01-31",
            },
        )

    assert result.isError is True
    assert _text(result) == "선택한 기간에 급식 정보가 없습니다."


@pytest.mark.asyncio
async def test_upstream_error_maps_to_mcp_error() -> None:
    fake = FakeNeisClient(error=NeisUpstreamError("장애"))
    server = create_mcp_server(fake)
    async with create_connected_server_and_client_session(server) as session:
        result = await session.call_tool("search_schools", {"name": "서울"})

    assert result.isError is True
    assert "잠시 후 다시 시도해 주세요." in _text(result)
