# Applicant data hosting — Sprint 5 prerequisite

**22.10.2026: local implementation ready. Accounts live since 03.11.2026; applications since 20.11.2026 (see Sprint 7 below).**

The current live portal uses the Oracle VM described in `deploy/oracle-vm/README.md`. The backlog explicitly requires a hosting decision before applicant accounts. The repository contains no recorded approval to store applicant account data there. Implementation therefore adds an explicit `APPLICANT_ACCOUNTS_ENABLED` deployment setting, defaulting to `false` on the VM. Local Docker enables it with a local mail inbox for verification and QA. Public catalogue, chat and public checklist PDFs work independently of this flag.

The account area stores e-mail, a salted scrypt password hash, language/reminder preferences, timestamps, hashed session/verification tokens, saved program/type pairs, document preparation flags and a reminder delivery ledger. It does not collect document files, grades, identity-document numbers or application forms. Verification expires after 24 hours; sessions expire after seven days by default. Account deletion cascades through sessions, saved programs, progress and reminder history. SMTP providers receive the destination address and the reminder/verification message. Operational access logs must not log request bodies or cookies; verification secrets travel in URL fragments and are stored only as hashes.

## Sprint 7: applications and uploaded documents

Sprint 7 adds the most sensitive data so far: application forms (name, date of birth,
citizenship, phone, education) and scans of personal documents, stored on the `uploads`
volume of the same VM (ADR 0001, 0003). No IIN or passport numbers are collected.
Applications and files are deleted with the account.

**20.11.2026: hosting decision recorded and applications switched on.** The team confirmed
(Dinmukhamed, repository and VM owner, delivering Sprint 7 by the Product Owner's
decision) that applicant accounts, application forms and uploaded scans are stored on the
project's Oracle Cloud Always Free VM (region me-dubai-1) described in
`deploy/oracle-vm/README.md`:

| Question | Decision |
| --- | --- |
| Host | Oracle Cloud VM, `/opt/sdu-admissions`; data in the `pgdata` and `uploads` Docker volumes |
| Operated by | Dinmukhamed (Oracle account and `sudo` on the VM). Teammates with a VM login have no `sudo` and cannot read the backups |
| Backups | Daily at 02:00 Almaty by `sdu-admissions-backup.timer`, kept 14 days in `/var/backups/sdu-admissions` (owner `ubuntu`, mode 700), kept by Dinmukhamed. Restore tested 20.11.2026. Same disk as the data; occasional copies off the server to an encrypted disk |
| E-mail | The team's Gmail account through Google SMTP (port 587, STARTTLS); the app password only in the VM's `.env`. E-mails carry links, never notes or documents |
| Limits | 10 MB per file, 40 MB per application, 100 MB per account; uploads pause below 2 GB free disk; abandoned drafts deleted after 30 days |
| Switching off | `APPLICATIONS_ENABLED=false` in `.env` and `docker compose up -d`: routes and links disappear, stored data stays until deleted |

This records the team's project decision for a university course project, not a legal
assessment of personal data processing.

## Live enablement record

Sprint 6 also stores private admissions questions, office replies, their timestamps,
the last responding staff reference and notification delivery status. Account
deletion removes these records too. Notifications contain only the account link;
assessment questionnaires and scores are not persisted. Include this data footprint
in the same outstanding hosting/SMTP decision before enabling accounts.

The Product Owner/repository owner records the chosen host, who operates it, backup handling and the configured SMTP sender/provider before enabling accounts. This is an outstanding project decision, not an automated claim about legal approval.

1. Record the hosting/SMTP decision here.
2. Set the VM environment values in `.env`: `SMTP_HOST`, `SMTP_PORT`, `SMTP_STARTTLS`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`. Keep secrets outside Git. Port 587 with STARTTLS is the default; local Mailpit uses 1025 without TLS. SMTP over implicit TLS (465) is not supported by this transport.
3. Set `APPLICANT_ACCOUNTS_ENABLED=true`; `PUBLIC_BASE_URL` is supplied from `SITE_HOST` by the VM compose file. Keep HTTPS and Secure cookies enabled.
4. Redeploy through the normal reviewed-PR/CI flow. Register a test account, verify through the real sender, test both applicant types, progress, personal PDF, opt-out and account deletion.
5. Record live QA and Product Owner acceptance in the sprint review and workbook.

Rolling back the API image does not remove the additive 0018 tables. Turning the flag off stops applicant routes and the worker after restart; it does not delete existing account data.
