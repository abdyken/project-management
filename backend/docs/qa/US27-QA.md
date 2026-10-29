# US27 - Eligibility check QA

**Record:** 29.10.2026. **Status:** implemented and locally verified; live QA and PO acceptance open.

## Acceptance scenarios

- Check below/at/above a published paid UNT threshold; grant and college/international routes do not inherit that threshold.
- Profile-subject combinations use the official programme grouping; a missing/conflicting combination remains unknown.
- IELTS overall AND component requirements accept the official SDU alternative; a low IELTS alone does not reject an available unreported alternative.
- PhD checks the published 75/100 threshold, alternative foreign-language certificates, KAZTEST and experience. Unconfirmed master track applicability stays pending.
- Only office-confirmed complete routes can produce a positive overall result; the seed declares no complete routes.

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
