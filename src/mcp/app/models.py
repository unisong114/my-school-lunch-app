"""MCP 도구 입출력 모델."""

from __future__ import annotations

from pydantic import BaseModel, Field


class School(BaseModel):
    """학교 검색 결과 항목."""

    eduOfficeCode: str = Field(..., description="시도교육청코드")
    eduOfficeName: str = Field(..., description="시도교육청명")
    schoolCode: str = Field(..., description="학교코드")
    schoolName: str = Field(..., description="학교명")
    schoolKind: str | None = Field(default=None, description="학교종류명")
    region: str | None = Field(default=None, description="시도명")
    address: str | None = Field(default=None, description="도로명주소")


class MealDish(BaseModel):
    """개별 급식 항목."""

    name: str = Field(..., description="요리명")
    allergies: list[int] = Field(default_factory=list, description="알레르기 번호 목록")


class DailyMeal(BaseModel):
    """하루 급식 정보."""

    date: str = Field(..., description="급식일자 (YYYY-MM-DD)")
    mealName: str = Field(default="중식", description="식사구분명")
    dishes: list[MealDish] = Field(default_factory=list, description="요리 목록")
    calorie: str | None = Field(default=None, description="칼로리 정보")
    nutrition: str | None = Field(default=None, description="영양 정보")
    origin: str | None = Field(default=None, description="원산지 정보")
    mealCount: str | None = Field(default=None, description="급식인원수")


class MealQueryResponse(BaseModel):
    """급식 조회 응답."""

    schoolCode: str = Field(..., description="학교코드")
    fromDate: str = Field(..., description="조회 시작일")
    toDate: str = Field(..., description="조회 종료일")
    meals: list[DailyMeal] = Field(default_factory=list, description="날짜별 급식 목록")
