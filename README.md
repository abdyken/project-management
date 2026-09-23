# SDU Admissions Portal

Sprint 1 demo: a programme catalogue, document checklist and FAQ assistant.

## Local start

Requirements: Docker Desktop, Python 3.12 with [uv](https://docs.astral.sh/uv/), and Node.js 20+ with npm.

```bash
# terminal 1
cd backend
cp .env.example .env
docker compose up --build

# terminal 2
cd frontend
cp .env.example .env
npm ci
npm run dev
```

The API is available at `http://localhost:8000`; the frontend URL is printed by Vite.

## Tests

```bash
cd backend
docker compose up -d db
uv sync --frozen
uv run pytest
```

Deployment and repository rules are in [`docs/`](docs/).
