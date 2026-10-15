import { chromium, firefox } from "playwright"
import fs from "node:fs"

// Sprint 4 staff area QA: US19 login, guard and logout at every width; at 1280 px also the
// US20 FAQ editor, US22 inbox and US9 dashboard scenarios. Needs a staff account:
//   STAFF_EMAIL=... STAFF_PASSWORD=... BASE_URL=http://localhost:8080 node e2e/staff-qa.mjs
// CHANNEL=chrome uses the installed Google Chrome instead of Playwright's Chromium.
// The FAQ edit is reverted and the item created from the inbox is retired at the end.
const BASE = process.env.BASE_URL ?? "http://localhost:5173"
const OUT = process.env.OUT ?? "e2e/shots"
const EMAIL = process.env.STAFF_EMAIL
const PASSWORD = process.env.STAFF_PASSWORD
if (!EMAIL || !PASSWORD) {
  console.error("Set STAFF_EMAIL and STAFF_PASSWORD")
  process.exit(2)
}
fs.mkdirSync(OUT, { recursive: true })

const results = []
function record(browser, width, check, ok, detail = "") {
  results.push({ browser, width, check, ok, detail })
  console.log(`${ok ? "PASS" : "FAIL"} ${browser} ${width}px ${check}${detail ? ` - ${detail}` : ""}`)
}

async function run(browserType, name, width) {
  const browser = await browserType.launch(name === "chromium" && process.env.CHANNEL ? { channel: process.env.CHANNEL } : {})
  const context = await browser.newContext({ viewport: { width, height: 820 }, locale: "en-US" })
  const page = await context.newPage()
  try {
    await page.goto(`${BASE}/staff`)
    await page.waitForURL(/\/staff\/login\?next=%2Fstaff/)
    await page.screenshot({ path: `${OUT}/staff-login-${name}-${width}.png` })
    record(name, width, "19.3 /staff without login opens the login page", true)

    await page.getByLabel("E-mail").fill(EMAIL)
    // One wrong password per run: five failures in 15 minutes lock the login (US19).
    if (width === WIDTHS[0]) {
      await page.getByLabel("Password").fill("definitely wrong")
      await page.getByRole("button", { name: "Log in" }).click()
      await page.getByRole("alert").waitFor()
      record(name, width, "19.3 wrong password shows an error", (await page.getByRole("alert").innerText()).includes("Wrong e-mail or password"))
    }

    await page.getByLabel("Password").fill(PASSWORD)
    await page.getByRole("button", { name: "Log in" }).click()
    await page.waitForURL(/\/staff$/)
    await page.getByRole("heading", { name: /^Welcome/ }).waitFor()
    record(name, width, "19.3 login opens the staff area", true)

    const cookies = await context.cookies()
    const session = cookies.find((cookie) => cookie.name === "staff_session")
    record(name, width, "19.2 session cookie is HttpOnly and limited to /api/staff", Boolean(session?.httpOnly && session.path === "/api/staff"))
    const readable = await page.evaluate(() => document.cookie.includes("staff_session"))
    record(name, width, "19.2 page scripts cannot read the session", !readable)
    record(name, width, "19.3 no chat widget in the staff area", (await page.getByRole("button", { name: /assistant|chat/i }).count()) === 0)

    await page.reload()
    await page.getByRole("heading", { name: /^Welcome/ }).waitFor()
    record(name, width, "19.3 the session survives a reload", true)

    await page.screenshot({ path: `${OUT}/staff-home-${name}-${width}.png`, fullPage: true })
    if (width >= 1280) await staffStories(page, name, width)
    // A staff page in the history, so "back" after logout has staff data to (not) show.
    await page.goto(`${BASE}/staff/faq`)
    await page.getByRole("heading", { name: "FAQ base" }).waitFor()

    await page.getByRole("button", { name: "Log out" }).click()
    await page.waitForURL(/\/staff\/login/)
    await page.goBack()
    await page.waitForURL(/\/staff\/login/)
    record(name, width, "19.3 back after logout shows the login page, not staff data", (await page.getByRole("heading", { name: /^Welcome/ }).count()) === 0)

    const me = await page.request.get(`${BASE}/api/staff/me`)
    record(name, width, "19.2 /api/staff/me after logout is 401", me.status() === 401)
  } catch (error) {
    record(name, width, "run", false, String(error).split("\n")[0])
    await page.screenshot({ path: `${OUT}/staff-${name}-${width}-error.png` }).catch(() => {})
  } finally {
    await browser.close()
  }
}

async function ask(page, question) {
  const response = await page.request.post(`${BASE}/api/assistant/ask`, {
    data: { question, session_id: `staff-qa-${Date.now()}-${Math.random()}` },
  })
  return response.json()
}

async function staffStories(page, name, width) {
  // US20: edit a published item, the assistant answers with the new text at once.
  await page.getByRole("link", { name: "FAQ" }).first().click()
  await page.getByRole("heading", { name: "FAQ base" }).waitFor()
  await page.getByLabel("Category").selectOption("dormitory")
  await page.waitForURL(/category=dormitory/)
  await page.getByText("3 items").waitFor()
  const rows = await page.locator("tbody tr").count()
  record(name, width, "20.3 category filter shows the 3 dormitory items", rows === 3, `${rows} rows`)
  await page.screenshot({ path: `${OUT}/staff-faq-list.png`, fullPage: true })

  await page.getByRole("link", { name: "How much does the dormitory cost?" }).click()
  const answer = page.getByLabel("Answer")
  await answer.waitFor()
  const original = await answer.inputValue()
  // A number, not a text marker: Gemini rephrases answers but must quote the cited numbers.
  const marker = "552,777"
  await answer.fill(original.replace("552,500", marker))
  await page.getByRole("button", { name: "Save", exact: true }).click()
  await page.getByRole("status").filter({ hasText: "Saved." }).waitFor()
  const changed = (await ask(page, "How much does the dormitory cost?")).answer
  record(name, width, "20.2 the assistant uses the edited answer without a restart", /552[,\s\u00a0]?777/.test(changed), changed.slice(0, 80))
  await page.screenshot({ path: `${OUT}/staff-faq-edit.png`, fullPage: true })
  await answer.fill(original)
  await page.getByRole("button", { name: "Save", exact: true }).click()
  await page.getByRole("status").filter({ hasText: "Saved." }).waitFor()
  record(name, width, "20.2 the edit is reverted", !/552[,\s\u00a0]?777/.test((await ask(page, "How much does the dormitory cost?")).answer))

  await page.getByRole("tab", { name: "Russian" }).click()
  await page.getByLabel("Question").fill("Сколько стоит общежитие?")
  const ruAnswer = await page.getByLabel("Answer").inputValue()
  await page.getByLabel("Answer").fill("")
  const warned = await page.getByRole("alert").filter({ hasText: "Russian" }).isVisible()
  const blocked = await page.getByRole("button", { name: "Save", exact: true }).isDisabled()
  record(name, width, "20.3 an incomplete translation is flagged and cannot be saved", warned && blocked)
  await page.getByLabel("Answer").fill(ruAnswer)

  // US22: an unanswered question becomes an FAQ item from the inbox.
  const question = `Is there a rowing club ${Date.now() % 100000} for students?`
  const before = await ask(page, question)
  record(name, width, "22.1 the test question has no FAQ answer yet", before.sources.length === 0)
  await page.goto(`${BASE}/staff/inbox`)
  const row = page.locator("li").filter({ hasText: question })
  await row.waitFor()
  record(name, width, "22.2 the question is in the inbox", true)
  await page.screenshot({ path: `${OUT}/staff-inbox.png`, fullPage: true })
  await row.getByRole("link", { name: "Answer" }).click()
  await page.getByLabel("Question").waitFor()
  record(name, width, "22.3 the editor opens with the question filled in", (await page.getByLabel("Question").inputValue()) === question)
  await page.getByLabel("Category").fill("student-services")
  await page.getByLabel("Answer").fill("Yes, SDU has a student rowing club; ask the student services office to join.")
  await page.getByLabel("Official page (https://…)").fill("https://sdu.edu.kz/en/student-life/")
  await page.getByRole("button", { name: "Save as draft" }).click()
  await page.getByRole("button", { name: "Publish" }).waitFor()
  const faqUrl = page.url()
  await page.getByRole("button", { name: "Publish" }).click()
  await page.getByRole("status").filter({ hasText: "marked as answered" }).waitFor()
  record(name, width, "22.3 publishing marks the inbox question as answered", true)
  const after = await ask(page, question)
  const faqId = faqUrl.split("/").pop().split("?")[0]
  record(name, width, "22.3 the same question now gets the new answer", after.sources.some((source) => source.faq_id === faqId), faqId)
  await page.goto(`${BASE}/staff/inbox?status=answered`)
  await page.locator("li").filter({ hasText: question }).waitFor()
  record(name, width, "22.2 the question is listed as answered", true)
  await page.goto(faqUrl.split("?")[0])
  await page.getByRole("button", { name: "Retire" }).click()
  await page.getByText("Retired: the assistant no longer uses this item.").waitFor()

  // US21: catalogue and document lists; the public pages show the edit at once.
  await page.goto(`${BASE}/staff/programs`)
  await page.getByRole("heading", { name: "Programs and document lists" }).waitFor()
  await page.getByLabel("Degree").selectOption("phd")
  await page.getByText("7 programs").waitFor()
  record(name, width, "21 degree filter shows the 7 PhD programs", (await page.locator("tbody tr").count()) === 7)
  await page.getByLabel("Degree").selectOption("")
  await page.getByText("64 programs").waitFor()
  await page.screenshot({ path: `${OUT}/staff-programs.png`, fullPage: true })

  // Kept to put the program back even when a step fails.
  const programApi = `${BASE}/api/staff/programs/6B04104`
  const originalProgram = await (await page.request.get(programApi)).json()
  const { program_id: _, documents: originalDocuments, updated_at: __, updated_by: ___, ...originalFields } = originalProgram
  try {
    await page.goto(`${BASE}/staff/programs/6B04104`)
    const fee = page.getByLabel("Fee per ECTS, local (KZT)")
    await fee.waitFor()
    const originalFee = await fee.inputValue()
    await fee.fill("43000")
    await page.getByRole("button", { name: "Save facts" }).click()
    await page.getByRole("form", { name: "Facts" }).getByRole("status").waitFor()
    const publicProgram = await (await page.request.get(`${BASE}/api/programs/6B04104`)).json()
    record(name, width, "21 a fee edit reaches the public catalogue at once", publicProgram.tuition_per_ects_kzt === 43000)
    const feeAnswer = (await ask(page, "How much does one ECTS cost for Finance (6B04104)?")).answer
    record(name, width, "21 the assistant answers with the new fee", /43[,\s\u00a0]?000/.test(feeAnswer), feeAnswer.slice(0, 80))

    const international = page.getByRole("region", { name: "Documents for international applicants" })
    const documentsBefore = await international.locator("li").count()
    await international.getByRole("button", { name: "Add document" }).click()
    const added = international.locator("li").last()
    await added.getByLabel(/Document/).fill("QA test document")
    await added.getByLabel("When").fill("With the application")
    await added.getByRole("button", { name: "Move up" }).click()
    await international.getByRole("button", { name: "Save list" }).click()
    await international.getByRole("status").waitFor()
    const checklist = await (await page.request.get(`${BASE}/api/programs/6B04104/checklist?applicant_type=international`)).json()
    const names = checklist.items.map((item) => item.name)
    record(name, width, "21 an added document is in the public checklist in its place", names[documentsBefore - 1] === "QA test document", `${names.length} items`)
    await page.screenshot({ path: `${OUT}/staff-program-edit.png`, fullPage: true })

    await page.goto(`${BASE}/programs/6B04104?applicant=international`)
    await page.locator('text="QA test document" >> visible=true').first().waitFor()
    record(name, width, "21 the public program page shows the edited list", true)
    await page.screenshot({ path: `${OUT}/public-program-after-edit.png`, fullPage: true })
  } finally {
    await page.request.put(programApi, { data: originalFields })
    await page.request.put(`${programApi}/documents/international`, { data: { documents: originalDocuments.international } })
  }
  const restored = await (await page.request.get(programApi)).json()
  record(
    name,
    width,
    "21 the program is reverted",
    restored.tuition_per_ects_kzt === originalProgram.tuition_per_ects_kzt &&
      JSON.stringify(restored.documents) === JSON.stringify(originalProgram.documents),
  )

  // US9: dashboard.
  await page.goto(`${BASE}/staff/dashboard`)
  await page.getByRole("heading", { name: "What applicants ask" }).waitFor()
  await page.locator('button[aria-label^="20"]').first().waitFor()
  const days = await page.locator('button[aria-label^="20"]').count()
  record(name, width, "9.2 seven days in the chart", days === 7, `${days} columns`)
  await page.locator('button[aria-label^="20"]').last().hover()
  record(name, width, "9.2 hovering a day shows its numbers", await page.getByRole("tooltip").isVisible())
  const questions = Number(await page.locator("p", { hasText: /^Questions$/ }).locator("xpath=following-sibling::p[1]").innerText())
  record(name, width, "9.2 the question count is shown", questions > 0, `${questions}`)
  await page.screenshot({ path: `${OUT}/staff-dashboard.png`, fullPage: true })
}

const WIDTHS = (process.env.WIDTHS ?? "360,768,1280").split(",").map(Number)
const BROWSERS = (process.env.BROWSERS ?? "chromium,firefox").split(",")
for (const [type, name] of [
  [chromium, "chromium"],
  [firefox, "firefox"],
].filter(([, name]) => BROWSERS.includes(name))) {
  for (const width of WIDTHS) await run(type, name, width)
}

const failed = results.filter((r) => !r.ok)
console.log(`\n${results.length - failed.length}/${results.length} checks passed`)
process.exit(failed.length ? 1 : 0)
