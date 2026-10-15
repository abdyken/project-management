# Data files

## Catalogue

- `catalogue.json` — official program catalogue and document requirements (T0.6, US16):
  all 64 bachelor, master and PhD programs of 2026-2027, collected from sdu.edu.kz on
  2026-09-23 and 2026-10-08, pending admissions office review.
  **Since Sprint 4 (US21) this file is only the seed:** the database is the source of
  truth and the admissions office edits programs and document lists in the staff area
  (`/staff/programs`). The API container runs `scripts/import_catalogue.py --if-empty`,
  which only fills an empty catalogue; running the import without the flag overwrites
  every staff edit with this file. Fees are per ECTS credit
  from the 2026-2027 fee orders; `null` means not published. `title_ru` / `title_kk` are
  the official Russian and Kazakh page titles. A program either has its own `documents`
  or `documents_from`: the program whose official list it shares (the admission pages
  publish one list per degree level and applicant type). An applicant type without a
  list has no official list, so the API returns the missing-data warning.
- `catalogue_evidence.json` — for each program field and document list, the source page
  and the quote it was taken from, for the admissions office review.
- `catalogue_review.md` — conflicts and gaps in the official sources the admissions office
  has to settle (duplicate code 7M01501, two master fee orders, unpublished values).

## FAQ base

- `faq.json` — official FAQ (T3.1, US8, US18): 75 items collected from sdu.edu.kz (35 on
  2026-09-23, 40 on 2026-10-08), pending review by the admissions office. Each item has
  `faq_id, question, answer, category, source_link, last_update, degrees, applicant_types`
  and an `evidence` quote copied from the source page (kept for the review, not used by
  the API). `question_ru, answer_ru, source_link_ru, evidence_ru` and the same `_kk` fields
  are the official Russian and Kazakh text of the same facts from the RU/KZ version of
  the page; `null` when that page lacks the facts or contradicts the English page (66
  items have Russian, 57 Kazakh).
  **Since Sprint 4 (US20) this file is only the seed:** migration 0015 copied it into the
  `faq_item` table, which is the source of truth. The admissions office edits the FAQ in
  the staff area (`/staff/faq`), and `scripts/reindex_faq.py` (run on every API start)
  indexes the published rows of the table, not this file. Edits to this file after the
  migration have no effect on the API; it is still read by the evaluation scripts and
  the image build (precomputed vectors), so keep it as the reviewed baseline.
- `faq_review.md` — how the texts were collected and checked, every missing translation
  with its reason, and the conflicts between the language versions for the office.
