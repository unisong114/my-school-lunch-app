"""에이전트 앱 설정."""

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

    mcp_server_url: str = Field(
        default="http://localhost:8100/mcp",
        validation_alias="MCP_SERVER_URL",
        description="급식 MCP 서버의 Streamable HTTP 엔드포인트.",
    )
    cors_allow_origins: str = Field(
        default="*",
        validation_alias="CORS_ALLOW_ORIGINS",
        description="쉼표로 구분된 허용 Origin 목록.",
    )
    host: str = Field(default="0.0.0.0", validation_alias="HOST")
    port: int = Field(default=9100, validation_alias="PORT")

    github_token: str | None = Field(
        default=None,
        validation_alias="GITHUB_TOKEN",
        description="Copilot SDK가 로그인 세션 대신 사용할 선택적 GitHub 토큰.",
    )
    github_copilot_cli_path: str | None = Field(
        default=None,
        validation_alias="GITHUB_COPILOT_CLI_PATH",
        description="Copilot CLI 실행 파일 경로.",
    )
    github_copilot_model: str | None = Field(
        default=None,
        validation_alias="GITHUB_COPILOT_MODEL",
        description="GitHub Copilot 모델 이름.",
    )
    github_copilot_timeout: float | None = Field(
        default=None,
        validation_alias="GITHUB_COPILOT_TIMEOUT",
        description="GitHub Copilot 요청 타임아웃(초).",
    )
    github_copilot_log_level: str | None = Field(
        default=None,
        validation_alias="GITHUB_COPILOT_LOG_LEVEL",
        description="GitHub Copilot CLI 로그 레벨.",
    )
    github_copilot_base_directory: str | None = Field(
        default=None,
        validation_alias="GITHUB_COPILOT_BASE_DIRECTORY",
        description="Copilot 세션 상태 저장 디렉터리.",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        """CORS 허용 Origin을 리스트로 변환합니다."""

        raw = self.cors_allow_origins.strip()
        if not raw or raw == "*":
            return ["*"]
        return [origin.strip() for origin in raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """설정 싱글턴을 반환합니다."""

    return Settings()
