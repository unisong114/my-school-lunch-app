"""FastAPI 애플리케이션 진입점."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4

from ag_ui.core import (
    CustomEvent,
    RunErrorEvent,
    RunFinishedEvent,
    RunFinishedSuccessOutcome,
    RunStartedEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
)
from ag_ui.encoder import EventEncoder
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import ValidationError

from . import __version__
from .config import Settings, get_settings
from .models import AgUiRunRequest, BattleInvocation, BattleState, LunchBattleResult
from .service import LunchBattleError, LunchBattleService


def _format_validation_error(error: ValidationError) -> str:
    messages: list[str] = []
    for item in error.errors():
        field_path = ".".join(str(part) for part in item["loc"])
        error_type = item["type"]
        if error_type == "missing":
            messages.append(f"'{field_path}' 필드가 필요합니다.")
        elif field_path.endswith("date"):
            messages.append("date는 YYYY-MM-DD 형식이어야 합니다.")
        else:
            messages.append(f"'{field_path}' 값이 올바르지 않습니다.")
    return " ".join(messages) or "요청 본문이 올바르지 않습니다."


def _merge_state_payload(request_model: AgUiRunRequest) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for payload in (request_model.state, request_model.forwarded_props):
        if payload is None:
            continue
        if not isinstance(payload, dict):
            raise HTTPException(status_code=422, detail="state 또는 forwarded_props는 JSON 객체여야 합니다.")
        merged.update(payload)
    return merged


def parse_invocation(payload: dict[str, Any]) -> BattleInvocation:
    """요청 본문을 도메인 입력으로 변환합니다."""

    try:
        request_model = AgUiRunRequest.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=_format_validation_error(exc)) from exc

    merged_state = _merge_state_payload(request_model)

    try:
        state = BattleState.model_validate(merged_state)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=_format_validation_error(exc)) from exc

    if (
        state.school_a.edu_office_code == state.school_b.edu_office_code
        and state.school_a.school_code == state.school_b.school_code
    ):
        raise HTTPException(status_code=400, detail="같은 학교를 두 번 선택할 수 없습니다.")

    if state.school_a.school_name == state.school_b.school_name and (
        state.school_a.school_code == state.school_b.school_code
    ):
        raise HTTPException(status_code=400, detail="같은 학교를 두 번 선택할 수 없습니다.")

    prompt = state.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="'prompt' 값이 올바르지 않습니다.")

    state = state.model_copy(update={"prompt": prompt})
    return BattleInvocation(
        threadId=request_model.thread_id,
        runId=request_model.run_id,
        parentRunId=request_model.parent_run_id,
        messages=request_model.messages,
        state=state,
    )


def create_app(service: LunchBattleService | None = None, settings: Settings | None = None) -> FastAPI:
    """FastAPI 앱을 생성합니다."""

    app_settings = settings or get_settings()
    battle_service = service or LunchBattleService(app_settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.battle_service = battle_service
        try:
            yield
        finally:
            await battle_service.close()

    app = FastAPI(
        title="급식 배틀 멀티에이전트 API",
        description="GitHub Copilot SDK와 Microsoft Agent Framework를 사용한 급식 비교 AG-UI 서버입니다.",
        version=__version__,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    app.state.battle_service = battle_service

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.get("/health", tags=["health"], summary="헬스 체크")
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.post("/agui", tags=["ag-ui"], summary="급식 배틀 AG-UI SSE 엔드포인트")
    async def agui(request: Request) -> StreamingResponse:
        try:
            payload = await request.json()
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="요청 본문이 올바른 JSON이 아닙니다.") from exc

        if not isinstance(payload, dict):
            raise HTTPException(status_code=422, detail="요청 본문은 JSON 객체여야 합니다.")

        invocation = parse_invocation(payload)
        battle_service: LunchBattleService = request.app.state.battle_service
        encoder = EventEncoder()

        async def event_generator():
            message_id = f"progress-{uuid4().hex}"
            yield encoder.encode(
                RunStartedEvent(
                    thread_id=invocation.thread_id,
                    run_id=invocation.run_id,
                    parent_run_id=invocation.parent_run_id,
                )
            )
            yield encoder.encode(TextMessageStartEvent(message_id=message_id, role="assistant"))
            yield encoder.encode(
                TextMessageContentEvent(
                    message_id=message_id,
                    delta="급식 비교를 시작합니다.\n",
                )
            )

            try:
                async for item in battle_service.stream_battle(invocation):
                    if isinstance(item, LunchBattleResult):
                        result_payload = item.model_dump(by_alias=True)
                        yield encoder.encode(TextMessageEndEvent(message_id=message_id))
                        yield encoder.encode(
                            CustomEvent(
                                name="lunch_battle_result",
                                value=result_payload,
                            )
                        )
                        yield encoder.encode(
                            RunFinishedEvent(
                                thread_id=invocation.thread_id,
                                run_id=invocation.run_id,
                                result=result_payload,
                                outcome=RunFinishedSuccessOutcome(),
                            )
                        )
                        return

                    yield encoder.encode(
                        TextMessageContentEvent(
                            message_id=message_id,
                            delta=f"{item.message}\n",
                        )
                    )

                raise LunchBattleError("최종 비교 결과가 생성되지 않았습니다.")
            except LunchBattleError as exc:
                yield encoder.encode(TextMessageEndEvent(message_id=message_id))
                yield encoder.encode(RunErrorEvent(message=str(exc), code="LunchBattleError"))
            except Exception:
                yield encoder.encode(TextMessageEndEvent(message_id=message_id))
                yield encoder.encode(
                    RunErrorEvent(
                        message="급식 비교 중 내부 오류가 발생했습니다.",
                        code="InternalError",
                    )
                )

        return StreamingResponse(
            event_generator(),
            media_type=encoder.get_content_type(),
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return app


app = create_app()
