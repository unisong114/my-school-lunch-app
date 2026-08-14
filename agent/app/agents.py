"""Copilot 에이전트 구성."""

from __future__ import annotations

import json
from typing import Any

from agent_framework import MCPStreamableHTTPTool
from agent_framework.github import GitHubCopilotAgent
from copilot import CopilotClient, RuntimeConnection

from .config import Settings
from .rubric import RubricSections
from .scoring import AREA_LABELS


AREA_OUTPUT_SCHEMA = {
    "status": "ok | no_data",
    "schoolA": {
        "score": "1~5 정수",
        "rationale": "한국어 근거 설명",
    },
    "schoolB": {
        "score": "1~5 정수",
        "rationale": "한국어 근거 설명",
    },
    "stopReason": "status가 no_data일 때만 한국어 사유",
}

QUALITY_GATE_SCHEMA = {
    "summary": "한국어 총평",
    "qualityNotes": ["한국어 점검 메모"],
}


def build_copilot_client(settings: Settings) -> CopilotClient:
    """공유 Copilot 클라이언트를 구성합니다."""

    connection = (
        RuntimeConnection.for_stdio(path=settings.github_copilot_cli_path)
        if settings.github_copilot_cli_path
        else None
    )
    return CopilotClient(
        connection=connection,
        github_token=settings.github_token,
        log_level=settings.github_copilot_log_level or "info",
        base_directory=settings.github_copilot_base_directory,
    )


def build_mcp_tool(settings: Settings) -> MCPStreamableHTTPTool:
    """NEIS MCP 서버 도구를 구성합니다."""

    return MCPStreamableHTTPTool(
        name="neis_mcp",
        url=settings.mcp_server_url,
        allowed_tools=["search_schools", "get_meals"],
        request_timeout=30,
    )


def _base_constraints(rubric: RubricSections) -> str:
    return (
        "다음 루브릭 원문을 엄격히 따른다.\n\n"
        f"{rubric.purpose}\n\n"
        f"{rubric.data_limits}\n"
    )


def build_evaluator_instructions(area_key: str, rubric: RubricSections) -> str:
    """영역별 평가자 시스템 지시문을 생성합니다."""

    label = AREA_LABELS[area_key]
    schema_text = json.dumps(AREA_OUTPUT_SCHEMA, ensure_ascii=False, indent=2)
    return (
        f"당신은 '{label}' 전문 평가자다.\n"
        f"{_base_constraints(rubric)}\n"
        f"{rubric.areas[area_key]}\n\n"
        "반드시 MCP 도구의 `get_meals(edu_office_code, school_code, from_date, to_date)`를 직접 호출해 "
        "학교 A와 학교 B의 선택 날짜 중식 데이터를 각각 확인한 뒤 평가한다.\n"
        "학교 한 곳이라도 해당 날짜 중식 데이터가 없으면 비교를 중단하고 status를 no_data로 반환한다.\n"
        "메뉴명만으로 확인할 수 없는 사실을 추정하지 않는다.\n"
        "최종 답변은 설명문 없이 JSON 객체만 반환한다.\n"
        "JSON 스키마:\n"
        f"{schema_text}"
    )


def build_quality_gate_instructions(rubric: RubricSections) -> str:
    """최종 평가자 시스템 지시문을 생성합니다."""

    schema_text = json.dumps(QUALITY_GATE_SCHEMA, ensure_ascii=False, indent=2)
    return (
        "당신은 급식 비교 결과의 최종 평가자다.\n"
        f"{_base_constraints(rubric)}\n"
        f"{rubric.quality_gate}\n\n"
        "네 전문 평가 결과와 앱이 계산한 총점을 검토하되, 점수나 승패를 바꾸지 않는다.\n"
        "과도한 추정, 근거 부족, 상충되는 주장만 지적하고 한국어 총평을 작성한다.\n"
        "최종 답변은 설명문 없이 JSON 객체만 반환한다.\n"
        "JSON 스키마:\n"
        f"{schema_text}"
    )


def build_evaluator_agents(
    *,
    settings: Settings,
    rubric: RubricSections,
    client: CopilotClient,
    mcp_tool: Any,
) -> dict[str, GitHubCopilotAgent]:
    """영역별 평가자 에이전트들을 생성합니다."""

    default_options: dict[str, Any] = {}
    if settings.github_copilot_model:
        default_options["model"] = settings.github_copilot_model

    return {
        area_key: GitHubCopilotAgent(
            id=area_key,
            name=area_key,
            instructions=build_evaluator_instructions(area_key, rubric),
            client=client,
            tools=[mcp_tool],
            default_options=default_options or None,
        )
        for area_key in AREA_LABELS
    }


def build_quality_gate_agent(
    *,
    settings: Settings,
    rubric: RubricSections,
    client: CopilotClient,
) -> GitHubCopilotAgent:
    """최종 품질 게이트 에이전트를 생성합니다."""

    default_options: dict[str, Any] = {}
    if settings.github_copilot_model:
        default_options["model"] = settings.github_copilot_model

    return GitHubCopilotAgent(
        id="qualityGate",
        name="qualityGate",
        instructions=build_quality_gate_instructions(rubric),
        client=client,
        default_options=default_options or None,
    )
