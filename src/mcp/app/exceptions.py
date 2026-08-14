"""NEIS API 연동 및 MCP 도구 처리 중 발생하는 예외 정의."""

from __future__ import annotations


class NeisError(Exception):
    """NEIS API 호출 계층의 기본 예외."""


class NeisUpstreamError(NeisError):
    """NEIS API가 오류를 반환했거나 통신에 실패한 경우."""

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ToolInputError(ValueError):
    """MCP 도구 입력값이 유효하지 않은 경우."""


class ToolNoResultError(RuntimeError):
    """학교 검색 결과 또는 급식 정보가 없는 경우."""
