# SDU Admissions Portal

Admissions portal for SDU University: the full official program catalogue (64 programs) with document checklists and side-by-side comparison, and a chat assistant that answers from the official FAQ and catalogue in Kazakh, Russian and English — with grounded Gemini answers when `GEMINI_API_KEY` is set (free tier) and word-for-word official answers without it.

Applicants can also verify an e-mail account, save programs, track prepared documents, opt into deadline reminders and export checklists as PDFs. Local e-mail is captured by Mailpit at http://localhost:8025. Live applicant accounts require the [hosting and SMTP setup](docs/applicant-hosting.md).

Sprint 6 adds [admissions planning](docs/sprint-6-tasks.md): source-backed eligibility checks,
programme recommendations, a professional/MDE tuition calculator, funding guidance and
private questions answered by the admissions office. Open `/admissions` on the portal.
The [64-programme source audit](docs/sprint-6-data-review.md) distinguishes confirmed
facts from missing or conflicting requirements; checks never promise admission or a grant.

Sprint plans and reviews: [`docs/sprint-2-tasks.md`](docs/sprint-2-tasks.md), [`docs/sprint-2-review.md`](docs/sprint-2-review.md), [`docs/sprint-3-tasks.md`](docs/sprint-3-tasks.md), [`docs/sprint-3-review.md`](docs/sprint-3-review.md), [`docs/sprint-4-tasks.md`](docs/sprint-4-tasks.md), [`docs/sprint-5-tasks.md`](docs/sprint-5-tasks.md), [`docs/sprint-5-review.md`](docs/sprint-5-review.md), [`docs/sprint-6-tasks.md`](docs/sprint-6-tasks.md), [`docs/sprint-6-review.md`](docs/sprint-6-review.md), [`docs/sprint-7-tasks.md`](docs/sprint-7-tasks.md), [`docs/sprint-7-review.md`](docs/sprint-7-review.md). Backlog, story and QA sheets: [`docs/table.xlsx`](docs/table.xlsx).

Design: the portal uses its own "Almaty Mosaic" identity (smalt turquoise fields on a tessera grid, SDU logo and credited SDU photos). Product context: [`PRODUCT.md`](PRODUCT.md). Visual system and tokens: [`DESIGN.md`](DESIGN.md). Before/after audits: [`docs/design/baseline-audit-2026-11-20.md`](docs/design/baseline-audit-2026-11-20.md), [`docs/design/redesign-audit-2026-11-20.md`](docs/design/redesign-audit-2026-11-20.md).

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

### Browser QA

Seven Playwright suites run against the local stack. They cover:

- `qa:applicant`: sign-up, login, password reset, saved checklists and reminders
- `qa:staff`: the staff area and catalogue/FAQ editing
- `qa:compare`: program comparison
- `qa:language`: Kazakh and Russian pages
- `qa:widget`: the chat assistant
- `qa:guidance`: the guidance tools and questions to admissions
- `qa:applications`: online applications and staff review

```bash
cd frontend
npm ci
npx playwright install chromium firefox
export BASE_URL=http://localhost:8080 STAFF_EMAIL=… STAFF_PASSWORD=…   # a local QA staff account
npm run qa:all                                   # every suite, in CI order
QA_RUNS=chromium:360,chromium:1280 npm run qa:staff   # one suite, a lighter matrix
```

`QA_RUNS` lists `browser:width` pairs for every suite (`frontend/e2e/matrix.mjs`). Without it, a suite runs Chromium and Firefox at 360, 768 and 1280 px.

The suites use Mailpit. They create and delete their own test accounts and do not modify official catalogue data. To re-run them on the same local database:

- Run `uv run python scripts/qa_reset.py` in `backend/`. It removes the archived synthetic programmes that the guidance suite leaves behind.
- Restart the API (`docker compose restart api`). This clears the in-memory login limiter, which locks the QA staff login after five wrong-password checks in 15 minutes.

CI runs the checks in three tiers:

- **Every pull request** (Frontend CI and Backend CI): lint, typecheck and build, the backend tests, and all seven suites in Chromium at 360 and 1280 px.
- **Nightly at 02:00 Almaty, or on demand** (`Nightly browser QA`): the same suites on the full matrix.
- **Pushes to `main`**: these go through the PR checks in `deploy.yml` before deploying. API details: [`backend/docs/api/applicant.md`](backend/docs/api/applicant.md).
