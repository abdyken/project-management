# Baseline UI audit (before the redesign)

**Date:** 20.11.2026.
**Method:** ECC `design-system` visual audit plus AI-slop check, and the `impeccable`
review of the incumbent UI.
**Evidence:**
- screenshots of the local stack at 360 and 1280 px in `baseline-2026-11-20/`
  (home, programmes, programme 6B06102, admissions hub, eligibility, login, compare)
- a code review of `frontend/src`

This file is the "before" record. The same audit runs again after each redesign phase.

## Scores (0-10)

| # | Dimension | Score | Evidence | Fix in the redesign |
| --- | --- | --- | --- | --- |
| 1 | Colour consistency | 5 | Tokens exist in `index.css:31-53`, but the header logo is a lime-green `#a0ec06` mark that is neither SDU's logo nor in the palette (`public/logo.svg`). Hard-coded hex values: dashboard chart (`StaffDashboardPage.tsx:11-12`), `text-[#1b3a4b]` (`ui/button.tsx:14`), globe RGB arrays (`HeroGlobe.tsx:37-39`), and `#c4a574` repeated in marker CSS (`index.css:101-112`). | Use the real SDU logo and brand colours; every colour comes from a token. |
| 2 | Typography hierarchy | 4 | One family (Inter) at 400/500/600 everywhere. h1 ranges 2xl → 6xl between pages. Body is almost always `text-sm` muted (218 uses), including hero leads. 13 tiny uppercase tracked labels, some 10 px (`ChatMessage.tsx:162`). | A display + text pairing, one type scale for all pages, 16 px body. |
| 3 | Spacing rhythm | 5 | Tailwind's default scale, but page shells vary: `max-w-5xl/3xl/2xl/md`, `py-10/12/16`, and some pages lack `sm:px-6`. | A `PageShell` with three widths and one vertical rhythm. |
| 4 | Component consistency | 4 | Two card languages (sharp `border bg-card` vs `rounded-xl border`). Select styling defined twice (`staff/styles.ts:1`, `ProgramFilters.tsx:20`). `labelClass` copied 4× with different tracking. Two StatusBadges. `fieldClass` has no focus ring while `Input` does. Hand-rolled tabs. Only 3 shadcn primitives. | Shared Card, Select, Field, Tabs, Badge, StatusBadge, Table, Stepper, Callout. |
| 5 | Responsive | 6 | No horizontal overflow at 360/768/1280 (QA-checked). On mobile the chat launcher sits on top of the globe. The programmes list is 64 identical cards stacked about 7,000 px tall at 1280 and longer on phones, with no paging or side filters. | Finder layout with side filters, count and compact rows; a launcher position that clears content. |
| 6 | Dark mode | 0 | None (`@custom-variant dark` declared, no values). | Not required: applicants use it on phones in daylight. Stays light-only, stated in DESIGN.md. |
| 7 | Animation | 6 | Restrained and reduced-motion-safe (globe pauses off-screen). Almost no state feedback beyond colour transitions; `animate-pulse` only. | One motion vocabulary (0.2–0.3 s ease) for hover, disclosure and focus moves. |
| 8 | Accessibility | 8 | Strong: chat focus return and Escape, `aria-live` announcers, focus management on the application form, `aria-pressed` language switcher, 16 px mobile inputs, status not shown by colour alone. Weak: gold step numbers `#c4a574` on `#f6f3ee` are about 2:1 (decorative but read as content); 10–11 px uppercase labels. | Keep everything that works; ≥ 4.5:1 for all text; no text under 12 px. |
| 9 | Information density | 5 | The programme detail table is clear, but the deadline column repeats the same long sentence on every row. The admissions hub cards show only a number and a title, with no description. The home page carries no deadlines, costs or paths. | Real data on the home page (dates, cost, paths), hub cards with one-line purpose, de-duplicated deadline text. |
| 10 | Polish | 5 | Few hover states; buttons have no directional affordance; footer is two lines; no breadcrumbs outside the guidance area; inconsistent "program"/"programme" spelling. | Arrow CTAs, a full footer, consistent terminology and states. |

**Total: 48 / 100.**

## AI-slop check

| Pattern | Present? | Where |
| --- | --- | --- |
| Gradients everywhere / purple-blue defaults | No | — |
| Glassmorphism, heavy shadows | No | one `blur-2xl` halo (`HeroGlobe.tsx:135`) |
| Generic hero: slogan + abstract visual | **Yes** | "Look up a program. / Ask the office." + spinning globe (`HomePage.tsx:27-50`) |
| Personality-free sans everywhere | **Yes** | Inter for every role |
| Numbered 01/02/03 feature steps | **Yes** | `HomePage.tsx:52-62`, `AdmissionsPages.tsx:47` |
| Tiny uppercase tracked eyebrows on every block | **Yes** | 13 places |
| Uniform identical card grids | **Yes** | programmes, admissions hub, dashboard tiles |
| Defensive AI-product copy | **Yes** | "Nothing here invents a rule." |
| Emoji as UI | **Yes** | `👍 · 👎` in `StaffDashboardPage.tsx:233` |
| Off-brand identity | **Yes** | lime-green placeholder logo instead of SDU's mark |

**Verdict:** this is not "loud" slop. It is template slop: a calm, generic SaaS look with
no university identity. The fix is identity (SDU logo, colours, real campus
photography, a real type pairing) and institutional structure (paths, dates, costs,
finder), not more decoration.
