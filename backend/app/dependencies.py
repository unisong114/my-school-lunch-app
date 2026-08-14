"""FastAPI 의존성 정의."""

from __future__ import annotations

from .config import Settings, get_settings
from .neis_client import NeisClient


def get_neis_client() -> NeisClient:
    """설정 기반 NEIS 클라이언트를 생성합니다."""
    settings: Settings = get_settings()
    return NeisClient(
        base_url=settings.neis_base_url,
        api_key=settings.neis_api_key,
        timeout=settings.neis_timeout_seconds,
    )
