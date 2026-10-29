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
RUN uv sync --frozen --no-dev --group model-build --no-install-project

COPY app/__init__.py app/
COPY app/assistant/__init__.py app/assistant/embeddings.py app/assistant/
RUN python -c "from app.assistant.embeddings import warm_up; warm_up()"

# Slim copy of the FAQ search model: ~240 MB of memory instead of ~610 MB, so the
# API fits a 512 MB server (scripts/build_slim_model.py explains the change).
COPY scripts/build_slim_model.py scripts/
RUN python scripts/build_slim_model.py --out /opt/slim-model

COPY . .

# The build fails if the slim model does not match the original on every FAQ text;
# then the FAQ vectors are precomputed so the server does not embed them on every start.
RUN python scripts/check_slim_model.py --model-dir /opt/slim-model \
 && EMBEDDING_MODEL_DIR=/opt/slim-model python scripts/precompute_faq_embeddings.py --out /opt/faq-embeddings.json

# To go back to the original model, set both variables to an empty value on the host.
ENV EMBEDDING_MODEL_DIR=/opt/slim-model \
    EMBEDDING_CACHE_FILE=/opt/faq-embeddings.json

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && python scripts/import_catalogue.py --if-empty && python scripts/seed_guidance.py && python scripts/reindex_faq.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
