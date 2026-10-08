# Backend — Admissions Portal API

Stack (T0.1): **Python 3.12 + FastAPI**, **SQLAlchemy 2 + Alembic**, **PostgreSQL 16 + pgvector** (FAQ embeddings live in the same database, no separate vector store). Dependencies are managed with [uv](https://docs.astral.sh/uv/) (`pyproject.toml` + `uv.lock`).

## Run

`docker compose up --build` in the repository root starts the database, this API and the web app (see the root README). The API container applies migrations, imports `app/data/catalogue.json` and rebuilds the FAQ index on start.

- API: http://localhost:8000, Swagger: http://localhost:8000/docs
- Health check: `/api/health` → `{"status": "ok", "database": "ok"}` (503 when the database is unreachable)
- API contracts: [programs](docs/api/programs.md), [checklist](docs/api/checklist.md), [assistant](docs/api/assistant.md); full OpenAPI file: [docs/api/openapi.json](docs/api/openapi.json) (`uv run python scripts/export_openapi.py` after changing endpoints)

To run the API on your machine instead, start only the database from the root (`docker compose up -d db`), then:

```bash
cd backend
cp .env.example .env
uv sync
uv run alembic upgrade head
uv run python scripts/import_catalogue.py
uv run python scripts/reindex_faq.py
uv run uvicorn app.main:app --reload
```

Grounded answers (US10) need `GEMINI_API_KEY` in `.env` (a free Google AI Studio key); `uv run python scripts/gemini_smoke.py` makes one test call. Without it the assistant answers word for word from the FAQ. Tests never call Gemini.

## Tests

```bash
docker compose up -d db   # from the repository root
cd backend
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
| 0007 | T0.6 | Fees per ECTS credit (KZT/USD), local and international deadlines, `source_url` |
| 0008 | US3 | FAQ audience fields (`degrees`, `applicant_types`) |
| 0009 | Dinmukhamed (US11) | `chat_turn` table - stored turns of a chat session |
| 0010 | US3 fix | Drop the approximate HNSW index on `faq_embeddings`: exact search, no missed FAQ items |

```bash
uv run alembic revision --autogenerate -m "describe the change"   # after changing models
uv run alembic upgrade head
uv run alembic downgrade -1
```

New migrations must set `down_revision` to the current head (`uv run alembic heads` shows it) so the chain never splits. Import new model modules in `migrations/env.py` so autogenerate sees them.

## Scheduled jobs

Chat turns are kept only against the anonymous session id and deleted after 30 days (US11). The API does this itself on start and every 24 hours, so no cron job is needed. To purge by hand:

```bash
uv run python scripts/purge_chat_turns.py
```

## Structure

```
app/
  main.py        FastAPI app, CORS, router registration
  config.py      settings from environment variables (.env)
  db.py          SQLAlchemy Base, engine, sessions (get_db_session for FastAPI)
  api/health.py  GET /api/health
  catalogue/     US1 - programs, search and filter API (Dinmukhamed)
  conversation/  US11 - chat turns of a session, context for follow-up questions (Dinmukhamed)
  checklist/     US4 - document requirements and checklist endpoint (Nurmek)
  assistant/     US3 - FAQ assistant, POST /api/assistant/ask (Serdar)
  followups/     unanswered questions and missing checklists for the admissions office
  data/          catalogue.json and the FAQ base
migrations/      Alembic migrations (one chain)
scripts/         import_catalogue.py, reindex_faq.py, run_accuracy_test.py, check_catalogue_answers.py, qa_us1.py, export_*.py (catalogue, negative feedback, unanswered questions)
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

- Evaluation set v2 (40 questions) against a running API: `ASSISTANT_BASE_URL=<url> uv run python scripts/run_accuracy_test.py` (see the T10.5 doc).
- Evaluation set v3 (70 questions: v2 plus new FAQ topics, Kazakh, Russian and catalogue cases): `uv run python scripts/run_accuracy_test.py --set v3`.
- Unanswered questions for the office (US18): `uv run python scripts/export_unanswered.py --days 30 --output unanswered.csv` groups the logged questions with counts; no session ids, e-mails or phone numbers.
- Catalogue answer check (US12): `ASSISTANT_BASE_URL=<url> uv run python scripts/check_catalogue_answers.py` asks the fee, deadline and language of every program and compares the answers with `catalogue.json`.
- After editing the FAQ file, run `uv run python scripts/reindex_faq.py` (or restart the container).

## Environment variables

See [.env.example](.env.example): database URL, CORS origins, FAQ file, similarity threshold, timeout and the admissions contact. Only `.env.example` is tracked; `.env` is git-ignored.
