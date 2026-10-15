# US19 QA record — staff login and roles

Date: 2026-10-15. Local run: full Docker stack (`docker compose up --build`, web on `http://localhost:8080`) on `feature/sprint-4-staff-area`. Live run: after deployment, see the end of this file.

| Check | Result |
| --- | --- |
| `tests/test_staff_auth.py`: salted scrypt hashes, HttpOnly/Secure/SameSite=Strict cookie on `/api/staff`, only the token hash stored, 401 without a session, same answer for a wrong password and an unknown e-mail, logout, expiry, officer 403 / admin 200 on `/users`, 6th failed login in 15 minutes blocked (per account and per IP), sliding window, deactivation and password reset log out, `create_staff_user.py` never prints the password | 13 passed |
| `curl` through nginx: login → `me` → `users` → logout → `me` 401 | PASS |
| `frontend/e2e/staff-qa.mjs` — Google Chrome at 360, 768 and 1280 px (US19 part) | **25/25 PASS** |

Scripted browser checks per width: `/staff` without a session opens the login page with `next`; a wrong password shows "Wrong e-mail or password" (checked once per run: five failures in 15 minutes lock the login, and repeated runs did trigger the lock); login opens the staff area; the cookie is HttpOnly with path `/api/staff` and page scripts cannot read it; no chat widget in the staff area; the session survives a reload; after logout the back button shows the login page, not staff data; `/api/staff/me` after logout is 401. At 360 px the header puts the page links on a second row (a first run showed the logout button cut off; fixed).

Firefox: Playwright's browser download did not complete on this machine, so the run used the installed Google Chrome only.

US19QATest: Pass (an officer logs in, sees FAQ, Inbox and Dashboard, logs out, back shows no staff data) — PASS locally. Fail case (staff data without login, a password in a log, the 6th wrong password accepted) — does not happen.
