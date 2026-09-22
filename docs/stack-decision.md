# Stack and architecture decision (T0.1)

**Decision date:** 2026-09-18. **Scope:** Sprint 1 demo only.

| Area | Decision | Why |
| --- | --- | --- |
| Frontend | React, TypeScript, Vite, Tailwind | Small typed SPA for the catalogue, detail page and chat. |
| Backend | Python 3.12, FastAPI, SQLAlchemy, Alembic | Typed HTTP API with simple migration support. |
| Database | PostgreSQL 16 with pgvector | Relational catalogue/checklist data and vector retrieval in one free-tier-compatible database. |
| FAQ retrieval | Embeddings with threshold fallback | Answers stay grounded in the approved FAQ; uncertain questions receive the Admissions Office fallback. |
| Dev hosting | Vercel (frontend), Render (API), Neon (Postgres) | Each has a free tier and supports the project without operational overhead. |

The API is the boundary between frontend and backend. Paths and response fields are documented under `backend/docs/api/`; a contract change requires a matching frontend change in the same pull request.

**Deferred:** analytics, PDF export, performance work and a full browser matrix are not required for this sprint.
