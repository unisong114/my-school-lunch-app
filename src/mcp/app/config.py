"""애플리케이션 설정.

환경 변수에서 NEIS API 연동 및 MCP 서버 바인딩에 필요한 값을 읽어들입니다.
민감한 정보(API 키)는 서버 측에서만 관리하며 MCP 클라이언트로 노출되지 않습니다.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """환경 변수 기반 애플리케이션 설정."""

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    neis_api_key: str = Field(
        default="",
        validation_alias="NEIS_API_KEY",
        description="NEIS 공개 API 인증 키. 비어 있으면 샘플(맛보기) 키로 동작합니다.",
    )
    neis_base_url: str = Field(
        default="https://open.neis.go.kr/hub",
        validation_alias="NEIS_BASE_URL",
        description="NEIS API 기본 URL.",
    )
    neis_timeout_seconds: float = Field(
        default=10.0,
        validation_alias="NEIS_TIMEOUT_SECONDS",
        description="NEIS API 호출 타임아웃(초).",
    )
    mcp_host: str = Field(
        default="0.0.0.0",
        validation_alias="MCP_HOST",
        description="MCP 서버(Streamable HTTP)가 바인딩할 호스트.",
    )
    mcp_port: int = Field(
        default=8100,
        validation_alias="MCP_PORT",
        description="MCP 서버(Streamable HTTP)가 바인딩할 포트.",
    )


@lru_cache
def get_settings() -> Settings:
    """설정 싱글턴을 반환합니다."""
    return Settings()
