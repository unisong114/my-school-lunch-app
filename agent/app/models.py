"""에이전트 앱 데이터 모델."""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator


class CamelModel(BaseModel):
    """camelCase alias 출력을 지원하는 공통 모델."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class BattleSchoolRef(CamelModel):
    """비교 대상 학교 식별자."""

    edu_office_code: str = Field(alias="eduOfficeCode", min_length=1)
    school_code: str = Field(alias="schoolCode", min_length=1)
    school_name: str = Field(alias="schoolName", min_length=1)


class BattleState(CamelModel):
    """`state` 또는 `forwarded_props`에 담기는 비교 입력."""

    school_a: BattleSchoolRef = Field(alias="schoolA")
    school_b: BattleSchoolRef = Field(alias="schoolB")
    date: date
    prompt: str = Field(min_length=1)

    @field_validator("date", mode="before")
    @classmethod
    def validate_date_format(cls, value: object) -> object:
        if isinstance(value, str) and len(value) != 10:
            raise ValueError("date는 YYYY-MM-DD 형식이어야 합니다.")
        return value


class AgUiRunRequest(CamelModel):
    """`/agui` 요청 본문."""

    thread_id: str = Field(alias="thread_id", min_length=1)
    run_id: str = Field(alias="run_id", min_length=1)
    parent_run_id: str | None = Field(default=None, alias="parent_run_id")
    messages: list[dict[str, Any]]
    state: dict[str, Any] | None = None
    forwarded_props: dict[str, Any] | None = Field(default=None, alias="forwarded_props")


class BattleInvocation(CamelModel):
    """서비스 내부 비교 실행 입력."""

    thread_id: str = Field(alias="threadId")
    run_id: str = Field(alias="runId")
    parent_run_id: str | None = Field(default=None, alias="parentRunId")
    messages: list[dict[str, Any]]
    state: BattleState


class SchoolAreaEvaluation(CamelModel):
    """단일 학교에 대한 영역별 평가 결과."""

    score: int = Field(ge=1, le=5)
    rationale: str = Field(min_length=1)


class AreaEvaluationResponse(CamelModel):
    """전문 평가자 에이전트의 구조화 출력."""

    status: Literal["ok", "no_data"]
    school_a: SchoolAreaEvaluation | None = Field(default=None, alias="schoolA")
    school_b: SchoolAreaEvaluation | None = Field(default=None, alias="schoolB")
    stop_reason: str | None = Field(default=None, alias="stopReason")


class QualityGateResponse(CamelModel):
    """최종 평가자 구조화 출력."""

    summary: str = Field(min_length=1)
    quality_notes: list[str] = Field(default_factory=list, alias="qualityNotes")


class AreaBattleResult(CamelModel):
    """최종 응답에 포함되는 영역별 결과."""

    score: int = Field(ge=1, le=5)
    weighted_score: float = Field(alias="weightedScore")
    rationale: str = Field(min_length=1)


class SchoolBattleResult(BattleSchoolRef):
    """최종 응답의 학교별 결과."""

    total_score: float = Field(alias="totalScore")
    areas: dict[str, AreaBattleResult]


class LunchBattleResult(CamelModel):
    """최종 비교 결과."""

    school_a: SchoolBattleResult = Field(alias="schoolA")
    school_b: SchoolBattleResult = Field(alias="schoolB")
    winner: Literal["A", "B", "tie"]
    summary: str = Field(min_length=1)
    quality_notes: list[str] = Field(default_factory=list, alias="qualityNotes")


class ProgressUpdate(CamelModel):
    """SSE 진행 메시지."""

    message: str


NonEmptyString = StringConstraints(strip_whitespace=True, min_length=1)
