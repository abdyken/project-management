# Backend — Admissions Portal API

Stack (T0.1): **Python 3.12 + FastAPI**, **SQLAlchemy 2 + Alembic**, **PostgreSQL 16 + pgvector** (FAQ embeddings live in the same database, no separate vector store). Dependencies are managed with [uv](https://docs.astral.sh/uv/) (`pyproject.toml` + `uv.lock`).

## Run with Docker (recommended)

```bash
cd backend
cp .env.example .env
uv run python scripts/reindex_faq.py   # builds the FAQ index file used by the assistant (INDEX_BACKEND=file)
docker compose up --build
```

- API: http://localhost:8000
- Health check: http://localhost:8000/api/health → `{"status": "ok", "database": "ok"}` (503 when the database is unreachable)
- Interactive API docs (Swagger): http://localhost:8000/docs

Migrations are applied automatically on API start (`alembic upgrade head`).

## Run the API on your machine (database still in Docker)

```bash
cd backend
cp .env.example .env
docker compose up -d db
uv sync
uv run alembic upgrade head
uv run python scripts/reindex_faq.py
uv run uvicorn app.main:app --reload
```

## Tests

```bash
docker compose up -d db
uv run python scripts/reindex_faq.py   # the assistant router tests need the FAQ index
uv run pytest
```

## Migrations

One shared Alembic chain for all modules (`migrations/versions/`):

| Revision | Owner | What |
| -------- | ----- | ---- |
| 0001 | Dinmukhamed (T0.3) | Baseline |
| 0002 | Serdar (T3.2) | `faq_embeddings` table + `vector` extension |

```bash
uv run alembic revision --autogenerate -m "describe the change"   # after changing models
uv run alembic upgrade head
uv run alembic downgrade -1
```

New migrations must set `down_revision` to the current head (`uv run alembic heads` shows it) so the chain never splits. Import new model modules in `migrations/env.py` so autogenerate sees them.

## Structure

```
app/
  main.py        FastAPI app, CORS, router registration
  config.py      settings from environment variables (.env)
  db.py          SQLAlchemy Base, engine, sessions (get_db_session for FastAPI)
  api/health.py  GET /api/health
  catalogue/     US1 - programs, search and filter API (Dinmukhamed)
  checklist/     US4 - document requirements and checklist endpoint (Nurmek)
  assistant/     US3 - FAQ assistant, POST /api/assistant/ask (Serdar)
  data/          sample FAQ / program / checklist fixtures used by the assistant
migrations/      Alembic migrations (one chain)
scripts/         reindex_faq.py, run_accuracy_test.py, smoke_test_provider.py
tests/
docs/            task notes (docs/serdar-ai-tasks/ - assistant tasks T0.7, T3.2-T3.7)
```

## Assistant module (US3, Serdar)

See [docs/serdar-ai-tasks/](docs/serdar-ai-tasks/). Defaults use mock LLM and embedding providers, so no API keys are needed locally.

```bash
curl -X POST http://127.0.0.1:8000/api/assistant/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "When is the application deadline?", "session_id": "demo"}'
```

- Accuracy report against the 10-question test set: `uv run python scripts/run_accuracy_test.py` (see the T3.7 doc).
- Retrieval index storage: `INDEX_BACKEND=file` (default, local JSON file) or `INDEX_BACKEND=postgres` (pgvector table from migration 0002, what the deployed dev environment should use). After switching to `postgres`, run `uv run python scripts/reindex_faq.py` to populate the table.
- Until the catalogue (T1.3) and checklist (T4.2) endpoints are deployed, the assistant reads `app/data/programs_sample.json` / `checklist_sample.json`; set `CATALOG_API_URL` / `CHECKLIST_API_URL` once they are.

## Environment variables

See [.env.example](.env.example) for the full list: database URL, CORS origins, LLM/embedding providers and keys, similarity threshold, timeouts. Never commit real API keys — only `.env.example` is tracked; `.env` is git-ignored.
