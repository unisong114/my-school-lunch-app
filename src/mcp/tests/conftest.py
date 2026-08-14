"""테스트 공용 픽스처 및 NEIS 샘플 응답."""

from __future__ import annotations

from typing import Any

import pytest

SCHOOL_SUCCESS: dict[str, Any] = {
    "schoolInfo": [
        {
            "head": [
                {"list_total_count": 1},
                {"RESULT": {"CODE": "INFO-000", "MESSAGE": "정상 처리되었습니다."}},
            ]
        },
        {
            "row": [
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
        },
    ]
}

MEAL_SUCCESS: dict[str, Any] = {
    "mealServiceDietInfo": [
        {
            "head": [
                {"list_total_count": 2},
                {"RESULT": {"CODE": "INFO-000", "MESSAGE": "정상 처리되었습니다."}},
            ]
        },
        {
            "row": [
                {
                    "MLSV_YMD": "20260102",
                    "MMEAL_SC_NM": "중식",
                    "DDISH_NM": "기장밥 (5.6.)<br/>미역국 (5.9.)<br/>제육볶음",
                    "CAL_INFO": "650.5 Kcal",
                    "NTR_INFO": "탄수화물(g) : 90.0",
                    "ORPLC_INFO": "쌀 : 국내산",
                    "MLSV_FGR": "512",
                },
                {
                    "MLSV_YMD": "20260101",
                    "MMEAL_SC_NM": "중식",
                    "DDISH_NM": "백미밥<br/>김치찌개 (5.9.10.)",
                    "CAL_INFO": "700.0 Kcal",
                    "NTR_INFO": "탄수화물(g) : 95.0",
                    "ORPLC_INFO": "김치 : 국내산",
                    "MLSV_FGR": "498",
                },
            ]
        },
    ]
}

NO_DATA: dict[str, Any] = {
    "RESULT": {"CODE": "INFO-200", "MESSAGE": "해당하는 데이터가 없습니다."}
}

ERROR_LIMIT: dict[str, Any] = {
    "RESULT": {"CODE": "INFO-300", "MESSAGE": "인증키가 유효하지 않습니다."}
}


@pytest.fixture(autouse=True)
def _test_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """테스트에서는 고정된 설정을 사용하도록 캐시를 초기화합니다."""
    from app.config import get_settings

    monkeypatch.setenv("NEIS_API_KEY", "test-key")
    monkeypatch.setenv("NEIS_BASE_URL", "https://open.neis.go.kr/hub")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
