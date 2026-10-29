# US5 - Programme recommendations QA

**Record:** 29.10.2026. **Status:** implemented and locally verified; live QA and PO acceptance open.

## Acceptance scenarios

- Select interests, degree, language and optional academic results; get up to three active matching programmes with eligibility and sources.
- Known failed requirements and incompatible published teaching languages are excluded; unknown requirements remain visible.
- No Gemini key, model failure, invalid ids or invented reason labels use deterministic template explanations. Scores/e-mail never enter the model prompt.
- Compare links open the existing comparison page.

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
