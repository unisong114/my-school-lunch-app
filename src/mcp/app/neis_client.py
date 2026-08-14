"""NEIS 공개 API 클라이언트.

`data/openapi.json` 명세(외부 API 계약)를 근거로 학교 기본정보와 급식식단정보를
조회합니다. 기존 백엔드 API 앱과 동일한 NEIS 응답 해석 규칙을 사용하지만, MCP
서버는 백엔드를 경유하지 않고 이 클라이언트로 NEIS API를 직접 호출합니다.
"""

from __future__ import annotations

from typing import Any

import httpx

from .exceptions import NeisUpstreamError

# NEIS 결과 코드 (RESULT.CODE)
_CODE_SUCCESS = "INFO-000"
_CODE_NO_DATA = "INFO-200"


def _extract_result(payload: dict[str, Any]) -> tuple[str, str]:
    """응답에서 RESULT 코드와 메시지를 추출합니다.

    데이터가 없을 때 NEIS는 최상위에 ``RESULT`` 객체만 반환합니다.
    """
    result = payload.get("RESULT")
    if isinstance(result, dict):
        return str(result.get("CODE", "")), str(result.get("MESSAGE", ""))
    return "", ""


def _parse_rows(payload: dict[str, Any], service_name: str) -> list[dict[str, Any]]:
    """NEIS 서비스 응답에서 row 목록을 추출합니다.

    성공 응답 구조:
        ``{ service_name: [ {"head": [...]}, {"row": [...]} ] }``
    데이터 없음:
        ``{ "RESULT": {"CODE": "INFO-200", ...} }`` → 빈 목록 반환
    그 외 오류 코드는 :class:`NeisUpstreamError` 로 변환합니다.
    """
    # 최상위 RESULT 만 있는 경우 (데이터 없음 또는 오류)
    if service_name not in payload:
        code, message = _extract_result(payload)
        if code == _CODE_NO_DATA:
            return []
        raise NeisUpstreamError(
            message or "NEIS API가 데이터를 반환하지 않았습니다.", code=code or None
        )

    service = payload[service_name]
    if not isinstance(service, list):
        raise NeisUpstreamError("NEIS 응답 형식이 올바르지 않습니다.")

    rows: list[dict[str, Any]] = []
    for block in service:
        if not isinstance(block, dict):
            continue
        # head 블록에 오류 코드가 담기는 경우 검증
        if "head" in block:
            for head_item in block.get("head", []):
                if isinstance(head_item, dict) and "RESULT" in head_item:
                    result = head_item["RESULT"]
                    code = str(result.get("CODE", ""))
                    if code not in ("", _CODE_SUCCESS, _CODE_NO_DATA):
                        raise NeisUpstreamError(
                            str(result.get("MESSAGE", "NEIS API 오류")), code=code
                        )
        if "row" in block and isinstance(block["row"], list):
            rows.extend(item for item in block["row"] if isinstance(item, dict))
    return rows


class NeisClient:
    """NEIS 공개 API 비동기 클라이언트."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        timeout: float = 10.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout
        self._client = client

    async def _request(
        self, path: str, service_name: str, params: dict[str, Any]
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {"Type": "json", "pIndex": 1, "pSize": 100}
        if self._api_key:
            query["KEY"] = self._api_key
        query.update({k: v for k, v in params.items() if v is not None})

        url = f"{self._base_url}/{path}"
        try:
            if self._client is not None:
                response = await self._client.get(url, params=query)
            else:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.get(url, params=query)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:  # 네트워크/타임아웃/상태 오류
            # 예외 문자열에는 인증 키가 포함된 요청 URL이 담길 수 있으므로
            # MCP 클라이언트에게는 일반화된 메시지만 전달합니다.
            raise NeisUpstreamError(
                "NEIS API 호출에 실패했습니다. 잠시 후 다시 시도해 주세요."
            ) from exc
        except ValueError as exc:  # JSON 파싱 실패
            raise NeisUpstreamError("NEIS API 응답을 해석할 수 없습니다.") from exc

        if not isinstance(payload, dict):
            raise NeisUpstreamError("NEIS API 응답 형식이 올바르지 않습니다.")
        return _parse_rows(payload, service_name)

    async def search_schools(self, name: str) -> list[dict[str, Any]]:
        """부분 학교명으로 학교를 검색합니다."""
        return await self._request(
            "schoolInfo", "schoolInfo", {"SCHUL_NM": name}
        )

    async def fetch_meals(
        self,
        *,
        edu_office_code: str,
        school_code: str,
        from_ymd: str,
        to_ymd: str,
        meal_code: str = "2",
    ) -> list[dict[str, Any]]:
        """학교 코드와 날짜 범위로 급식식단정보를 조회합니다.

        ``meal_code`` 기본값 ``"2"`` 는 중식(점심)을 의미합니다.
        """
        return await self._request(
            "mealServiceDietInfo",
            "mealServiceDietInfo",
            {
                "ATPT_OFCDC_SC_CODE": edu_office_code,
                "SD_SCHUL_CODE": school_code,
                "MMEAL_SC_CODE": meal_code,
                "MLSV_FROM_YMD": from_ymd,
                "MLSV_TO_YMD": to_ymd,
            },
        )
