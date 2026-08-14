"""엔드포인트 통합 테스트 (NEIS 클라이언트 모킹)."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_neis_client
from app.exceptions import NeisUpstreamError
from app.main import app


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


def _client(fake: FakeNeisClient) -> TestClient:
    app.dependency_overrides[get_neis_client] = lambda: fake
    return TestClient(app)


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


def test_health() -> None:
    resp = TestClient(app).get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_sample_schools_returns_ten() -> None:
    resp = _client(FakeNeisClient()).get("/api/schools/sample")
    assert resp.status_code == 200
    schools = resp.json()["schools"]
    assert len(schools) == 10
    codes = {(s["eduOfficeCode"], s["schoolCode"]) for s in schools}
    assert len(codes) == 10  # 중복 없음


def test_search_schools_ok() -> None:
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
    resp = _client(fake).get("/api/schools", params={"name": "서울"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["schools"]) == 1
    assert body["schools"][0]["schoolName"] == "서울고등학교"
    assert fake.calls["search"] == "서울"


def test_search_schools_empty() -> None:
    resp = _client(FakeNeisClient(schools=[])).get(
        "/api/schools", params={"name": "없는학교"}
    )
    assert resp.status_code == 200
    assert resp.json()["schools"] == []


def test_search_schools_requires_name() -> None:
    resp = _client(FakeNeisClient()).get("/api/schools")
    assert resp.status_code == 422


def test_search_schools_upstream_error() -> None:
    fake = FakeNeisClient(error=NeisUpstreamError("장애", code="ERROR-500"))
    resp = _client(fake).get("/api/schools", params={"name": "서울"})
    assert resp.status_code == 502


def test_meals_ok_lunch_only() -> None:
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
    resp = _client(fake).get(
        "/api/meals",
        params={
            "eduOfficeCode": "B10",
            "schoolCode": "7010569",
            "fromDate": "2026-01-01",
            "toDate": "2026-01-31",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["schoolCode"] == "7010569"
    assert len(body["meals"]) == 1
    assert body["meals"][0]["dishes"][1]["allergies"] == [5, 9]
    assert fake.calls["meals"]["meal_code"] == "2"


def test_meals_invalid_date_range() -> None:
    resp = _client(FakeNeisClient()).get(
        "/api/meals",
        params={
            "eduOfficeCode": "B10",
            "schoolCode": "7010569",
            "fromDate": "2026-02-01",
            "toDate": "2026-01-01",
        },
    )
    assert resp.status_code == 400


def test_meals_empty_result() -> None:
    resp = _client(FakeNeisClient(meals=[])).get(
        "/api/meals",
        params={
            "eduOfficeCode": "B10",
            "schoolCode": "7010569",
            "fromDate": "2026-01-01",
            "toDate": "2026-01-31",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["meals"] == []


def test_meals_upstream_error() -> None:
    fake = FakeNeisClient(error=NeisUpstreamError("장애"))
    resp = _client(fake).get(
        "/api/meals",
        params={
            "eduOfficeCode": "B10",
            "schoolCode": "7010569",
            "fromDate": "2026-01-01",
            "toDate": "2026-01-31",
        },
    )
    assert resp.status_code == 502
