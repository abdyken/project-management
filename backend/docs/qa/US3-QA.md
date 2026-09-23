# US3 QA record — FAQ assistant (T3.7)

Local run on 2026-09-24 against the Docker stack, official FAQ base (`app/data/faq.json`, 35 items). The Product Owner rule still requires the same run on the deployed dev environment.

| ID | Scenario | Expected | Result |
| --- | --- | --- | --- |
| US3-A | "When is the application deadline for bachelor programs?" | Matching FAQ answer with its official source link | PASS — faq-002, link to sdu.edu.kz/en/admission-3-2/ |
| US3-A (QA sheet wording) | "What is the application deadline for the master program?" | Matching FAQ answer | PARTIAL — returns faq-001 (international applicants' deadlines, applies to all levels). SDU has not published 2026 master's dates, so the FAQ has no master-specific item. |
| US3-B | Off-topic question ("Who won the football world cup?") | "I could not find this information in the official FAQ" + admissions contact; question logged | PASS — logged in `admissions_followup` as `unanswered_question` |
| US3-C | Invented information | No answer outside the FAQ base | PASS — every answer is the verbatim FAQ text; below the threshold or for another degree the fixed fallback is returned |
| US3-D | Accuracy test set (20 paraphrased questions, 6 off-topic) | Accuracy and failures recorded | 24/26 (92%), 1 wrong answer — see [T3.7](../serdar-ai-tasks/T3.7-accuracy-test-set.md) |

Follow-up for the admissions office: add an official FAQ item for master's application dates once they are published.
