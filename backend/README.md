# Backend — Admissions Portal API

Stack (T0.1): **Python 3.12 + FastAPI**, **SQLAlchemy 2 + Alembic**, **PostgreSQL 16 + pgvector** (FAQ embeddings live in the same database, no separate vector store). Dependencies are managed with [uv](https://docs.astral.sh/uv/) (`pyproject.toml` + `uv.lock`).

## Run with Docker (recommended)

```bash
cd backend
cp .env.example .env
docker compose up --build
```

- API: http://localhost:8000
- Health check: http://localhost:8000/api/health → `{"status": "ok", "database": "ok"}` (503 when the database is unreachable)
- Interactive API docs (Swagger): http://localhost:8000/docs
- API contracts: [programs](docs/api/programs.md), [checklist](docs/api/checklist.md), [assistant](docs/api/assistant.md); full OpenAPI file: [docs/api/openapi.json](docs/api/openapi.json) (`uv run python scripts/export_openapi.py` after changing endpoints)

On start the API container applies migrations, imports `app/data/catalogue.json` and rebuilds the FAQ index.

## Run the API on your machine (database still in Docker)

```bash
cd backend
cp .env.example .env
docker compose up -d db
uv sync
uv run alembic upgrade head
uv run python scripts/import_catalogue.py
uv run python scripts/reindex_faq.py
uv run uvicorn app.main:app --reload
```

## Tests

```bash
docker compose up -d db
uv run pytest
```

## Migrations

One shared Alembic chain for all modules (`migrations/versions/`):

| Revision | Owner | What |
| -------- | ----- | ---- |
| 0001 | Dinmukhamed (T0.3) | Baseline |
| 0002 | Serdar (T3.2) | `faq_embeddings` table + `vector` extension |
| 0003 | Dinmukhamed (T1.1) | `program` table |
| 0004 | Nurmek (T4.1) | `program_document_requirement` table |
| 0005 | T3.2 | `faq_embeddings` resized to 384 dimensions |
| 0006 | US3/US4 | `admissions_followup` log of unanswered questions and missing checklists |

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
  followups/     unanswered questions and missing checklists for the admissions office
  data/          catalogue.json and the FAQ base
migrations/      Alembic migrations (one chain)
scripts/         import_catalogue.py, reindex_faq.py, run_accuracy_test.py, qa_us1.py, export_*.py
tests/
docs/            task notes (docs/serdar-ai-tasks/ - assistant tasks T0.7, T3.2-T3.7)
```

## Assistant module (US3, Serdar)

See [docs/serdar-ai-tasks/](docs/serdar-ai-tasks/). Answers are the text of the closest FAQ item, found with a local multilingual embedding model (no API key). The model is downloaded once into `FASTEMBED_CACHE_PATH`.

```bash
curl -X POST http://127.0.0.1:8000/api/assistant/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "When is the application deadline?", "session_id": "demo"}'
```

- Accuracy report against a running API: `uv run python scripts/run_accuracy_test.py` (see the T3.7 doc).
- After editing the FAQ file, run `uv run python scripts/reindex_faq.py` (or restart the container).

## Environment variables

See [.env.example](.env.example): database URL, CORS origins, FAQ file, similarity threshold, timeout and the admissions contact. Only `.env.example` is tracked; `.env` is git-ignored.
