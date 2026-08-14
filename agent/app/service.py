"""급식 배틀 오케스트레이션 서비스."""

from __future__ import annotations

import contextlib
import json
import re
from collections.abc import AsyncIterator
from typing import Any

from agent_framework import AgentResponse
from agent_framework.orchestrations import ConcurrentBuilder
from agent_framework._workflows._agent_executor import AgentExecutorResponse
from agent_framework._workflows._workflow import Workflow

from .agents import (
    build_copilot_client,
    build_evaluator_agents,
    build_mcp_tool,
    build_quality_gate_agent,
)
from .config import Settings
from .models import (
    AreaBattleResult,
    AreaEvaluationResponse,
    BattleInvocation,
    LunchBattleResult,
    ProgressUpdate,
    QualityGateResponse,
    SchoolBattleResult,
)
from .rubric import RubricSections, load_rubric_sections
from .scoring import AREA_LABELS, calculate_school_scores, determine_winner


class LunchBattleError(Exception):
    """사용자에게 안전하게 노출할 수 있는 비교 오류."""


class LunchBattleService:
    """급식 비교 오케스트레이션 서비스."""

    def __init__(self, settings: Settings, rubric: RubricSections | None = None) -> None:
        self._settings = settings
        self._rubric = rubric or load_rubric_sections()
        self._client = self._build_copilot_client()
        self._mcp_tool = self._build_mcp_tool()
        self._evaluator_agents = build_evaluator_agents(
            settings=self._settings,
            rubric=self._rubric,
            client=self._client,
            mcp_tool=self._mcp_tool,
        )
        self._quality_gate_agent = build_quality_gate_agent(
            settings=self._settings,
            rubric=self._rubric,
            client=self._client,
        )

    def _build_copilot_client(self) -> Any:
        return build_copilot_client(self._settings)

    def _build_mcp_tool(self) -> Any:
        return build_mcp_tool(self._settings)

    async def close(self) -> None:
        """공유 클라이언트를 정리합니다."""

        stop = getattr(self._client, "stop", None)
        if stop is None:
            return
        with contextlib.suppress(Exception):
            await stop()

    def _build_workflow(self, invocation: BattleInvocation) -> Workflow:
        async def aggregate(results: list[AgentExecutorResponse]) -> LunchBattleResult:
            return await self._aggregate_results(invocation, results)

        return (
            ConcurrentBuilder(participants=list(self._evaluator_agents.values()))
            .with_aggregator(aggregate)
            .build()
        )

    async def stream_battle(self, invocation: BattleInvocation) -> AsyncIterator[ProgressUpdate | LunchBattleResult]:
        """비교 진행 상황과 최종 결과를 순차적으로 반환합니다."""

        yield ProgressUpdate(message="4개 평가 에이전트에게 급식 비교를 요청했습니다.")
        workflow = self._build_workflow(invocation)
        completed: set[str] = set()
        workflow_stream = workflow.run(message=self._build_evaluator_prompt(invocation), stream=True)

        async for event in workflow_stream:
            if event.type != "executor_completed" or not event.executor_id:
                continue
            if event.executor_id in self._evaluator_agents and event.executor_id not in completed:
                completed.add(event.executor_id)
                yield ProgressUpdate(message=f"{AREA_LABELS[event.executor_id]} 평가가 완료되었습니다.")

        final_result = await workflow_stream.get_final_response()
        outputs = final_result.get_outputs()
        if not outputs:
            raise LunchBattleError("비교 결과를 생성하지 못했습니다.")
        output = outputs[-1]
        if not isinstance(output, LunchBattleResult):
            raise LunchBattleError("최종 비교 결과 형식이 올바르지 않습니다.")
        yield ProgressUpdate(message="최종 품질 게이트 검토를 완료했습니다.")
        yield output

    def build_devui_workflow(self) -> Workflow:
        """DevUI에서 직접 실행할 디버그용 워크플로우를 반환합니다."""

        sample = BattleInvocation.model_validate(
            {
                "threadId": "devui-thread",
                "runId": "devui-run",
                "messages": [],
                "state": {
                    "schoolA": {
                        "eduOfficeCode": "B10",
                        "schoolCode": "7010569",
                        "schoolName": "학교 A",
                    },
                    "schoolB": {
                        "eduOfficeCode": "B10",
                        "schoolCode": "7010536",
                        "schoolName": "학교 B",
                    },
                    "date": "2026-08-14",
                    "prompt": "중식의 강점과 개선점을 비교해 주세요.",
                },
            }
        )
        return self._build_workflow(sample)

    def _build_evaluator_prompt(self, invocation: BattleInvocation) -> str:
        state = invocation.state
        payload = {
            "schoolA": state.school_a.model_dump(by_alias=True),
            "schoolB": state.school_b.model_dump(by_alias=True),
            "date": state.date.isoformat(),
            "prompt": state.prompt,
        }
        return (
            "다음 입력으로 같은 날짜의 두 학교 중식을 비교 평가하세요.\n"
            "반드시 `get_meals` 도구를 학교별로 직접 호출해 확인한 데이터만 사용하세요.\n"
            "조회 범위는 from_date와 to_date 모두 선택 날짜 한 날로 설정하세요.\n"
            "사용자 추가 분석 요청도 반영하세요.\n\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
        )

    async def _aggregate_results(
        self,
        invocation: BattleInvocation,
        results: list[AgentExecutorResponse],
    ) -> LunchBattleResult:
        parsed_by_area: dict[str, AreaEvaluationResponse] = {}

        for result in results:
            area_key = result.executor_id
            if area_key not in AREA_LABELS:
                continue
            parsed = self._parse_agent_json(result.agent_response.text, AreaEvaluationResponse)
            if parsed.status == "no_data":
                raise LunchBattleError(parsed.stop_reason or "선택한 날짜에 급식 데이터가 없어 비교를 중단했습니다.")
            if parsed.school_a is None or parsed.school_b is None:
                raise LunchBattleError(f"{AREA_LABELS[area_key]} 평가 결과에 학교별 점수가 없습니다.")
            parsed_by_area[area_key] = parsed

        missing_areas = [area for area in AREA_LABELS if area not in parsed_by_area]
        if missing_areas:
            missing_labels = ", ".join(AREA_LABELS[area] for area in missing_areas)
            raise LunchBattleError(f"일부 평가 결과가 누락되었습니다: {missing_labels}")

        school_a_scores = {
            area: parsed.school_a.score
            for area, parsed in parsed_by_area.items()
            if parsed.school_a is not None
        }
        school_b_scores = {
            area: parsed.school_b.score
            for area, parsed in parsed_by_area.items()
            if parsed.school_b is not None
        }

        school_a_weighted, school_a_total = calculate_school_scores(school_a_scores)
        school_b_weighted, school_b_total = calculate_school_scores(school_b_scores)
        winner = determine_winner(school_a_total, school_b_total)

        quality_gate_result = await self._run_quality_gate(
            invocation=invocation,
            parsed_by_area=parsed_by_area,
            school_a_total=school_a_total,
            school_b_total=school_b_total,
            winner=winner,
        )

        return LunchBattleResult(
            schoolA=SchoolBattleResult(
                eduOfficeCode=invocation.state.school_a.edu_office_code,
                schoolCode=invocation.state.school_a.school_code,
                schoolName=invocation.state.school_a.school_name,
                totalScore=school_a_total,
                areas={
                    area: AreaBattleResult(
                        score=parsed.school_a.score,
                        weightedScore=school_a_weighted[area],
                        rationale=parsed.school_a.rationale,
                    )
                    for area, parsed in parsed_by_area.items()
                    if parsed.school_a is not None
                },
            ),
            schoolB=SchoolBattleResult(
                eduOfficeCode=invocation.state.school_b.edu_office_code,
                schoolCode=invocation.state.school_b.school_code,
                schoolName=invocation.state.school_b.school_name,
                totalScore=school_b_total,
                areas={
                    area: AreaBattleResult(
                        score=parsed.school_b.score,
                        weightedScore=school_b_weighted[area],
                        rationale=parsed.school_b.rationale,
                    )
                    for area, parsed in parsed_by_area.items()
                    if parsed.school_b is not None
                },
            ),
            winner=winner,
            summary=quality_gate_result.summary,
            qualityNotes=quality_gate_result.quality_notes,
        )

    async def _run_quality_gate(
        self,
        *,
        invocation: BattleInvocation,
        parsed_by_area: dict[str, AreaEvaluationResponse],
        school_a_total: float,
        school_b_total: float,
        winner: str,
    ) -> QualityGateResponse:
        payload = {
            "comparisonInput": {
                "schoolA": invocation.state.school_a.model_dump(by_alias=True),
                "schoolB": invocation.state.school_b.model_dump(by_alias=True),
                "date": invocation.state.date.isoformat(),
                "prompt": invocation.state.prompt,
            },
            "areaEvaluations": {
                area: parsed.model_dump(by_alias=True, exclude_none=True)
                for area, parsed in parsed_by_area.items()
            },
            "calculatedTotals": {
                "schoolA": school_a_total,
                "schoolB": school_b_total,
                "winner": winner,
            },
        }
        prompt = (
            "다음은 앱이 이미 계산한 두 학교 급식 비교 결과입니다.\n"
            "점수와 승패는 바꾸지 말고, 품질 게이트만 수행하세요.\n\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
        )
        response = await self._quality_gate_agent.run(prompt)
        return self._parse_agent_json(response.text, QualityGateResponse)

    def _parse_agent_json(self, text: str, model_type: type[Any]) -> Any:
        candidates: list[str] = [text.strip()]
        fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
        candidates.extend(block.strip() for block in fenced)

        if "{" in text and "}" in text:
            start = text.find("{")
            end = text.rfind("}") + 1
            candidates.append(text[start:end].strip())

        for candidate in candidates:
            if not candidate:
                continue
            try:
                parsed = json.loads(candidate)
                return model_type.model_validate(parsed)
            except Exception:
                continue

        raise LunchBattleError("에이전트 응답을 구조화된 JSON으로 해석하지 못했습니다.")
