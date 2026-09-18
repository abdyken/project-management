# Backend — Admissions Portal API

Python 3.12, FastAPI, PostgreSQL 16, SQLAlchemy 2, Alembic.

## Run with Docker (recommended)

```bash
cd backend
cp .env.example .env
docker compose up --build
```

- API: http://localhost:8000
- Health check: http://localhost:8000/api/health → `{"status": "ok", "database": "ok"}`
- Interactive API docs (Swagger): http://localhost:8000/docs

Migrations are applied automatically on API start (`alembic upgrade head`).

## Run the API on your machine (database still in Docker)

Requires [uv](https://docs.astral.sh/uv/).

```bash
cd backend
docker compose up -d db
uv sync
export DATABASE_URL=postgresql+psycopg://admissions:admissions@localhost:5432/admissions
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

## Tests

```bash
docker compose up -d db
DATABASE_URL=postgresql+psycopg://admissions:admissions@localhost:5432/admissions uv run pytest
```

## Migrations

```bash
uv run alembic revision --autogenerate -m "describe the change"   # after changing models
uv run alembic upgrade head
uv run alembic downgrade -1
```

## Structure

```
app/
  main.py        FastAPI app, CORS, router registration
  config.py      settings from environment variables (.env)
  db.py          SQLAlchemy engine, session, declarative Base
  api/health.py  GET /api/health (200 ok / 503 when the database is unreachable)
  catalogue/     US1 - programs, search and filter API
  checklist/     US4 - document requirements and checklist endpoint
  assistant/     US3 - FAQ assistant
migrations/      Alembic migrations
tests/
```

## Environment variables

| Variable       | Purpose                                         |
| -------------- | ----------------------------------------------- |
| `DATABASE_URL` | SQLAlchemy URL (`postgresql+psycopg://...`)     |
| `APP_ENV`      | `local` / `dev`                                 |
| `CORS_ORIGINS` | Comma-separated front-end origins allowed by CORS |
| `PORT`         | Port for the API in the container (default 8000) |
