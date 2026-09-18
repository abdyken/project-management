# Repository working agreement (T0.2)

## Branches and pull requests

- Do not push directly to `main`.
- Name branches `feature/<task>-short-name`, `fix/<task>-short-name`, or `docs/<task>-short-name` (for example, `feature/t4-1-checklist-model`).
- Open one focused pull request per task. Link its task and describe how it was tested.
- One teammate reviews before merge. The author resolves review comments and merges only when required checks pass.
- Do not commit `.env`, API keys, database URLs with credentials, generated FAQ indexes, or `node_modules`/`.venv`.

## Code and contract rules

- Keep backend code in `backend/` and frontend code in `frontend/`; do not duplicate API models or hardcode checklist data in UI components.
- A database change includes an Alembic migration and tests.
- An API change updates its Markdown contract and frontend integration in the same pull request.
- Use official admissions data only. Unknown values are `null`/"not specified", never guessed.

## GitHub setup required once by Nurmek

In **Settings → Branches**, protect `main`: require a pull request, one approving review, and the `Backend CI / test` status check. GitHub cannot be configured from repository code alone.
