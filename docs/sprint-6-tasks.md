# Sprint 6 - programme selection and admissions help

**Original sprint:** 24-30.10.2026. **Implementation session:** 29.10.2026.
**Delivery:** project owner with Codex. Original backlog owners are retained as
story contacts; this does not claim they implemented or accepted this session.

Goal: check published requirements, select up to three programmes, estimate tuition,
read funding guidance and receive a personal answer from the admissions office.

| Tasks | Story / original contact | Implementation and acceptance |
| --- | --- | --- |
| 6.0 | All / Askhat | Audit all 64 catalogue rows; rule/tariff evidence and explicit unresolved gaps; `sprint-6-data-review.md` |
| 27.1-27.3 | US27 / Dinmukhamed | Source-backed scoped AND/OR rules, three-state evaluation, staff editor, applicant form; check threshold boundaries and missing data |
| 28.1-28.3 | US28 / Daniyar | Separate professional/MDE and language-group rates, KZT/USD, source evidence and nullable incomplete totals; compare with hand calculation |
| 5.1-5.3 | US5 / Serdar | Interest/subject/result questionnaire, deterministic filtering/ranking and constrained Gemini explanation labels; at most 3 active programmes with compare links |
| 29.1-29.2 | US29 / Askhat | Funding page from published database FAQ, category filters, official translations/source fallback and campaign warnings |
| 30.1-30.3 | US30 / Nurmek | Verified applicant requests, staff queue and reply, private account view, durable retryable notification; deletion and isolation checks |
| 6.QA | All | Backend integration/regression, schema/migration checks, RU/KK/EN UI, Chromium/Firefox at 360/768/1280 px, API contracts and QA records |
| CO.6 | Askhat / project owner | Record hosting/SMTP choice, deployed QA and PO acceptance for carried-over stories; remains open until actually performed |

## Delivery order and boundaries

Data → eligibility → cost → recommendations → funding → private requests → QA.
Migration 0019 only adds two tables; image rollback does not undo it. Startup seeds
missing guidance rows after the catalogue import and preserves all staff edits.
No assessment profile/score storage, uploads, application form or application-status
processing. The catalogue/FAQ databases remain authoritative.

All 64 programmes have a source audit; this is not the same as all admissions rules
being confirmed. The seed deliberately declares no route complete while official
applicability, subject rules and source conflicts remain open. Missing facts are
blockers to data completeness, not fabricated positive or negative decisions.

## Development and QA

After `alembic upgrade head` and the catalogue import, run
`python scripts/seed_guidance.py`, then the existing FAQ indexing/start commands.
Docker startup and CI perform the missing-only seed automatically.

New API contracts: `backend/docs/api/guidance.md` and `requests.md`.
QA cards: `backend/docs/qa/US5-QA.md`, `US27-QA.md` through `US30-QA.md`.

Browser QA uses a disposable database, local Mailpit and a test staff account:

```sh
cd frontend
BASE_URL=http://localhost:5173 MAILPIT_URL=http://localhost:8025 \
  STAFF_EMAIL=<test-staff-email> STAFF_PASSWORD=<test-staff-password> npm run qa:guidance
```

For real local SMTP notification checks also provide `QA_RUN_NOTIFICATIONS=true`,
the disposable `DATABASE_URL`, `APPLICANT_ACCOUNTS_ENABLED=true`, `PUBLIC_BASE_URL`
and `SMTP_HOST/PORT/STARTTLS`. `QA_PYTHON` optionally selects the backend interpreter.
The script creates/deletes its test applicants and creates/archives synthetic QA
programmes. Never run it against a live admissions database.

DoD: reviewed PR, passing required CI, reproducible QA, migration and API contracts;
live enablement/acceptance recorded only after the hosting decision and live checks.
