"""LunchBattleService의 응답 파싱 로직 단위 테스트."""

from __future__ import annotations

import json

import pytest

from app.config import Settings
from app.models import AreaEvaluationResponse
from app.service import LunchBattleError, LunchBattleService


class DummyClient:
    async def stop(self) -> None:
        return None


class DummyMCPTool:
    pass


@pytest.fixture
def service(monkeypatch) -> LunchBattleService:
    monkeypatch.setattr(LunchBattleService, "_build_copilot_client", lambda self: DummyClient())
    monkeypatch.setattr(LunchBattleService, "_build_mcp_tool", lambda self: DummyMCPTool())
    return LunchBattleService(Settings())


def test_parse_area_response_accepts_strict_schema(service: LunchBattleService) -> None:
    text = json.dumps(
        {
            "status": "ok",
            "schoolA": {"score": 4, "rationale": "근거 A"},
            "schoolB": {"score": 3, "rationale": "근거 B"},
        },
        ensure_ascii=False,
    )

    result = service._parse_area_response(text, "nutritionBalance")

    assert isinstance(result, AreaEvaluationResponse)
    assert result.school_a is not None and result.school_a.score == 4
    assert result.school_b is not None and result.school_b.score == 3


def test_parse_area_response_recovers_nested_evaluation_shape(
    service: LunchBattleService,
) -> None:
    """평가자가 스키마를 벗어나 4개 영역을 evaluation에 중첩해 응답해도 복구한다."""

    text = "```json\n" + json.dumps(
        {
            "status": "ok",
            "schoolA": {
                "name": "학교 A",
                "evaluation": {
                    "nutritionBalance": {"score": 3, "rationale": "무관 영역"},
                    "participation": {"score": 4, "rationale": "학교 A 참여도 근거"},
                },
            },
            "schoolB": {
                "name": "학교 B",
                "evaluation": {
                    "participation": {"score": 5, "rationale": "학교 B 참여도 근거"},
                },
            },
        },
        ensure_ascii=False,
    ) + "\n```"

    result = service._parse_area_response(text, "mealParticipation")

    assert result.status == "ok"
    assert result.school_a is not None
    assert result.school_a.score == 4
    assert result.school_a.rationale == "학교 A 참여도 근거"
    assert result.school_b is not None
    assert result.school_b.score == 5
    assert result.school_b.rationale == "학교 B 참여도 근거"


def test_parse_area_response_raises_when_unrecoverable(service: LunchBattleService) -> None:
    with pytest.raises(LunchBattleError):
        service._parse_area_response("이 텍스트에는 JSON이 없습니다.", "healthiness")
