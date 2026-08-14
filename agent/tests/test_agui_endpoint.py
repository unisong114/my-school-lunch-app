"""AG-UI SSE 통합 테스트."""

from __future__ import annotations

import json

from agent_framework import AgentResponse, AgentResponseUpdate, Content, Message, ResponseStream
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.service import LunchBattleService


AREA_RESPONSES = {
    "nutritionBalance": {
        "status": "ok",
        "schoolA": {"score": 4, "rationale": "열량과 식품군 구성이 비교적 균형적입니다."},
        "schoolB": {"score": 3, "rationale": "구성은 갖췄지만 채소 다양성이 아쉽습니다."},
    },
    "healthiness": {
        "status": "ok",
        "schoolA": {"score": 4, "rationale": "튀김 비중이 낮고 부담 요인이 적습니다."},
        "schoolB": {"score": 3, "rationale": "가공식품과 당류 신호가 일부 보입니다."},
    },
    "menuQuality": {
        "status": "ok",
        "schoolA": {"score": 5, "rationale": "메뉴 조화와 식재료 다양성이 우수합니다."},
        "schoolB": {"score": 4, "rationale": "전반적으로 무난하지만 일부 중복이 있습니다."},
    },
    "mealParticipation": {
        "status": "ok",
        "schoolA": {"score": 3, "rationale": "급식 인원수는 확인되나 평균적인 규모입니다."},
        "schoolB": {"score": 2, "rationale": "급식 인원수는 있으나 규모가 더 작습니다."},
    },
}

QUALITY_GATE_RESPONSE = {
    "summary": "학교 A가 영양 균형과 메뉴 품질에서 앞서 총점 우위를 보였습니다. 학교 B는 채소 다양성과 건강성 개선이 필요합니다.",
    "qualityNotes": ["메뉴명만으로 조리법을 단정하지 않도록 평가 근거를 유지했습니다."],
}


class DummyClient:
    async def stop(self) -> None:
        return None


class DummyMCPTool:
    pass


def _parse_sse_frames(raw_text: str) -> list[dict[str, object]]:
    frames: list[dict[str, object]] = []
    for chunk in raw_text.strip().split("\n\n"):
        if not chunk.startswith("data: "):
            continue
        frames.append(json.loads(chunk[6:]))
    return frames


def test_agui_streams_expected_event_sequence(monkeypatch) -> None:
    monkeypatch.setattr(LunchBattleService, "_build_copilot_client", lambda self: DummyClient())
    monkeypatch.setattr(LunchBattleService, "_build_mcp_tool", lambda self: DummyMCPTool())

    def fake_run(self, _messages, *, stream: bool = False, **_kwargs):
        name = getattr(self, "name", None) or getattr(self, "id", None)
        if name == "qualityGate":
            payload = QUALITY_GATE_RESPONSE
        else:
            payload = AREA_RESPONSES[name]

        if not stream:
            async def final_response():
                return AgentResponse(messages=[Message("assistant", [json.dumps(payload, ensure_ascii=False)])])

            return final_response()

        async def iterator():
            yield AgentResponseUpdate(
                contents=[Content.from_text(text=json.dumps(payload, ensure_ascii=False))],
                role="assistant",
            )

        return ResponseStream(iterator(), finalizer=AgentResponse.from_updates)

    monkeypatch.setattr("agent_framework_github_copilot._agent.GitHubCopilotAgent.run", fake_run)

    service = LunchBattleService(Settings())
    app = create_app(service=service)
    with TestClient(app) as client:
        response = client.post(
            "/agui",
            json={
                "thread_id": "thread-1",
                "run_id": "run-1",
                "messages": [{"role": "user", "content": "서울고와 경기고를 비교해 줘"}],
                "state": {
                    "schoolA": {
                        "eduOfficeCode": "B10",
                        "schoolCode": "7010569",
                        "schoolName": "서울고",
                    },
                    "schoolB": {
                        "eduOfficeCode": "B10",
                        "schoolCode": "7010536",
                        "schoolName": "경기고",
                    },
                    "date": "2026-08-14",
                    "prompt": "각 학교의 장단점과 개선안을 알려 주세요.",
                },
            },
        )

    assert response.status_code == 200
    frames = _parse_sse_frames(response.text)
    frame_types = [frame["type"] for frame in frames]

    assert frame_types[0] == "RUN_STARTED"
    assert frame_types[1] == "TEXT_MESSAGE_START"
    assert "TEXT_MESSAGE_CONTENT" in frame_types
    assert frame_types[-2] == "CUSTOM"
    assert frame_types[-1] == "RUN_FINISHED"

    final_event = frames[-2]
    assert final_event["name"] == "lunch_battle_result"
    value = final_event["value"]
    assert value["winner"] == "A"
    assert value["schoolA"]["totalScore"] == 81.0
    assert value["schoolB"]["totalScore"] == 61.0
    assert value["schoolA"]["areas"]["nutritionBalance"]["weightedScore"] == 32.0
    assert value["qualityNotes"] == QUALITY_GATE_RESPONSE["qualityNotes"]
