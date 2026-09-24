# US2 QA record — chat widget (T2.7)

Local run on 2026-09-24 against the Docker stack (`docker compose up --build`, http://localhost:8080) in Chrome, desktop width and 375 px (phone) width. The Product Owner rule still requires the same run on the deployed dev environment.

| ID | Scenario | Expected | Result |
| --- | --- | --- | --- |
| US2-A1 | Open the chat from any page (home, catalogue, program) | Widget opens; also opens with the keyboard (Tab + Enter) | PASS |
| US2-A2 | Type a question and send | Question shown as applicant message, typing indicator, then the answer with its **Source** link | PASS |
| US2-A3 | Navigate to another page and reopen | Whole session dialogue is still shown | PASS |
| US2-A4 | Empty or whitespace-only message | **Send** stays disabled; Enter does nothing | PASS |
| US2-A5 | Long message | Input stops at 500 characters, counter shows `500/500` | PASS |
| US2-B | No answer within 10 s (API container paused) | "The assistant is not responding, please try again or contact the admissions office"; the question stays in the input and can be resent | PASS |
| US2-C | Phone width (375 px) | Chat opens as a bottom sheet with its own close button; catalogue, filters and checklist fit without sideways scrolling | PASS |
| US2-D | Escape / close / minimise | Escape and × close the panel; minimise shows a bar that restores the dialogue | PASS |

Not run: Firefox (the US2 card mentions it; the sprint plan limits the matrix to Chrome and a phone screen).
