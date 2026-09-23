FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    FASTEMBED_CACHE_PATH=/opt/fastembed \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app/__init__.py app/
COPY app/assistant/__init__.py app/assistant/embeddings.py app/assistant/
RUN python -c "from app.assistant.embeddings import warm_up; warm_up()"

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && python scripts/import_catalogue.py && python scripts/reindex_faq.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
