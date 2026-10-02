from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://admissions:admissions@localhost:5432/admissions"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"

    faq_data_path: str = "app/data/faq.json"
    similarity_threshold: float = 0.5
    # Whole answer, model call included. Keep it above gemini_timeout_seconds, so a slow
    # model ends in the word-for-word FAQ answer instead of a 504.
    assistant_timeout_seconds: float = 15.0
    # US14: pause between streamed chunks of a ready answer, so it visibly appears while
    # "being written". Model answers are streamed the same way: the grounding check (US10)
    # needs the whole answer before any of it is shown.
    stream_chunk_delay_seconds: float = 0.02

    # US10: grounded answers from Gemini, free tier only (Google AI Studio key, no billing).
    # No key = no model calls: every answer is the word-for-word FAQ answer of Sprint 1.
    # The key is set only in the Render environment, never in the repository.
    gemini_api_key: str = ""
    # Free models in the order they are tried. Free limits are per model, so when one
    # answers 429 (limit reached) or 503 (overloaded) the next one is asked.
    # Flash-Lite first: on the free tier it answers in ~6 s and was never overloaded in our
    # measurements, while gemini-3.8-flash mostly answered 503.
    gemini_models: str = "gemini-3.5-flash-lite,gemini-3.8-flash,gemini-3.5-flash"
    # One model call; the API rejects deadlines under 10 s (400). A timeout or any other
    # API error ends in the FAQ answer, without trying the next model.
    gemini_timeout_seconds: float = 10.0
    # "low" keeps latency down and every default model accepts it ("minimal" is rejected
    # by gemini-3.8-flash with 400); empty = the model's default thinking.
    gemini_thinking_level: str = "low"
    # How many FAQ items above the threshold are sent to the model as sources.
    grounding_top_k: int = 5
    admissions_office_contact: str = (
        "SDU Admissions Office, Abylai Khan 1/1, 040900 Kaskelen. Tel. +7 727 307 95 65"
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def gemini_model_list(self) -> list[str]:
        return [model.strip() for model in self.gemini_models.split(",") if model.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
