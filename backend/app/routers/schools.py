"""학교 검색 엔드포인트."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..dependencies import get_neis_client
from ..exceptions import NeisUpstreamError
from ..models import SchoolSearchResponse
from ..neis_client import NeisClient
from ..services import map_schools

router = APIRouter(prefix="/api", tags=["schools"])


@router.get(
    "/schools",
    response_model=SchoolSearchResponse,
    summary="부분 학교명으로 학교 검색",
)
async def search_schools(
    name: str = Query(
        ..., min_length=1, description="검색할 학교명 일부", examples=["서울"]
    ),
    client: NeisClient = Depends(get_neis_client),
) -> SchoolSearchResponse:
    """부분 학교명으로 학교를 검색해 목록을 반환합니다.

    일치하는 학교가 없으면 빈 목록을 반환합니다.
    """
    query = name.strip()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="학교명을 입력해 주세요.",
        )
    try:
        rows = await client.search_schools(query)
    except NeisUpstreamError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"학교 정보를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요. ({exc.message})",
        ) from exc
    return SchoolSearchResponse(schools=map_schools(rows))
