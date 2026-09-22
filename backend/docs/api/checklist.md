# Document checklist API (US4)

## `GET /api/programs/{program_id}/checklist`

Returns requirements for one active programme and one applicant type.

```text
GET /api/programs/cs-bsc-en/checklist?applicant_type=international
```

`applicant_type` is required and is either `local` or `international`. Invalid or missing values return FastAPI's standard `422` validation response.

### Populated checklist — 200

```json
{
  "program_id": "cs-bsc-en",
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
  "warning": null
}
```

### No stored requirements — 200

This is intentionally not an unexplained empty list. The frontend and assistant must display `warning` and direct the applicant to the Admissions Office.

```json
{
  "program_id": "cs-bsc-en",
  "applicant_type": "local",
  "items": [],
  "warning": "Document requirements for this programme are not recorded yet. Please contact the Admissions Office."
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
