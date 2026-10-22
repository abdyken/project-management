# US26 QA record — checklist PDF

Date: 2026-10-22. Local API on `feature/sprint-5-applicant-area`. Live acceptance open.

| Check | Result |
| --- | --- |
| `tests/test_applicant.py`, PDF extraction with pypdf | PASS: public and personal exports in EN/RU/KK; current official document names, formats and deadlines; personal prepared count; no applicant e-mail in exports; missing-list warning; unknown/invalid request rejection; authentication/no-store for private exports |
| Applicant browser matrix (part of **97/97**) | PASS: attachment downloads in Chromium/Firefox at 360/768/1280 px |
| Rendered visual check, official Computer Science international checklist in Kazakh | PASS: both pages inspected with Poppler; Kazakh Unicode glyphs, wrapped long requirements, aligned status column, source/contact, margins and page numbers; no clipping or overlap |

Both endpoints render a current checklist snapshot with ReportLab and bundled licensed DejaVu Sans. Public exports have no personal progress; personal exports require a saved checklist and a valid applicant session. Official document text remains as published, with translated interface labels.

US26QATest pass and fail cases pass locally.
