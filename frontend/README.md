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

`GET /api/health`, `GET /api/programs`, `GET /api/programs/:id`, `GET /api/programs/:id/checklist?applicant_type=local|international`, `POST /api/assistant/ask`.
