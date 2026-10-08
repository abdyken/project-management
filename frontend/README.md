# SDU Admissions frontend

Web portal for SDU University (Kaskelen) admissions: programme catalogue, document checklist, and a session chat that answers from the backend FAQ.

## Stack

- Vite + React 19 + TypeScript
- Tailwind CSS v4
- React Router
- TanStack Query
- Zustand (chat session)
- shadcn/ui primitives (Button, Input, Select, Sheet)

## Local start

```bash
cd frontend
npm ci
npm run dev
```

Start the API on port 8000 first (see the root README). The dev server proxies `/api` there.

`docker compose up --build` in the repository root builds this app into an nginx image (`Dockerfile`, `nginx.conf`) that serves it on http://localhost:8080 and forwards `/api` to the API container.

## Environment

| Variable | Default | Meaning |
| --- | --- | --- |
| `VITE_API_BASE_URL` | empty | Leave empty locally (Vite proxies `/api`). Set the deployed origin for a production build. |

## Routes

- `/` — admissions entry
- `/programs` — catalogue (search + school / degree / language)
- `/programs/:id` — programme + document checklist

The chat widget is mounted on every page.

## API

`GET /api/health`, `GET /api/programs`, `GET /api/programs/:id`, `GET /api/programs/:id/checklist?applicant_type=local|international`, `POST /api/assistant/ask/stream`, `GET /api/assistant/suggestions`. Ratings are kept in the session store and sent to `POST /api/assistant/feedback`.

## Widget QA (US14 14.5)

`e2e/widget-qa.mjs` drives the chat widget in Chromium and Firefox at 360, 768 and 1280 px: starter and follow-up suggestions, sources, checklist lists, follow-ups (US11), comparison (US12), rating with a reason that survives navigation (US13), new conversation, and closing the chat mid-answer (US14). Playwright is installed only for the run, not added to `package.json`:

```bash
npm i --no-save playwright@1.55.0
npx playwright install chromium firefox
BASE_URL=http://localhost:5173 node e2e/widget-qa.mjs
```

Screenshots and `results.json` go to `e2e/shots/` (git-ignored). `WIDTHS=360` limits the run to one width.
