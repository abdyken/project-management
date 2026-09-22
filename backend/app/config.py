"""T0.7 — LLM and embedding provider setup.

Central place for every environment-driven setting the assistant module
needs. Real API keys must never be committed: only ``.env.example``
(placeholders) lives in the repo, the real ``.env`` is git-ignored.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App / shared (T0.3) ---
    app_env: str = "local"
    # Comma-separated list of front-end origins allowed by CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # --- LLM provider (answer generation) ---
    llm_provider: str = "mock"  # mock | anthropic
    llm_api_key: str = ""
    llm_model: str = "claude-haiku-4-5-20251001"
    llm_spending_limit_usd: float = 20.0

    # --- Embedding provider (retrieval) ---
    embedding_provider: str = "mock"  # mock | openai | voyage
    embedding_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"

    # --- Assistant behaviour ---
    similarity_threshold: float = 0.72
    assistant_timeout_seconds: float = 4.0
    admissions_office_contact: str = "admissions@university.example (+7 000 000 00 00)"

    # --- Data / integration (until T1.x / T4.x are deployed, see catalog_client.py /
    # checklist_client.py — these point at the sample fixtures instead of real services) ---
    faq_data_path: str = "app/data/faq_sample.json"
    faq_index_path: str = "app/data/faq_index.json"
    catalog_api_url: str = ""
    checklist_api_url: str = ""

    # --- Storage backend for the retrieval index (T3.2) ---
    # "file"     — local JSON file, no DB needed. Default, used for offline dev/tests.
    # "postgres" — pgvector column in the shared Postgres DB (T0.1 stack decision:
    #              Python 3.12 + FastAPI + SQLAlchemy/Alembic + PostgreSQL 16 + pgvector).
    index_backend: str = "file"
    database_url: str = "postgresql+psycopg://admissions:admissions@localhost:5432/admissions"
    # pgvector requires a fixed column width. Must match the embedding provider's output
    # size (mock = 256). If EMBEDDING_MODEL changes to a real provider with a different
    # dimension, update this and regenerate the Alembic migration for faq_embeddings.
    embedding_dimensions: int = 256

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
