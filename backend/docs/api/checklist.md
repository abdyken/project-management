# Document checklist API (US4)

## `GET /api/programs/{program_id}/checklist`

Returns requirements for one active programme and one applicant type.

```text
GET /api/programs/6B06102/checklist?applicant_type=international
```

`applicant_type` is required and is either `local` or `international`. Invalid or missing values return `422` with `{"error_code": "INVALID_REQUEST", "message": "applicant_type: …"}`.

### Populated checklist — 200

```json
{
  "program_id": "6B06102",
  "applicant_type": "international",
  "items": [
    {
      "name": "Passport",
      "format": "copy",
      "translation": true,
      "notarisation": true,
      "deadline": "Application"
    }
  ],
  "warning": null,
  "contact": null
}
```

### No stored requirements — 200

This is intentionally not an unexplained empty list. The frontend and assistant show `warning` and `contact`. The case is recorded in the `admissions_followup` table.

```json
{
  "program_id": "6B06102",
  "applicant_type": "local",
  "items": [],
  "warning": "The document list for this program is not published yet, please contact the admissions office.",
  "contact": "SDU Admissions Office, Abylai Khan 1/1, 040900 Kaskelen. Tel. +7 727 307 95 65"
}
```

### Program not found — 404

Uses the catalogue error contract:

```json
{ "error_code": "PROGRAM_NOT_FOUND", "message": "Program not found." }
```

## Schema confirmation (T4.1)

Table `program_document_requirement` (migration `0004`): `program_id` → `program.program_id` (on delete cascade), `applicant_type` (`local` / `international`), `name`, `document_format` (`original` / `copy`), `translation_required`, `notarisation_required`, `deadline` (free text), `display_order`.

| Who         | For                              | Confirmed  |
| ----------- | -------------------------------- | ---------- |
| Dinmukhamed | T4.1 — part of the US1 program data | confirmed 2026-09-22 |
