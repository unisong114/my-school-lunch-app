"""MCP 서버 내부 예외 정의."""

from __future__ import annotations


class NeisError(Exception):
    """NEIS API 연동 기본 예외."""


class NeisUpstreamError(NeisError):
    """NEIS API 호출 실패 또는 응답 오류."""

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
