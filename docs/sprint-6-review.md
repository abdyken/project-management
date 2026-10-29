# Sprint 6 - implementation review and QA

**Sprint:** 24-30.10.2026. **Implementation and local verification:** 29.10.2026.
**Branch:** `feature/sprint-6-program-guidance`.

## Result

All five planned stories are implemented: US27 requirements, US28 tuition estimates,
US5 programme recommendations, US29 funding guide and US30 private staff handoff.
The public `/admissions` hub connects them to programme details, comparison, chat
and the existing applicant/staff accounts. New public pages support RU/KK/EN.

The source audit and public guidance endpoints cover all 64 catalogue programmes.
Confirmed data includes 32 paid bachelor UNT thresholds, published profile-subject
groupings, bachelor MDE and language tariffs, programme-specific master credit
references, and local PhD exam/certificate/KAZTEST/experience rules. All rules and
rates retain their source and evidence. General master CT rules remain pending
until programme-track applicability is established. No universal GPA threshold,
mandatory IELTS-only path or universal whole-degree price is introduced.

This does **not** mean all missing university data is resolved: programme-specific
completeness, some master/PhD details, conflicting sources and professional/MDE
credit splits remain explicit in `sprint-6-data-review.md`. The seed does not claim
any route fully confirmed. An officer can update rules, alternatives, sources,
tariffs and confirmed route coverage in the existing programme editor.

| Story | Implementation | Evidence | Acceptance |
| --- | --- | --- | --- |
| US27 | Scoped AND/OR rules; known failure vs unknown; published PhD alternatives; staff maintenance | `backend/docs/qa/US27-QA.md` | Live QA / office confirmation / PO open |
| US28 | Separate professional/MDE and language-group tariffs, KZT/USD, partial totals, changed-rate reconfirmation | `backend/docs/qa/US28-QA.md` | Live QA / PO open |
| US5 | Interest/subject/result form, deterministic filtering/ranking, constrained Gemini reasons and fallback, compare links | `backend/docs/qa/US5-QA.md` | Live QA / PO open |
| US29 | Published database FAQ guide with official translations, applicability filters and campaign warnings | `backend/docs/qa/US29-QA.md` | Current-campaign office confirmation / PO open |
| US30 | Private verified-owner questions, staff queue/reply, transactional link-only notification with retry and account-delete cascade | `backend/docs/qa/US30-QA.md` | Hosting/SMTP decision / live QA / PO open |

## Verification

| Check | Result |
| --- | --- |
| Full backend suite on isolated PostgreSQL/pgvector | **632 passed**, 3 dependency/config deprecation warnings |
| Final targeted integration and migration-metadata checks | **40 passed**, included scenarios plus final error-schema/fixture changes |
| New guidance/request browser matrix | **72/72**, Chromium + Firefox at 360/768/1280 px; RU/KK/EN headings/layout; actual local Mailpit notification |
| Existing comparison browser matrix | **60/60** |
| Existing language browser matrix | **144/144** |
| Existing chat widget browser matrix | **78/78** |
| Existing staff browser matrix | **88/88** |
| Existing applicant browser matrix | **97/97**, including account, tracker, PDFs and reminder preferences |
| Total browser checks in the final matrices | **539/539** |
| Final focused UI checks | **3/3**: exact accessible subject label, master deep-link initialization, Russian language-group calculation |
| All 64 programmes through running guidance/eligibility/split-cost APIs | **64/64** |
| Running assistant catalogue checks | **192/192** |
| Existing v3 assistant evaluation, no Gemini key | **63/70 (90%)**, **9/9** correct fallbacks, **0** invented facts; previous seven misses retained |
| Frontend lint, TypeScript and production build | PASS; existing large-chunk advisory remains |
| Static checking/formatting of new Python code | PASS |
| Empty database → 0019 → downgrade 0018 → upgrade 0019 | PASS in a separate disposable migration database |
| Staff metadata survives repeated missing-only seeding | PASS |
| Visual inspection | Mobile and desktop eligibility/cost/staff screenshots inspected; no material clipping or layout errors |

The browser runs used a dedicated local database and Mailpit, not the existing
project database or a remote deployment. A first staff regression retained a cached
count containing synthetic QA programmes; after removing only those archived test
rows, the final complete staff matrix passed. The guidance harness now reuses two
accounts, respecting registration and five-questions-per-hour limits. Application
limits were not relaxed to make QA pass.
The final UI pass also corrected explicit label/control associations so select
option text is not included in the accessible field name; the new full matrix was
repeated successfully after that correction.

The new browser matrix is added to Backend CI after the existing applicant matrix.
This record reports local execution; a remote GitHub CI run is not asserted.
Generated OpenAPI and the two new API contracts accompany migration 0019.
`docs/table.xlsx` retains its existing historical planning/acceptance records; the
five new Markdown QA cards document this implementation without fabricating PO sign-off.

## Remaining acceptance work

1. Resolve the named data gaps with official sources / the admissions office.
2. Record the existing applicant-hosting/SMTP decision, including private questions
   and replies. Accounts remain disabled by default on the VM.
3. Review the PR and required CI; deploy through the normal workflow, repeat live
   scenarios and record actual PO acceptance. Earlier sprint acceptance carry-over
   remains open unless verified separately.

Assessments do not store scores or profiles. Gemini explanations are tested with
controlled model responses and unavailable/invalid-model cases; a real keyed model
call was not performed. Ordinary SMTP retains the documented crash-between-send-
and-commit duplicate possibility; retryable messages are not described as exactly-once.
