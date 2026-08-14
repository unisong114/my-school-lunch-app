"""MCP 도구 정의.

공식 MCP Python SDK(``mcp`` 패키지, 1.x)의 FastMCP를 사용해 Streamable HTTP
전송 방식의 MCP 서버를 구성합니다. 기존 백엔드 API 앱과는 독립적으로 동작하며,
NEIS 공개 API(`data/openapi.json` 명세)를 직접 호출합니다.

주의: FastMCP는 도구 함수의 파라미터 타입을 런타임에 검사해 JSON 스키마를
생성하므로, 이 모듈에서는 지연 평가(``from __future__ import annotations``)를
사용하지 않습니다.
"""

from mcp.server.fastmcp import FastMCP

from .config import get_settings
from .dependencies import get_neis_client
from .exceptions import NeisUpstreamError, ToolInputError, ToolNoResultError
from .models import MealSearchResult, SchoolSearchResult
from .services import map_meals, map_schools, to_neis_ymd, validate_date_range

# 중식(점심) 식사구분코드
_LUNCH_MEAL_CODE = "2"

_settings = get_settings()

mcp = FastMCP(
    "급식 배틀 MCP 서버",
    host=_settings.mcp_host,
    port=_settings.mcp_port,
)


@mcp.tool(
    name="search_schools",
    description=(
        "학교 이름의 일부를 입력해 후보 학교의 이름, 교육청 정보, 학교 식별"
        " 정보(교육청코드·행정표준코드)를 조회합니다."
    ),
)
async def search_schools(school_name: str) -> SchoolSearchResult:
    """부분 학교명으로 후보 학교를 검색합니다.

    Args:
        school_name: 검색할 학교 이름의 일부 (예: "서울고").

    Raises:
        ToolInputError: ``school_name`` 이 비어 있는 경우.
        ToolNoResultError: 일치하는 학교가 없는 경우.
        RuntimeError: NEIS API 호출에 실패하거나 응답이 지연된 경우.
    """
    query = (school_name or "").strip()
    if not query:
        raise ToolInputError("학교명을 입력해 주세요.")

    client = get_neis_client()
    try:
        rows = await client.search_schools(query)
    except NeisUpstreamError as exc:
        raise RuntimeError(
            f"학교 정보를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요. ({exc.message})"
        ) from exc

    schools = map_schools(rows)
    if not schools:
        raise ToolNoResultError(f"'{query}'와 일치하는 학교를 찾을 수 없습니다.")
    return SchoolSearchResult(schools=schools)


@mcp.tool(
    name="get_meals",
    description=(
        "선택한 학교(교육청코드·행정표준코드)와 시작일·종료일을 입력하면 중식"
        " 기준 날짜별 급식 정보를 조회합니다."
    ),
)
async def get_meals(
    edu_office_code: str,
    school_code: str,
    from_date: str,
    to_date: str,
) -> MealSearchResult:
    """선택한 학교와 날짜 범위에 대해 중식 기준 급식을 조회합니다.

    Args:
        edu_office_code: 시도교육청코드 (ATPT_OFCDC_SC_CODE).
        school_code: 행정표준코드 (SD_SCHUL_CODE).
        from_date: 조회 시작일 (YYYY-MM-DD).
        to_date: 조회 종료일 (YYYY-MM-DD).

    Raises:
        ToolInputError: 필수값이 비어 있거나 날짜 범위가 유효하지 않은 경우.
        ToolNoResultError: 선택한 학교와 날짜 범위에 급식 정보가 없는 경우.
        RuntimeError: NEIS API 호출에 실패하거나 응답이 지연된 경우.
    """
    edu_office = (edu_office_code or "").strip()
    school = (school_code or "").strip()
    if not edu_office:
        raise ToolInputError("교육청코드(edu_office_code)를 입력해 주세요.")
    if not school:
        raise ToolInputError("행정표준코드(school_code)를 입력해 주세요.")

    start, end = validate_date_range(from_date, to_date)

    client = get_neis_client()
    try:
        rows = await client.fetch_meals(
            edu_office_code=edu_office,
            school_code=school,
            from_ymd=to_neis_ymd(start),
            to_ymd=to_neis_ymd(end),
            meal_code=_LUNCH_MEAL_CODE,
        )
    except NeisUpstreamError as exc:
        raise RuntimeError(
            f"급식 정보를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요. ({exc.message})"
        ) from exc

    meals = map_meals(rows)
    if not meals:
        raise ToolNoResultError(
            f"선택한 학교(school_code={school})와 날짜 범위"
            f"({from_date} ~ {to_date})에 대한 급식 정보가 없습니다."
        )
    return MealSearchResult(
        schoolCode=school,
        fromDate=from_date,
        toDate=to_date,
        meals=meals,
    )
