# Backend

Stack (T0.1 decision): **Python 3.12 + FastAPI**, **SQLAlchemy + Alembic** for migrations, **PostgreSQL 16 + pgvector** (FAQ embeddings live in the same DB, no separate vector store).

Right now the repo only contains the **assistant module** (Serdar, AI/IS developer — T0.7, T3.2–T3.7, see [docs/serdar-ai-tasks/](docs/serdar-ai-tasks/)). The catalogue and checklist modules (T0.3, Dinmukhamed) are not built yet; this module ships with file-based stand-ins for them (`app/data/programs_sample.json`, `app/data/checklist_sample.json`) so it runs and is fully tested on its own. Swap `CATALOG_API_URL` / `CHECKLIST_API_URL` in `.env` once those endpoints are deployed.

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # defaults to mock LLM/embedding providers + a local JSON index — no keys needed to run
```

## Run it

```bash
python scripts/reindex_faq.py      # builds the FAQ retrieval index (T3.2)
uvicorn app.main:app --reload      # standalone runner; mount app.assistant.router into the real app once T0.3 exists
```

```bash
curl -X POST http://127.0.0.1:8000/api/assistant/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "When is the application deadline?", "session_id": "demo"}'
```

## Tests

```bash
python -m pytest tests/ -v
```

19 tests, all offline (mock LLM/embedding providers, no DB needed) — retrieval accuracy (T3.2), fallback guard (T3.4), assistant service incl. document-checklist questions (T3.3/T3.6), and the full HTTP contract (T3.5).

Accuracy report against a 10-question test set: `python scripts/run_accuracy_test.py` (see T3.7 doc for the recorded results and how to point it at a deployed dev environment).

## Postgres / pgvector backend

Default `INDEX_BACKEND=file` needs no database. To use the real pgvector-backed index instead (this is what should run in the deployed dev environment, T0.5):

```bash
docker run -d --name assistant-pg -e POSTGRES_PASSWORD=postgres -p 5432:5432 pgvector/pgvector:pg16

export DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/postgres
export INDEX_BACKEND=postgres

alembic upgrade head            # creates the faq_embeddings table (migrations/versions/0001_*)
python scripts/reindex_faq.py   # populates it
uvicorn app.main:app --reload
```

This `docker run` line is for local verification only — the real docker-compose / dev-environment setup is T0.3/T0.5 (Dinmukhamed/Nurmek). When that lands, merge `migrations/versions/0001_create_faq_embeddings.py`'s `down_revision` into the shared Alembic history instead of keeping two separate chains.

## Environment variables

See [.env.example](.env.example) for the full list (LLM/embedding provider + keys, similarity threshold, timeouts, DB URL). Never commit real API keys — only `.env.example` placeholders are tracked; `.env` is git-ignored.
