"""NEIS 공개 API 비동기 클라이언트."""

from __future__ import annotations

from typing import Any

import httpx

from .exceptions import NeisUpstreamError

_CODE_SUCCESS = "INFO-000"
_CODE_NO_DATA = "INFO-200"


def _extract_result(payload: dict[str, Any]) -> tuple[str, str]:
    """최상위 RESULT 코드를 추출합니다."""
    result = payload.get("RESULT")
    if isinstance(result, dict):
        return str(result.get("CODE", "")), str(result.get("MESSAGE", ""))
    return "", ""


def _extract_head_result(block: dict[str, Any]) -> tuple[str, str]:
    """head 블록의 RESULT 코드를 추출합니다."""
    for item in block.get("head", []):
        if isinstance(item, dict) and isinstance(item.get("RESULT"), dict):
            result = item["RESULT"]
            return str(result.get("CODE", "")), str(result.get("MESSAGE", ""))
    return "", ""


def _parse_rows(payload: dict[str, Any], service_name: str) -> list[dict[str, Any]]:
    """NEIS 서비스 응답에서 row 목록을 추출합니다."""
    if service_name not in payload:
        code, message = _extract_result(payload)
        if code == _CODE_NO_DATA:
            return []
        raise NeisUpstreamError(
            message or "NEIS API가 올바르지 않은 응답을 반환했습니다.",
            code=code or None,
        )

    service = payload[service_name]
    if not isinstance(service, list):
        raise NeisUpstreamError("NEIS API 응답 형식이 올바르지 않습니다.")

    rows: list[dict[str, Any]] = []
    for block in service:
        if not isinstance(block, dict):
            continue
        if "head" in block:
            code, message = _extract_head_result(block)
            if code == _CODE_NO_DATA:
                return []
            if code not in ("", _CODE_SUCCESS):
                raise NeisUpstreamError(message or "NEIS API 오류가 발생했습니다.", code=code)
        if "row" in block and isinstance(block["row"], list):
            rows.extend(item for item in block["row"] if isinstance(item, dict))
    return rows


class NeisClient:
    """NEIS API 클라이언트."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        timeout: float = 10.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout
        self._client = client

    async def _request(
        self,
        path: str,
        service_name: str,
        params: dict[str, Any],
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {"Type": "json", "pIndex": 1, "pSize": 100}
        if self._api_key:
            query["KEY"] = self._api_key
        query.update({key: value for key, value in params.items() if value is not None})

        url = f"{self._base_url}/{path}"
        try:
            if self._client is not None:
                response = await self._client.get(url, params=query)
            else:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.get(url, params=query)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise NeisUpstreamError("NEIS API 호출에 실패했습니다.") from exc
        except ValueError as exc:
            raise NeisUpstreamError("NEIS API 응답을 해석할 수 없습니다.") from exc

        if not isinstance(payload, dict):
            raise NeisUpstreamError("NEIS API 응답 형식이 올바르지 않습니다.")
        return _parse_rows(payload, service_name)

    async def search_schools(self, name: str) -> list[dict[str, Any]]:
        """부분 학교명으로 학교를 검색합니다."""
        return await self._request("schoolInfo", "schoolInfo", {"SCHUL_NM": name})

    async def fetch_meals(
        self,
        *,
        edu_office_code: str,
        school_code: str,
        from_ymd: str,
        to_ymd: str,
        meal_code: str = "2",
    ) -> list[dict[str, Any]]:
        """학교와 날짜 범위로 급식을 조회합니다."""
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
