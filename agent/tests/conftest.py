"""공통 테스트 설정."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from app.main import create_app


class StubBattleService:
    """유효성 검사 테스트용 서비스 스텁."""

    async def close(self) -> None:
        return None

    async def stream_battle(self, _invocation):  # pragma: no cover - invalid 요청에서는 호출되지 않음
        if False:
            yield None


@pytest.fixture
def validation_app():
    return create_app(service=StubBattleService())
