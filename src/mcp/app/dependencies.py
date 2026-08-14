"""NEIS 클라이언트 팩토리.

설정값을 기반으로 :class:`NeisClient` 인스턴스를 생성합니다. 테스트에서는 이
함수를 모킹해 실제 NEIS API 호출 없이 도구를 검증할 수 있습니다.
"""

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
