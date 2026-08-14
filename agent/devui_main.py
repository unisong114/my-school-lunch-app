"""Agent Framework DevUI 실행 스크립트."""

from __future__ import annotations

from agent_framework.devui import serve

from app.config import get_settings
from app.service import LunchBattleService


def main() -> None:
    settings = get_settings()
    service = LunchBattleService(settings)
    workflow = service.build_devui_workflow()
    serve(
        entities=[workflow],
        host="127.0.0.1",
        port=8181,
        auto_open=False,
        auth_enabled=False,
    )


if __name__ == "__main__":
    main()
