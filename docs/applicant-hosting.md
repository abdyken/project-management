# Applicant data hosting — Sprint 5 prerequisite

**22.10.2026: local implementation ready; live hosting decision pending.**

The current live portal uses the Oracle VM described in `deploy/oracle-vm/README.md`. The backlog explicitly requires a hosting decision before applicant accounts. The repository contains no recorded approval to store applicant account data there. Implementation therefore adds an explicit `APPLICANT_ACCOUNTS_ENABLED` deployment setting, defaulting to `false` on the VM. Local Docker enables it with a local mail inbox for verification and QA. Public catalogue, chat and public checklist PDFs work independently of this flag.

The account area stores e-mail, a salted scrypt password hash, language/reminder preferences, timestamps, hashed session/verification tokens, saved program/type pairs, document preparation flags and a reminder delivery ledger. It does not collect document files, grades, identity-document numbers or application forms. Verification expires after 24 hours; sessions expire after seven days by default. Account deletion cascades through sessions, saved programs, progress and reminder history. SMTP providers receive the destination address and the reminder/verification message. Operational access logs must not log request bodies or cookies; verification secrets travel in URL fragments and are stored only as hashes.

## Live enablement record

The Product Owner/repository owner records the chosen host, who operates it, backup handling and the configured SMTP sender/provider before enabling accounts. This is an outstanding project decision, not an automated claim about legal approval.

1. Record the hosting/SMTP decision here.
2. Set the VM environment values in `.env`: `SMTP_HOST`, `SMTP_PORT`, `SMTP_STARTTLS`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`. Keep secrets outside Git. Port 587 with STARTTLS is the default; local Mailpit uses 1025 without TLS. SMTP over implicit TLS (465) is not supported by this transport.
3. Set `APPLICANT_ACCOUNTS_ENABLED=true`; `PUBLIC_BASE_URL` is supplied from `SITE_HOST` by the VM compose file. Keep HTTPS and Secure cookies enabled.
4. Redeploy through the normal reviewed-PR/CI flow. Register a test account, verify through the real sender, test both applicant types, progress, personal PDF, opt-out and account deletion.
5. Record live QA and Product Owner acceptance in the sprint review and workbook.

Rolling back the API image does not remove the additive 0018 tables. Turning the flag off stops applicant routes and the worker after restart; it does not delete existing account data.
