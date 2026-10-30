# Admissions guidance - Sprint 6

All paths start with `/api`. Existing JSON errors use `{error_code, message}`.
The catalogue and guidance tables are the source of truth; startup seeding inserts
only missing records. No public assessment persists scores, interests or profiles.
The checked campaign is 2026-2027; evidence includes campaign, check date, quote,
HTTPS URL and `confirmed` / `pending` / `conflict` status. The frozen source audit
and known gaps cover all 64 programmes in `docs/sprint-6-data-review.md`.

## Eligibility

`POST /eligibility/check`: `{program_id, applicant_type?, education_route?,
admission_basis?, track?, scores?, language?}`. Categories: local/international;
education: school/college/bachelor/master; basis: paid/grant; master's track:
scientific/profile/null; language: en/ru/kk. Defaults: local, school, paid, null, en.

Scores are optional: `unt_total` 0-140, `ct_total` 0-150, `gpa` 0-4,
`ielts_overall` / `ielts_component_min` 0-9, `subject_pair` text, and nullable
booleans `sdu_english`, `interview`, `special_exam`, `creative_exam`.
`sdu_english=true` means an accepted SDU English exam / B1 certificate, not a
self-assessed English level. Unknown values are null, never zero by default.
For PhD: `phd_total` 0-100, `toefl_ibt` 0-120, `toefl_pbt` 0-677, `toeic` 0-990,
`duolingo` 0-160, `work_months` 0-1000 and nullable `kaztest` boolean are supported.
The published local doctoral route checks the 75/100 entrance threshold, alternative
foreign-language certificates, KAZTEST and nine months' documented experience;
remaining programme-specific requirements are still explicit gaps. General master's
CT minima remain pending until their scientific/profile applicability to each
programme is confirmed; choosing a track alone does not turn them into known failures.

Returns `{program_id, status, checks, gaps, admission_guaranteed:false}`.
Each check includes its key, `pass|fail|unknown`, alternatives and evidence.
Conditions within an alternative are AND; alternatives are OR. Missing scores
or unconfirmed evidence produce unknown. A confirmed failed applicable rule gives
`does_not_meet`; otherwise incomplete route coverage or unknown checks give
`insufficient_data`. Only an office-confirmed complete route with passed checks
gives `meets_published_requirements`. That still does not guarantee admission or a
competitive grant. A paid-contract UNT threshold never applies to grant applicants.

## Cost estimate

`POST /programs/{id}/cost-estimate`:
`{professional_ects, mde_ects?:0, currency?:"KZT", language_group?, language?:"en"}`.
Credits are integers, each 0-1000, with a combined total of 1-1000. Currency is KZT
or USD; the currencies use independently published tariffs, not FX conversion.

Returns components with credits, unit rate, amount and evidence; `known_subtotal`,
nullable `estimated_total`, `gaps`, assumptions, optional published programme ECTS
and `is_binding_quote:false`. Any missing requested tariff makes the total null;
the known subtotal remains explicitly partial. With language-specific tariffs an
explicit matching group is required. No unrelated group is used as a fallback.
A catalogue professional fee change invalidates the previously confirmed rate
snapshot until the officer rechecks its evidence and saves the guidance.

The caller supplies the actual professional/MDE credit allocation. The result is
an estimate at current rates, excluding future increases, scholarships and other
expenses. It never claims a binding whole-degree price. Bachelor MDE rates are not
silently applied to master/PhD programmes. Programme-specific 60/90/130 ECTS values
take precedence over generic degree references.

`GET /programs/{id}/guidance` returns published rule/tariff metadata and explicit
data gaps. Missing guidance is an incomplete record, not invented defaults.

## Recommendations

`POST /recommendations`: eligibility profile plus `degree_level` (default bachelor),
`interests` (1-8 of computing/business/law/education/languages/science/media/psychology),
and optional `teaching_language`.

Returns up to 3 active programme records, each with eligibility, matching-interest
reason labels and gaps. Each interest has core terms (the subject itself) and related
terms (an adjacent field). Per interest, a core title term scores 10 (+1 when the title
starts with it), a related title term scores 5, and a matching school adds 2;
confirmed eligible routes add 3. Ties sort by programme id. Confirmed eligibility
failures and known teaching-language mismatches are excluded; missing requirements
and language remain explicit. No matches means an empty list.

Gemini receives only selected programme titles and allowed reason labels, never
scores or e-mail. Its response must contain exactly those ids and nonempty subsets
of the allowed labels. Invalid/model-unavailable responses use template explanations;
model text cannot introduce admission facts. Response includes
`explanation_mode:template|grounded_model` and `admission_guaranteed:false`.

## Funding

`GET /funding?language=en&degree_level=bachelor&applicant_type=local` reads published
FAQ rows on grants/discounts/scholarships, including the curated existing items.
Staff edits and retirement are reflected on the next API request. Each card has
its official text, URL, content language, last-check date and campaign warning.
Missing official translations fall back visibly to the English source. Historical
campaign text is labelled historical; other entries still require confirmation for
the current campaign. No automatic award or discount stacking is implied.

## Staff editing

`GET|PUT /staff/programs/{id}/guidance` requires the existing staff session.
PUT replaces a validated `Guidance` payload: scoped rules, office-confirmed complete
routes, sourced credit counts, sourced MDE and language tariffs, field evidence and
gaps. Rules support AND/OR alternatives. New rules/evidence start pending in the UI.
The officer is responsible for confirming applicability, sources and complete routes.
The server records the last staff editor/time and current professional fee snapshot.
New programmes can have an empty guidance record; archived programmes remain editable.

Unknown/inactive public programme: 404 `PROGRAM_NOT_FOUND`; invalid body/parameters:
422 `INVALID_REQUEST`; unauthenticated staff: 401 `NOT_LOGGED_IN`.
The generated OpenAPI file contains all request/response schemas.
