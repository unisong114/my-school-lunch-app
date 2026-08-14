"""급식배틀 MCP 서버."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, TextContent

from .config import get_settings
from .exceptions import NeisUpstreamError
from .models import MealQueryResponse
from .neis_client import NeisClient
from .services import (
    InputValidationError,
    map_meals,
    map_schools,
    to_neis_ymd,
    validate_date_range,
    validate_required_text,
    validate_school_name,
)


@lru_cache
def get_neis_client() -> NeisClient:
    """NEIS 클라이언트 싱글턴을 반환합니다."""
    settings = get_settings()
    return NeisClient(
        base_url=settings.neis_base_url,
        api_key=settings.neis_api_key,
        timeout=settings.neis_timeout_seconds,
    )


def _json_result(payload: list[dict[str, Any]] | dict[str, Any]) -> CallToolResult:
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=json.dumps(payload, ensure_ascii=False, indent=2),
            )
        ],
        structuredContent=payload if isinstance(payload, dict) else None,
    )


def _error_result(message: str) -> CallToolResult:
    return CallToolResult(
        isError=True,
        content=[TextContent(type="text", text=message)],
    )


def create_mcp_server(neis_client: NeisClient | Any | None = None) -> FastMCP:
    """FastMCP 서버를 생성합니다."""
    settings = get_settings()
    resolved_client = neis_client

    def get_client() -> NeisClient | Any:
        return resolved_client or get_neis_client()

    server = FastMCP(
        name="geupsik-battle-mcp",
        instructions="학교 검색과 중식 급식 조회 도구를 제공합니다.",
        host=settings.mcp_host,
        port=settings.mcp_port,
        streamable_http_path="/mcp",
    )

    @server.tool(name="search_schools", description="부분 학교명으로 후보 학교를 검색합니다.")
    async def search_schools(name: str) -> CallToolResult:
        try:
            school_name = validate_school_name(name)
            schools = map_schools(await get_client().search_schools(school_name))
        except InputValidationError as exc:
            return _error_result(str(exc))
        except NeisUpstreamError:
            return _error_result("학교 검색 중 NEIS 서비스 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")

        if not schools:
            return _error_result("조건에 맞는 학교를 찾을 수 없습니다.")

        payload = [school.model_dump(mode="json", by_alias=True) for school in schools]
        return _json_result(payload)

    @server.tool(
        name="get_meals",
        description="학교 코드와 날짜 범위로 중식 급식 정보를 조회합니다.",
    )
    async def get_meals(
        edu_office_code: str,
        school_code: str,
        from_date: str,
        to_date: str,
    ) -> CallToolResult:
        try:
            edu_code = validate_required_text(edu_office_code, "교육청 코드")
            school = validate_required_text(school_code, "학교 코드")
            start, end = validate_date_range(from_date, to_date)
            meals = map_meals(
                await get_client().fetch_meals(
                    edu_office_code=edu_code,
                    school_code=school,
                    from_ymd=to_neis_ymd(start),
                    to_ymd=to_neis_ymd(end),
                    meal_code="2",
                )
            )
        except InputValidationError as exc:
            return _error_result(str(exc))
        except NeisUpstreamError:
            return _error_result("급식 조회 중 NEIS 서비스 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")

        if not meals:
            return _error_result("선택한 기간에 급식 정보가 없습니다.")

        payload = MealQueryResponse(
            schoolCode=school,
            fromDate=from_date,
            toDate=to_date,
            meals=meals,
        ).model_dump(mode="json", by_alias=True)
        return _json_result(payload)

    return server


mcp = create_mcp_server()


def main() -> None:
    """Streamable HTTP MCP 서버를 실행합니다."""
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
