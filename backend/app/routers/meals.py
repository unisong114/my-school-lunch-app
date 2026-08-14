"""급식 조회 엔드포인트."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..dependencies import get_neis_client
from ..exceptions import NeisUpstreamError
from ..models import MealQueryResponse
from ..neis_client import NeisClient
from ..services import (
    DateRangeError,
    map_meals,
    to_neis_ymd,
    validate_date_range,
)

router = APIRouter(prefix="/api", tags=["meals"])

# 중식(점심) 식사구분코드
_LUNCH_MEAL_CODE = "2"


@router.get(
    "/meals",
    response_model=MealQueryResponse,
    summary="학교와 날짜 범위로 중식 급식 조회",
)
async def get_meals(
    eduOfficeCode: str = Query(..., min_length=1, description="시도교육청코드"),
    schoolCode: str = Query(..., min_length=1, description="행정표준코드"),
    fromDate: str = Query(..., description="조회 시작일 (YYYY-MM-DD)"),
    toDate: str = Query(..., description="조회 종료일 (YYYY-MM-DD)"),
    client: NeisClient = Depends(get_neis_client),
) -> MealQueryResponse:
    """선택한 학교와 날짜 범위에 대해 중식 기준 날짜별 급식을 반환합니다.

    유효하지 않은 날짜 범위는 400 오류로 안내하며, 급식 정보가 없으면 빈
    목록을 반환합니다.
    """
    try:
        start, end = validate_date_range(fromDate, toDate)
    except DateRangeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    try:
        rows = await client.fetch_meals(
            edu_office_code=eduOfficeCode.strip(),
            school_code=schoolCode.strip(),
            from_ymd=to_neis_ymd(start),
            to_ymd=to_neis_ymd(end),
            meal_code=_LUNCH_MEAL_CODE,
        )
    except NeisUpstreamError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"급식 정보를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요. ({exc.message})",
        ) from exc

    return MealQueryResponse(
        schoolCode=schoolCode.strip(),
        fromDate=fromDate,
        toDate=toDate,
        meals=map_meals(rows),
    )
