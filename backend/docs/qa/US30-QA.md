# US30 - Personal handoff to admissions QA

**Record:** 29.10.2026. **Status:** implemented and locally verified; live QA and PO acceptance open.

## Acceptance scenarios

- A verified applicant submits a private question; staff reply; the reply appears only in the owning account.
- Client-key retries deduplicate, a changed question with the same key conflicts, and the durable five-per-hour limit applies.
- Another applicant/staff cookie cannot impersonate the owner; all private responses are no-store; cross-origin mutations are rejected.
- SMTP failure retains the committed answer, retry sends once under ordinary successful operation, and the e-mail contains no private question/answer text.
- Account deletion cascades through questions, answers and delivery state.

## Verification evidence

- Full final backend run: **632 passed** on a separate PostgreSQL/pgvector database.
- New integration cases: `backend/tests/test_guidance.py` and `backend/tests/test_admissions_requests.py`.
- New browser matrix: **72/72**, Chromium and Firefox at 360/768/1280 px; RU/KK/EN page labels and layout; genuine local Mailpit delivery.
- All 64 programmes: public guidance, eligibility and split-cost endpoints responded correctly; seed payloads validated; staff changes survive repeat seeding.
- Frontend lint, TypeScript and production build pass. Migration empty DB -> 0019 -> 0018 -> 0019 passes.

## Boundaries

- These are local results, not a CI run, a production enablement decision or PO approval.
- Data completeness blockers remain in `docs/sprint-6-data-review.md`; rules, rates and outcomes are not invented to close them.
- Real hosting/SMTP configuration and deployed acceptance remain subject to `docs/applicant-hosting.md`.
