"""NEIS 클라이언트 단위 테스트."""

from __future__ import annotations

import httpx
import pytest
import respx

from app.exceptions import NeisUpstreamError
from app.neis_client import NeisClient
from tests.conftest import ERROR_LIMIT, HEAD_ERROR, MEAL_SUCCESS, NO_DATA, SCHOOL_SUCCESS

BASE_URL = "https://open.neis.go.kr/hub"


def _client(api_key: str = "test-key") -> NeisClient:
    return NeisClient(base_url=BASE_URL, api_key=api_key)


@respx.mock
async def test_search_schools_success() -> None:
    respx.get(f"{BASE_URL}/schoolInfo").mock(
        return_value=httpx.Response(200, json=SCHOOL_SUCCESS)
    )
    rows = await _client().search_schools("서울")
    assert len(rows) == 1
    assert rows[0]["SCHUL_NM"] == "서울고등학교"


@respx.mock
async def test_search_schools_no_data_returns_empty() -> None:
    respx.get(f"{BASE_URL}/schoolInfo").mock(
        return_value=httpx.Response(200, json=NO_DATA)
    )
    rows = await _client().search_schools("없는학교")
    assert rows == []


@respx.mock
async def test_fetch_meals_success_sends_lunch_code() -> None:
    route = respx.get(f"{BASE_URL}/mealServiceDietInfo").mock(
        return_value=httpx.Response(200, json=MEAL_SUCCESS)
    )
    rows = await _client().fetch_meals(
        edu_office_code="B10",
        school_code="7010569",
        from_ymd="20260101",
        to_ymd="20260131",
    )
    assert len(rows) == 2
    request = route.calls.last.request
    assert request.url.params["MMEAL_SC_CODE"] == "2"
    assert request.url.params["MLSV_FROM_YMD"] == "20260101"
    assert request.url.params["KEY"] == "test-key"


@respx.mock
async def test_blank_api_key_omits_key_param() -> None:
    route = respx.get(f"{BASE_URL}/schoolInfo").mock(
        return_value=httpx.Response(200, json=SCHOOL_SUCCESS)
    )
    await _client(api_key="").search_schools("서울")
    request = route.calls.last.request
    assert "KEY" not in request.url.params


@respx.mock
async def test_top_level_error_code_raises() -> None:
    respx.get(f"{BASE_URL}/schoolInfo").mock(
        return_value=httpx.Response(200, json=ERROR_LIMIT)
    )
    with pytest.raises(NeisUpstreamError):
        await _client().search_schools("서울")


@respx.mock
async def test_head_error_code_raises() -> None:
    respx.get(f"{BASE_URL}/schoolInfo").mock(
        return_value=httpx.Response(200, json=HEAD_ERROR)
    )
    with pytest.raises(NeisUpstreamError):
        await _client().search_schools("서울")


@respx.mock
async def test_http_error_raises() -> None:
    respx.get(f"{BASE_URL}/schoolInfo").mock(
        return_value=httpx.Response(500, text="server error")
    )
    with pytest.raises(NeisUpstreamError):
        await _client().search_schools("서울")
