# FAQ research: US8 (RU/KK) and US18 (new items)

Collected on 2026-10-08, only from sdu.edu.kz. Nothing was translated by me: every RU/KK answer uses the wording of the official RU/KZ twin page, shortened into a plain sentence. Every fact also has an official source. Questions are my phrasing.

## Counts

| | RU filled | RU null | KK filled | KK null |
|---|---|---|---|---|
| Task A: 35 existing items (translations.json) | 28 | 7 | 22 | 13 |
| Task B: 40 new items faq-036…faq-075 (new_items.json) | 38 | 2 | 35 | 5 |

- Task B: 40 new EN items, all with a verbatim EN quote. last_update is 2026-10-08.
- New category: student-services (military department, student ID, medical center, inclusion). All other items reuse the existing categories.

## How it was checked

- Each source page was downloaded with curl and its twins were taken from the hreflang="ru" / hreflang="kz" link tags. The source_link_ru / source_link_kk values are those exact hreflang URLs (percent-encoded as published).
- A script checked every evidence fragment (EN, RU, KK) against the page text. All 75 items pass: each fragment occurs verbatim after link markers are removed and whitespace is collapsed. When a quote joins parts that are not next to each other on the page, they are separated by " … ". Table rows are quoted cell by cell, separated by spaces, the same way as the existing faq.json evidence.
- The same script checked every number in every answer against the page. The only misses are the medical-center hours in faq-071 (see "Uncertain").
- I left faq.json and every other repo file untouched.

## Every null and its reason

| faq_id | lang | reason |
|---|---|---|
| faq-001 | kk | The KZ twin (hreflang="kz") of this source page is published in English, not Kazakh. Its text matches the EN page word for word, so there is no official Kazakh wording. |
| faq-003 | ru | The RU twin's “Онлайн подача документов” block only says documents are uploaded online and links the instruction. It does not contain the facts that a State Grant application is possible without an electronic signature or pedagogical exam results, or that originals must reach the admissions commission before August 25. |
| faq-003 | kk | The KZ twin's “Онлайн құжат тапсыру” block only says documents can be uploaded online and links the instruction. It does not contain the State Grant without e-signature / pedagogical exam sentence or the “originals before August 25” sentence. |
| faq-004 | kk | The KZ twin (hreflang="kz") of this source page is published in English, not Kazakh. Its text matches the EN page word for word, so there is no official Kazakh wording. |
| faq-006 | kk | The KZ twin (hreflang="kz") of this source page is published in English, not Kazakh. Its text matches the EN page word for word, so there is no official Kazakh wording. |
| faq-007 | kk | The KZ twin (hreflang="kz") of this source page is published in English, not Kazakh. Its text matches the EN page word for word, so there is no official Kazakh wording. |
| faq-008 | ru | Lists differ. RU item 5 is “Сертификат КТ” (EN: copy of the test certificate for the chosen program, “if you have one”); the RU grant list is “Сертификат КТ, копия удостоверение и диплом с приложением; 4 шт. Фотокарточки” (EN: CT certificate and 4 photos only). RU also says to send the documents to admissions@sdu.edu.kz and drops “not required during lockdown”. |
| faq-008 | kk | Grant document list differs: KZ “КТ сертификаты, жеке куәлік көшірмесі және диплом приложениясымен; 3 х 4 өлшеміндегі фотосурет (4 дана)” adds an ID copy and the diploma with supplement, which the EN item does not list. KZ also asks to send the documents to admissions@sdu.edu.kz. |
| faq-010 | kk | The KZ twin (hreflang="kz") of this source page is published in English, not Kazakh. Its text matches the EN page word for word, so there is no official Kazakh wording. |
| faq-012 | ru | Different condition: RU says “Абитуриенты, имеющие сертификат IELTS 5.5 и выше, могут предоставить его сканированную копию для освобождения от Вступительного экзамена” — the EN requirement “each section min 5.0” is missing, so the waiver rule differs. |
| faq-012 | kk | The KZ twin (hreflang="kz") of this source page is published in English, not Kazakh. Its text matches the EN page word for word, so there is no official Kazakh wording. |
| faq-013 | kk | The source page has no Kazakh twin: its HTML has only hreflang="ru" and hreflang="en" alternates. |
| faq-016 | kk | The KZ twin (hreflang="kz") of this source page is published in English, not Kazakh. Its text matches the EN page word for word, so there is no official Kazakh wording. |
| faq-017 | ru | Missing fact: the RU tuition-fees page says the student “обязан произвести оплату в зависимости от количества выбранных им предметов” but not that payment is made before the start of the semester (EN: “needs to make payment accordingly before the start of the semester”). |
| faq-019 | ru | Missing fact: the RU admission page never gives the code. Its FAQ says only “заполнить бланк, указав группу специальностей и вуз”, and its state-grant table has no “SDU code” column. (The RU master page does say “Код SDU – 302”, but that is a different source page.) |
| faq-023 | kk | Missing facts: the KZ admission page's “Студенттер үйі” block has only “Студенттер үйіндегі орын саны шектеулі. Орындар ең алдымен 1-курс студенттеріне беріледі. 2, 3 және 4 курс студенттері 25 тамыздан кейін ғана өтініш бере алады.” It has no application deadline (August 25) and no check-in date (August 28). The KZ accommodation page has no dates either. |
| faq-032 | ru | Conflicting number: RU says the foreign-language test is waived with “IELTS 6.0,TOEFL (IBT 60, PBT 498)”. EN says IELTS 5.5. |
| faq-032 | kk | Conflicting number: KZ says “Шет тілі тесті (IELTS 6.0, TOEFL (IBT 60, PBT 498)”. EN says IELTS 5.5. KZ also does not say the test part is “not required”. |
| faq-035 | ru | Missing fact: the RU admission page lists the same e-mails and phones, but “+7 702 000 11 33” appears with no “only WhatsApp text” note (only a wa.me link). The RU international page drops the note too. EN says the number takes WhatsApp text messages only. |
| faq-035 | kk | Missing fact: same as RU. The KZ admission page lists the e-mails and both phones, but the “only WhatsApp text” restriction on +7 702 000 11 33 is missing. |
| faq-043 | kk | Different wording of the rule: KZ says the applicant “ағылшын тілін міндетті сабақ ретінде алу керек немесе Foundation бағдарламасы бойынша оқуға түсу керек” (must), while EN and RU say it is recommended. |
| faq-048 | kk | The KZ twin (hreflang="kz") of this source page is published in English, not Kazakh. Its text matches the EN page word for word, so there is no official Kazakh wording. |
| faq-058 | ru | Missing fact: the RU FAQ answer only says to apply as soon as you receive the SDU registration form. The rule “a student visa can be issued no earlier than 90 days before the start date” is absent. |
| faq-058 | kk | Missing fact: the KZ FAQ answer has the same gap as RU. The 90-day rule is absent. |
| faq-070 | kk | Different fact: the KZ FAQ says “Бакалавриат/магистратура студенттерінің өтініштері қабылданбайды!” (applications from bachelor/master students are not accepted). The word “graduating” is missing, so the sentence contradicts the eligibility list in the same answer. |
| faq-073 | ru | Missing: the RU financial-aid page has no Qazaq Republic scholarship section. It lists only SDU grants for SPT and INFOMATRIX ASIA winners. |
| faq-074 | kk | The source page has no Kazakh twin: its HTML has only hreflang="ru" and hreflang="en" alternates. |

## Conflicts between language versions (and between SDU pages)

These affect items:

1. Master's CT foreign-language waiver (faq-032): EN says IELTS 5.5. RU and KZ say IELTS 6.0. Both RU/KK are null. The office needs to confirm which is current.
2. Master's documents (faq-008): the RU/KZ grant lists add an ID copy and the diploma with supplement. RU item 5 is "Сертификат КТ", not "copy of test certificate (if you have one)". RU/KZ also say to e-mail the documents to admissions@sdu.edu.kz. EN still says "not required during lockdown".
3. International placement-test waiver (faq-012): EN says "IELTS 5.5 (each section min 5.0)". RU says only "IELTS 5.5 и выше".
4. The KZ international admissions page (/halykaralyk-kabyldau-komissyasy/) is the English text, not Kazakh. That makes KK null for faq-001, 004, 006, 007, 010, 012, 016 and new faq-048.
5. The RU local admissions page never gives SDU code 302 (faq-019). It also lacks the "apply for State Grant without e-signature" and "originals before August 25" sentences (faq-003). The KZ page lacks the same faq-003 sentences and the dormitory deadline (Aug 25) and check-in date (Aug 28) (faq-023).
6. "+7 702 000 11 33 (only WhatsApp text)" (faq-035): the note exists only on the EN international page. RU/KZ show the number with a wa.me link but no "text only" restriction. If the team accepts dropping that restriction, a reduced RU/KK contacts item can be built from the same pages: the e-mails and both phone numbers are identical.
7. Tuition payment timing (faq-017): EN and KZ say "pay before the start of the semester". RU omits it.
8. Foundation-language rule (faq-043): EN and RU say English as a compulsory subject or the Foundation program is recommended. KZ says it is required ("керек").
9. Exchange eligibility (faq-070): KZ drops the word "graduating" ("Бакалавриат/магистратура студенттерінің өтініштері қабылданбайды!"), so the KZ text contradicts itself.
10. Visa timing (faq-058): only EN has the rule "visa issued no earlier than 90 days before the start date". The RU/KZ visa extension lists also omit "copy of passport", so faq-055 covers only the 30/14 working-day timing, which matches in all three.
11. Master ECTS: the EN master page says "To graduate with master's degree a student needs to cover 240 ECTS". The tuition-fees page (EN/RU/KZ) says 120 ECTS for master's and 180 ECTS for PhD. faq-064 uses the tuition-fees page, but the master page looks wrong and should be reported to the office.
12. Academic difference courses: the transfer page (EN/RU/KZ) says they are fee-based, including state-grant transfers (used in faq-052). The SSC FAQ quotes an internal rule "2.6. elimination of subject differences in the curricula of students is carried out free of charge". The office should confirm.

Found but not used in any item, for the office review:

13. Student organisations count: EN admission FAQ 35, EN international FAQ 28, RU international FAQ 29, student-fund page 28 (RU intro says 40), SSC FAQ "27". faq-018 uses the student-fund fee paragraph, which says 28 in all three languages.
14. Exchange numbers: EN admission FAQ says "more than 100 students" a year, RU/KZ say "about 100". The SSC FAQ says 47 partner universities and the IRO page says about 33 MoUs. I did not use any of these numbers.
15. Dormitory: capacity is 1280 people (EN) vs 1120 (RU/KZ), and the places boards show 560/560 (EN) vs 250/250 (RU/KZ). There are three different required-document lists: the admission page (2 photos, copies of 075, ID, payment), the EN accommodation page (4 photos, ...) and the RU/KZ accommodation page (adds application, power of attorney for minors, address certificate, admission confirmation). The Dorm-Service BIC is HSBKKZKX on the admission pages but KZKOKZKX on the accommodation page. Not used.
16. State-grant count tables: the EN bachelor table (e.g. B057 IT 5100) differs from the RU/KZ tables (4800 full / 4602 shortened / 300). The PhD 2025-2026 grants are 3 groups x 1 (EN/KZ) vs 21 across 7 groups (RU). Not used.
17. UNT-discount table: the EN row "6B01702 Computer Science" under the School of Education is RU "Иностранный язык: два иностранных языка", so it is mislabelled in EN. Not used (faq-045 only uses the SITAM rows, which match).
18. Visa invitation form (faq-024): the RU/KZ "скачать" link points to a file on nu.edu.kz (Nazarbayev University). EN says the form is downloadable from the university's website. The facts in faq-024 still match.
19. Medical center name (faq-071): EN "Zhanuya Zhumabek Med Center", KZ "Жанұя Жұмабек Мед", RU "Жануя".
20. ISPT host-country lists differ between EN and RU. faq-013 does not mention countries.

## Uncertain / judgement calls

- faq-071 hours: the EN page shows "(900 - 1800)" because the superscripts were lost. The RU HTML has 9 and 18 with superscript 00, so all three answers say 9:00–18:00.
- Small differences kept in filled answers: RU/KZ dorm laundry is "550 тг" without "per wash" (faq-049). KZ security has no "24/7" ("толыққанды аумақ күзеті"). RU/KZ do not label the MBA programs "Master" (faq-031). The RU arrival list says "сертификат" without "valid" (faq-007). Each RU/KK answer states only what its own page says.
- faq-065/066 calendar: the dates come from the "1 year" tab. Spring classes start 18.01.2027 for all years, but the 08–16.01.2027 registration window quoted is the first-year tab.
- faq-070: the EN text says "starting from the second year of the second semester". The answer reads it as "second semester of the second year", which matches RU "со второго курса второго семестра".
- faq-047 (bank details): the EN admission page prints them in Russian, and the answer copies them as published.
- Undated pages (not tied to a campaign, but not marked current either): the FAQ blocks (faq-036–040), SSC FAQ (faq-067–070), financial aid / Qazaq Republic (faq-073), ISPT registration procedure (faq-074; the page still shows 2025 results and a 2025–2026 fee list). Worth confirming with the office.

## Task B topics not covered (no usable official text)

- Refunds: no page found.
- Tuition installments: none published. Kaspi Red installments exist only for the dormitory (already in faq-022).
- Health insurance for international students: not found.
- Admissions office address and opening hours: not published. Only the legal address appears in the payment details. The visa office (faq-056) and SSC (8:30–17:30) hours are published.
- Military department: there is no dedicated page (search finds nothing). The info comes from the SSC FAQ (faq-067).
- UNT minimum / threshold scores per program: only in linked Google Drive PDFs, not parsed. The journalism program page shows thresholds 100/80, but it is undated and also says "Degree: Bachelor of Law" and "2024-2025" for the exam, so I did not use it.
- Master/PhD 2026 deadlines: the master page lists only 2025 dates (and mentions 2023), so it is outdated. The PhD page has none.
- SPT olympiad: /en/spt/ redirects to /ru/spt/. The financial-aid SPT counts (18/18/18/210) contradict the 2026 discount list (27/27/27/225), so I skipped them.
- Skipped as unclear or long: "Early Bird January 25% / March 15%" (listed with no explanation), partner-school discounts (long list), "12 ISPT grants per country" (not clearly 2026), vacant grants (2024).
