"""내부 API(프론트엔드 ↔ 백엔드) 스키마 정의.

`src/openapi.json` 계약과 일치하는 Pydantic 모델을 정의합니다.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class School(BaseModel):
    """학교 검색 결과 항목."""

    eduOfficeCode: str = Field(..., description="시도교육청코드 (ATPT_OFCDC_SC_CODE)")
    eduOfficeName: str = Field(..., description="시도교육청명")
    schoolCode: str = Field(..., description="행정표준코드 (SD_SCHUL_CODE)")
    schoolName: str = Field(..., description="학교명")
    schoolKind: str | None = Field(default=None, description="학교종류명")
    region: str | None = Field(default=None, description="시도명")
    address: str | None = Field(default=None, description="도로명주소")


class SchoolSearchResponse(BaseModel):
    """학교 검색 응답."""

    schools: list[School] = Field(default_factory=list)


class MealDish(BaseModel):
    """개별 급식 요리 항목."""

    name: str = Field(..., description="요리명")
    allergies: list[int] = Field(
        default_factory=list, description="알레르기 유발 식품 번호 목록"
    )


class DailyMeal(BaseModel):
    """특정 날짜의 중식 급식 정보."""

    date: str = Field(..., description="급식일자 (YYYY-MM-DD)")
    mealName: str = Field(default="중식", description="식사구분명")
    dishes: list[MealDish] = Field(default_factory=list, description="요리 목록")
    calorie: str | None = Field(default=None, description="칼로리 정보")
    nutrition: str | None = Field(default=None, description="영양 정보")
    origin: str | None = Field(default=None, description="원산지 정보")


class MealQueryResponse(BaseModel):
    """급식 조회 응답."""

    schoolCode: str = Field(..., description="행정표준코드")
    fromDate: str = Field(..., description="조회 시작일 (YYYY-MM-DD)")
    toDate: str = Field(..., description="조회 종료일 (YYYY-MM-DD)")
    meals: list[DailyMeal] = Field(
        default_factory=list, description="날짜별 중식 급식 목록"
    )


class ErrorResponse(BaseModel):
    """오류 응답."""

    detail: str = Field(..., description="오류 메시지")
