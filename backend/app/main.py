"""FastAPI 애플리케이션 진입점."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .config import get_settings
from .routers import meals, schools

app = FastAPI(
    title="급식 배틀 백엔드 API",
    description="NEIS 공개 API를 중계·가공해 학교 검색과 중식 급식 조회를 제공합니다.",
    version=__version__,
)

_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(schools.router)
app.include_router(meals.router)


@app.get("/api/health", tags=["health"], summary="헬스 체크")
async def health() -> dict[str, str]:
    """서비스 상태를 반환합니다."""
    return {"status": "ok", "version": __version__}
