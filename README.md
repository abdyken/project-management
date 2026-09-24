# SDU Admissions Portal

Sprint 1 demo: a program catalogue, document checklist and FAQ assistant for SDU University admissions.

## Start everything

Requirement: Docker Desktop.

```bash
docker compose up --build
```

Open http://localhost:8080. The first start takes a few minutes (it downloads the embedding model into the API image). On every start the API applies migrations, imports `backend/app/data/catalogue.json` and indexes `backend/app/data/faq.json`.

| Service | URL |
| --- | --- |
| Web app | http://localhost:8080 |
| API | http://localhost:8000 (docs at `/docs`) |
| Postgres | `localhost:5432`, user/password/db `admissions` |

`docker compose down -v` removes the database volume.

## Develop

Requirements: Python 3.12 with [uv](https://docs.astral.sh/uv/) and Node.js 20.19+ or 22.12+.

```bash
docker compose up -d db

# terminal 1
cd backend
cp .env.example .env
uv sync
uv run alembic upgrade head
uv run python scripts/import_catalogue.py
uv run python scripts/reindex_faq.py
uv run uvicorn app.main:app --reload

# terminal 2
cd frontend
npm ci
npm run dev
```

Vite serves the app at http://localhost:5173 and proxies `/api` to port 8000.

## Tests

```bash
docker compose up -d db
cd backend
uv sync --frozen
uv run pytest
```

Deployment and repository rules are in [`docs/`](docs/).
