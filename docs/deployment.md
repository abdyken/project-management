# Dev deployment handoff (T0.5)

This repository is ready for the three services below. The account actions and final URLs must be completed by the project owner in Neon, Render and Vercel/Netlify.

1. **Neon:** create a PostgreSQL database with pgvector enabled and copy its connection URL. For SQLAlchemy set `DATABASE_URL` to the same URL with `postgresql+psycopg://` as its scheme.
2. **Render:** create a Web Service from this repository with root directory `backend` and Docker runtime. Set `DATABASE_URL`, `CORS_ORIGINS=<frontend URL>`, `APP_ENV=dev`, and the non-secret provider settings from `backend/.env.example`. Set both `CATALOG_API_URL` and `CHECKLIST_API_URL` to the Render service URL so the assistant uses the deployed catalogue and checklist rather than its local demo fixtures. Add real provider keys only as Render secrets. The Docker startup command applies migrations automatically.
3. **Vercel or Netlify:** deploy `frontend` with build command `npm run build` and publish directory `dist`. Set `VITE_USE_MOCKS=false` and `VITE_API_BASE_URL=<Render URL>`.
4. Open the frontend and check the catalogue, a checklist, and one chat question. Then set the exact frontend URL in Render's `CORS_ORIGINS` if it changed.

The `Backend CI` workflow runs the required pgvector database, `uv sync`, FAQ reindex and pytest for every pull request. Enable the branch protection rule in `docs/repository-rules.md` so it blocks failing merges.
