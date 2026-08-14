"""환경 변수 기반 MCP 서버 설정."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """MCP 서버 설정."""

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    neis_api_key: str = Field(
        default="",
        validation_alias="NEIS_API_KEY",
        description="NEIS 공개 API 인증 키. 비어 있으면 비인증 호출로 동작합니다.",
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
        description="MCP 서버 바인드 호스트.",
    )
    mcp_port: int = Field(
        default=9001,
        validation_alias="MCP_PORT",
        description="MCP 서버 바인드 포트.",
    )


@lru_cache
def get_settings() -> Settings:
    """설정 싱글턴을 반환합니다."""
    return Settings()
