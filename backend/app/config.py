"""애플리케이션 설정.

환경 변수에서 NEIS API 연동에 필요한 값을 읽어들입니다. 민감한 정보(API 키)는
서버 측에서만 관리하며 프론트엔드로 노출되지 않습니다.
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
    cors_allow_origins: str = Field(
        default="*",
        validation_alias="CORS_ALLOW_ORIGINS",
        description="쉼표로 구분된 허용 Origin 목록. 기본값은 모든 Origin 허용.",
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
