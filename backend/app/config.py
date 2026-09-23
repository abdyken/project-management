from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    database_url: str = "postgresql+psycopg://admissions:admissions@localhost:5432/admissions"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"

    faq_data_path: str = "app/data/faq_sample.json"
    similarity_threshold: float = 0.5
    assistant_timeout_seconds: float = 4.0
    admissions_office_contact: str = (
        "SDU Admissions Office, Abylai Khan 1/1, 040900 Kaskelen. Tel. +7 727 307 95 65"
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
