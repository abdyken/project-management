# SDU Admissions Portal

Admissions portal for SDU University: the full official program catalogue (64 programs) with document checklists and side-by-side comparison, and a chat assistant that answers from the official FAQ and catalogue in Kazakh, Russian and English — with grounded Gemini answers when `GEMINI_API_KEY` is set (free tier) and word-for-word official answers without it.

Applicants can also verify an e-mail account, save programs, track prepared documents, opt into deadline reminders and export checklists as PDFs. Local e-mail is captured by Mailpit at http://localhost:8025. Live applicant accounts require the [hosting and SMTP setup](docs/applicant-hosting.md).

Sprint 6 adds [admissions planning](docs/sprint-6-tasks.md): source-backed eligibility checks,
programme recommendations, a professional/MDE tuition calculator, funding guidance and
private questions answered by the admissions office. Open `/admissions` on the portal.
The [64-programme source audit](docs/sprint-6-data-review.md) distinguishes confirmed
facts from missing or conflicting requirements; checks never promise admission or a grant.

Sprint plans and reviews: [`docs/sprint-2-tasks.md`](docs/sprint-2-tasks.md), [`docs/sprint-2-review.md`](docs/sprint-2-review.md), [`docs/sprint-3-tasks.md`](docs/sprint-3-tasks.md), [`docs/sprint-3-review.md`](docs/sprint-3-review.md), [`docs/sprint-4-tasks.md`](docs/sprint-4-tasks.md), [`docs/sprint-5-tasks.md`](docs/sprint-5-tasks.md).

## Start everything

Requirement: Docker Desktop.

```bash
docker compose up --build
```

Open http://localhost:8080. The first start takes a few minutes (it downloads the embedding model into the API image). On every start the API applies migrations, fills an empty catalogue from `backend/app/data/catalogue.json`, seeds missing guidance records, indexes published database FAQ rows and deletes chat turns older than 30 days. Staff edits are preserved. If port 5432 is taken, start with `POSTGRES_PORT=5433 docker compose up --build`.

| Service | URL |
| --- | --- |
| Web app | http://localhost:8080 |
| API | http://localhost:8000 (docs at `/docs`) |
| Postgres | `localhost:5432`, user/password/db `admissions` |
| Local e-mail inbox | http://localhost:8025 |

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
uv run python scripts/seed_guidance.py
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

Applicant browser QA (Chromium and Firefox, 360/768/1280 px) runs against the local stack:

```bash
cd frontend
npm ci
npx playwright install chromium firefox
BASE_URL=http://localhost:8080 npm run qa:applicant
```

The script uses Mailpit, creates and deletes its own test applicant, and does not modify official catalogue data. Backend CI runs the same matrix. API details: [`backend/docs/api/applicant.md`](backend/docs/api/applicant.md).
