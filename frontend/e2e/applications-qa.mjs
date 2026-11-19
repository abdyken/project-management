import assert from "node:assert/strict"
import fs from "node:fs"
import { chromium, firefox, request } from "playwright"

// Sprint 7 (US31-US33, US6) against a disposable local stack with Mailpit and
// APPLICATIONS_ENABLED=true. Creates its own applicants (deleted at the end, with their
// files) and needs a staff account: STAFF_EMAIL and STAFF_PASSWORD.
const BASE = process.env.BASE_URL ?? "http://localhost:5173"
const MAIL = process.env.MAILPIT_URL ?? "http://localhost:8025"
const OUT = process.env.OUT ?? "e2e/shots"
const STAFF_EMAIL = process.env.STAFF_EMAIL
const STAFF_PASSWORD = process.env.STAFF_PASSWORD
const PASSWORD = "Sprint7-browser-local-only"
const PROGRAM = process.env.QA_PROGRAM ?? "6B06102"
const PDF = Buffer.concat([Buffer.from("%PDF-1.4\n"), Buffer.alloc(4096, 48)])
const PNG = Buffer.concat([Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]), Buffer.alloc(1024, 49)])
assert.ok(STAFF_EMAIL && STAFF_PASSWORD, "Set STAFF_EMAIL and STAFF_PASSWORD for a disposable staff account")
fs.mkdirSync(OUT, { recursive: true })
const results = []
const created = []

function record(browser, width, check, ok = true, detail = "") {
  results.push({ browser, width, check, ok })
  console.log(`${ok ? "PASS" : "FAIL"} ${browser} ${width}px ${check}${detail ? ` - ${detail}` : ""}`)
  assert.ok(ok, `${check} ${detail}`)
}

async function mailTo(address, subjectPart) {
  for (let attempt = 0; attempt < 50; attempt++) {
    const inbox = await (await fetch(`${MAIL}/api/v1/messages`)).json()
    const message = inbox.messages.find(
      (item) => item.To.some((to) => to.Address === address) && (!subjectPart || item.Subject.includes(subjectPart)),
    )
    if (message) return (await fetch(`${MAIL}/api/v1/message/${message.ID}`)).json()
    await new Promise((resolve) => setTimeout(resolve, 200))
  }
  throw new Error(`No e-mail "${subjectPart}" for ${address}`)
}

// A verified applicant with one saved local checklist, through the API.
async function applicant(email) {
  const api = await request.newContext({ baseURL: BASE })
  assert.equal((await api.post("/api/applicant/register", { data: { email, language: "en" } })).status(), 202)
  created.push(email)
  const token = (await mailTo(email, "Verify")).Text.match(/#token=([A-Za-z0-9_-]+)/)[1]
  assert.equal((await api.post("/api/applicant/verify", { data: { token, password: PASSWORD } })).status(), 200)
  assert.equal((await api.put(`/api/applicant/programs/${PROGRAM}/local`)).status(), 200)
  return api
}

async function login(page, email) {
  await page.goto(`${BASE}/account/login`)
  await page.getByLabel("E-mail", { exact: true }).fill(email)
  await page.getByLabel("Password", { exact: true }).fill(PASSWORD)
  await page.getByRole("button", { name: "Log in", exact: true }).click()
  await page.waitForURL(/\/account$/)
}

async function noOverflow(page) {
  return page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1)
}

async function run(type, name, width) {
  const stamp = `${name}-${width}-${Date.now()}`
  const email = `sprint7-${stamp}@example.com`
  const other = `sprint7-other-${stamp}@example.com`
  // CHROMIUM_CHANNEL=chrome uses an installed Google Chrome instead of Playwright's Chromium.
  const browser = await type.launch(type === chromium && process.env.CHROMIUM_CHANNEL ? { channel: process.env.CHROMIUM_CHANNEL } : {})
  const applicantContext = await browser.newContext({ viewport: { width, height: 900 }, locale: "en-US", acceptDownloads: true })
  const staffContext = await browser.newContext({ viewport: { width, height: 900 }, locale: "en-US", acceptDownloads: true })
  const page = await applicantContext.newPage()
  const staff = await staffContext.newPage()
  const errors = []
  for (const tab of [page, staff]) {
    tab.on("pageerror", (error) => errors.push(error.message))
    tab.on("console", (message) => {
      // A refused upload or a 4xx the page handles is logged by the browser as a failed resource; that is expected.
      if (message.type() === "error" && !/Failed to load resource/.test(message.text())) errors.push(message.text())
    })
  }
  const api = await applicant(email)
  const otherApi = await applicant(other)
  try {
    // US31: start from a saved checklist, fill in, save.
    await login(page, email)
    await page.getByRole("link", { name: "My applications", exact: true }).click()
    await page.getByRole("heading", { name: "My applications", level: 1 }).waitFor()
    await page.getByRole("button", { name: "Start application", exact: true }).first().click()
    await page.waitForURL(/\/account\/applications\/\d+$/)
    const id = Number(page.url().split("/").pop())
    await page.getByText("Draft", { exact: true }).waitFor()
    record(name, width, "US31 application starts from a saved checklist as a draft", (await (await api.get(`/api/applicant/applications/${id}`)).json()).status === "draft")
    record(name, width, "US31 submit is blocked until the form and a document are there", await page.getByRole("button", { name: "Submit application" }).isDisabled())
    await page.getByLabel("Full name", { exact: true }).fill("Aigerim Bekova")
    await page.getByLabel("Date of birth", { exact: true }).fill("2008-03-14")
    await page.getByLabel("Citizenship", { exact: true }).fill("Kazakhstan")
    // Validation: a phone with letters is refused before anything is sent.
    const phone = page.getByLabel("Phone", { exact: true })
    await phone.fill("call me maybe")
    await page.getByRole("button", { name: "Save", exact: true }).click()
    record(name, width, "US31 an invalid phone is refused in the browser", await phone.evaluate((input) => input.validity.patternMismatch))
    record(name, width, "US31 nothing is saved while a field is invalid", (await (await api.get(`/api/applicant/applications/${id}`)).json()).phone === null)
    record(name, width, "US31 the birth date cannot be in the future", (await page.getByLabel("Date of birth", { exact: true }).getAttribute("max")) === new Date().toISOString().slice(0, 10))
    await phone.fill("+7 701 000 00 00")
    await page.getByLabel("Previous education", { exact: true }).selectOption("school")
    await page.getByLabel("Year of graduation", { exact: true }).fill("2026")
    await page.getByLabel("I agree that SDU processes the data in this application to review it.").check()
    await page.getByRole("button", { name: "Save", exact: true }).click()
    await page.getByRole("status").filter({ hasText: /^Saved$/ }).waitFor()
    record(name, width, "US31 form saved", (await (await api.get(`/api/applicant/applications/${id}`)).json()).full_name === "Aigerim Bekova")

    // US32: a fake file is refused, a real scan uploads and ticks the tracker.
    const inputs = page.locator('input[type="file"]')
    await inputs.last().setInputFiles({ name: "not-a-pdf.pdf", mimeType: "application/pdf", buffer: Buffer.from("MZ executable") })
    await page.getByRole("alert").filter({ hasText: "Upload a PDF, JPEG or PNG file." }).waitFor()
    record(name, width, "US32 a file that is not PDF/JPEG/PNG is refused by content")
    // The real path: the visible button opens the system file picker.
    const [chooser] = await Promise.all([page.waitForEvent("filechooser"), page.getByRole("button", { name: /^Upload a scan: / }).first().click()])
    await chooser.setFiles({ name: "certificate.pdf", mimeType: "application/pdf", buffer: PDF })
    await page.getByText("certificate.pdf", { exact: true }).waitFor()
    record(name, width, "US32 the upload is announced", (await page.getByRole("status").filter({ hasText: "Uploaded: certificate.pdf" }).count()) === 1)
    record(name, width, "US32 the hidden file inputs are out of the Tab order", await inputs.evaluateAll((all) => all.every((input) => input.tabIndex === -1)))
    // An extra document can be removed again; focus returns to the Documents heading.
    await inputs.last().setInputFiles({ name: "extra.png", mimeType: "image/png", buffer: PNG })
    await page.getByText("extra.png", { exact: true }).waitFor()
    await page.getByRole("button", { name: "Remove: extra.png" }).click()
    await page.getByText("extra.png", { exact: true }).waitFor({ state: "detached" })
    record(name, width, "US32 a document can be removed", await page.evaluate(() => document.activeElement?.id === "documents-title"))
    record(name, width, "US32 scan uploaded to its checklist document", await page.getByText("Uploaded", { exact: true }).first().isVisible())
    const detail = await (await api.get(`/api/applicant/applications/${id}`)).json()
    const documentId = detail.documents[0].id
    const saved = await (await api.get(`/api/applicant/programs/${PROGRAM}/local`)).json()
    record(name, width, "US32 the scan ticks the document in the tracker (US25)", saved.prepared >= 1)
    record(name, width, "US31 layout fits the screen", await noOverflow(page))
    await page.screenshot({ path: `${OUT}/applications-${name}-${width}-form.png`, fullPage: true })

    // Isolation: another applicant gets 404 for the application and the file.
    record(name, width, "US32 another applicant cannot open the application", (await otherApi.get(`/api/applicant/applications/${id}`)).status() === 404)
    record(name, width, "US32 another applicant cannot download the file", (await otherApi.get(`/api/applicant/applications/${id}/documents/${documentId}`)).status() === 404)

    await page.getByRole("button", { name: "Submit application", exact: true }).click()
    await page.getByText("Submitted", { exact: true }).waitFor()
    record(name, width, "US31 submitted application is read-only", await page.getByLabel("Full name", { exact: true }).isDisabled())
    record(name, width, "US31 focus moves to the new status after submitting", await page.evaluate(() => document.activeElement?.getAttribute("role") === "status"))

    // A second draft (international checklist) can be deleted with its files.
    assert.equal((await api.put(`/api/applicant/programs/${PROGRAM}/international`)).status(), 200)
    await page.goto(`${BASE}/account/applications`)
    await page.getByRole("button", { name: "Start application", exact: true }).first().click()
    await page.waitForURL(/\/account\/applications\/\d+$/)
    const draftId = Number(page.url().split("/").pop())
    await page.getByRole("button", { name: "Delete draft", exact: true }).click()
    record(name, width, "US31 deleting asks for confirmation first", await page.evaluate(() => document.activeElement?.textContent?.includes("Delete this draft")))
    await page.getByRole("button", { name: "Delete draft", exact: true }).click()
    await page.waitForURL(/\/account\/applications$/)
    record(name, width, "US31 a draft can be deleted", (await api.get(`/api/applicant/applications/${draftId}`)).status() === 404)
    await page.goto(`${BASE}/account/applications/99999999`)
    await page.getByRole("alert").filter({ hasText: "Application not found." }).waitFor()
    record(name, width, "US31 an unknown application shows not found", (await page.getByRole("button", { name: "Try again" }).count()) === 0)

    // US33: staff queue, document download, request changes.
    await staff.goto(`${BASE}/staff/login`)
    await staff.getByLabel("E-mail", { exact: true }).fill(STAFF_EMAIL)
    await staff.getByLabel("Password", { exact: true }).fill(STAFF_PASSWORD)
    await staff.getByRole("button", { name: "Log in", exact: true }).click()
    await staff.waitForURL(/\/staff$/)
    await staff.goto(`${BASE}/staff/applications`)
    await staff.getByRole("heading", { name: "Applications", level: 1 }).waitFor()
    await staff.getByLabel("Programme", { exact: true }).selectOption(PROGRAM)
    await staff.waitForURL(new RegExp(`program=${PROGRAM}`))
    record(name, width, "US33 the queue filters by programme", await staff.getByRole("link", { name: `Open #${id}` }).isVisible())
    await staff.getByRole("link", { name: `Open #${id}` }).click()
    await staff.getByRole("heading", { name: "Aigerim Bekova" }).waitFor()
    const [download] = await Promise.all([staff.waitForEvent("download"), staff.getByRole("link", { name: "Download: certificate.pdf" }).click()])
    record(name, width, "US33 staff download the exact uploaded file", fs.readFileSync(await download.path()).equals(PDF))
    await staff.getByLabel("New status", { exact: true }).selectOption("needs_changes")
    record(name, width, "US33 a note is required to request changes", await staff.getByRole("button", { name: "Save status" }).isDisabled())
    await staff.getByLabel("Note to the applicant", { exact: true }).fill("Please attach a clearer scan of the certificate.")
    await staff.getByRole("button", { name: "Save status", exact: true }).click()
    await staff.getByRole("status").filter({ hasText: "Status saved: Changes requested." }).waitFor({ state: "attached" })
    record(name, width, "US33 staff requested changes", (await (await api.get(`/api/applicant/applications/${id}`)).json()).status === "needs_changes")
    record(name, width, "US33 staff layout fits the screen", await noOverflow(staff))

    // The applicant is e-mailed (link only), sees the note, corrects and resubmits.
    const mail = await mailTo(email, "status changed")
    record(name, width, "US33 status e-mail links to the application without the note", mail.Text.includes(`/account/applications/${id}`) && !mail.Text.includes("clearer scan"))
    await page.goto(`${BASE}/account/applications/${id}`)
    await page.getByText("Please attach a clearer scan of the certificate.").waitFor()
    record(name, width, "US33 applicant reads the office's note", await page.getByText("Changes requested", { exact: true }).isVisible())
    await page.locator('input[type="file"]').first().setInputFiles({ name: "certificate-clear.png", mimeType: "image/png", buffer: PNG })
    await page.getByText("certificate-clear.png", { exact: true }).waitFor()
    await page.getByRole("button", { name: "Submit application", exact: true }).click()
    await page.getByText("Submitted", { exact: true }).waitFor()
    record(name, width, "US31 corrected application submitted again")

    await staff.reload()
    await staff.getByLabel("New status", { exact: true }).selectOption("accepted")
    await staff.getByRole("button", { name: "Save status", exact: true }).click()
    await staff.getByText("This application is closed: no further status changes.").waitFor()
    record(name, width, "US33 staff accepted; closed applications cannot change", (await (await api.get(`/api/applicant/applications/${id}`)).json()).status === "accepted")

    // Rejection, opened directly by URL: a note is required, the applicant is told.
    const otherId = (await (await otherApi.post("/api/applicant/applications", { data: { program_id: PROGRAM, applicant_type: "local", language: "en" } })).json()).id
    const otherDetail = await (await otherApi.get(`/api/applicant/applications/${otherId}`)).json()
    assert.equal((await otherApi.put(`/api/applicant/applications/${otherId}`, { data: { full_name: "Daulet Sarsen", date_of_birth: "2007-09-01", citizenship: "Kazakhstan", phone: "+7 702 000 00 00", education_level: "school", graduation_year: 2026, consent: true } })).status(), 200)
    assert.equal((await otherApi.post(`/api/applicant/applications/${otherId}/documents`, { multipart: { file: { name: "diploma.pdf", mimeType: "application/pdf", buffer: PDF }, requirement_id: String(otherDetail.requirements[0].id) } })).status(), 201)
    assert.equal((await otherApi.post(`/api/applicant/applications/${otherId}/submit`)).status(), 200)
    await staff.goto(`${BASE}/staff/applications/${otherId}`)
    await staff.getByRole("heading", { name: "Daulet Sarsen" }).waitFor()
    await staff.getByLabel("New status", { exact: true }).selectOption("rejected")
    record(name, width, "US33 a note is required to reject", await staff.getByRole("button", { name: "Save status" }).isDisabled())
    await staff.getByLabel("Note to the applicant", { exact: true }).fill("The programme needs a bachelor's degree.")
    await staff.getByRole("button", { name: "Save status", exact: true }).click()
    await staff.getByText("This application is closed: no further status changes.").waitFor()
    record(name, width, "US33 staff rejected; the applicant is e-mailed", (await mailTo(other, "status changed")).Text.includes(`/account/applications/${otherId}`))

    // US6: the chat answers with the applicant's own status.
    await page.reload()
    await page.getByText("Accepted", { exact: true }).waitFor()
    await page.getByRole("button", { name: "Open admissions chat" }).click()
    const question = page.getByLabel("Your question", { exact: true })
    await question.fill("What is the status of my application?")
    await question.press("Enter")
    const log = page.getByRole("log", { name: "Conversation" })
    await log.getByText("accepted, your documents are complete", { exact: false }).waitFor({ timeout: 20_000 })
    record(name, width, "US6 chat gives the logged-in applicant their own status and next step", await log.getByText("Bring the originals", { exact: false }).isVisible())

    // US6 without an account: a general answer and no personal data.
    const visitorContext = await browser.newContext({ viewport: { width, height: 900 }, locale: "en-US" })
    const visitor = await visitorContext.newPage()
    await visitor.goto(BASE)
    await visitor.getByRole("button", { name: "Open admissions chat" }).click()
    await visitor.getByLabel("Your question", { exact: true }).fill("What is the status of my application?")
    await visitor.getByLabel("Your question", { exact: true }).press("Enter")
    const visitorLog = visitor.getByRole("log", { name: "Conversation" })
    await visitorLog.getByText("under My applications in your account", { exact: false }).waitFor({ timeout: 20_000 })
    record(name, width, "US6 a visitor gets the general answer without anyone's status", (await visitorLog.getByText("accepted, your documents", { exact: false }).count()) === 0)
    await visitorContext.close()

    // RU and KK pages.
    await page.goto(`${BASE}/account/applications`)
    await page.getByRole("button", { name: "Русский" }).click()
    await page.getByRole("heading", { name: "Мои заявки", level: 1 }).waitFor()
    await page.getByRole("button", { name: "Қазақша" }).click()
    await page.getByRole("heading", { name: "Менің өтініштерім", level: 1 }).waitFor()
    record(name, width, "US31 applications page in Russian and Kazakh", await noOverflow(page))
    await page.goto(`${BASE}/account/applications/${id}`)
    const kazakhSize = await page.getByText(/^\d+ КБ$/).first().waitFor().then(() => true, () => false)
    record(name, width, "US32 file sizes use the page language", kazakhSize)
    await page.getByRole("button", { name: "English" }).click()
    record(name, width, "Sprint 7 no frontend runtime errors", errors.length === 0, errors.join(" | "))
  } catch (error) {
    results.push({ browser: name, width, check: String(error), ok: false })
    console.error(error)
    await page.screenshot({ path: `${OUT}/applications-${name}-${width}-applicant-error.png`, fullPage: true }).catch(() => {})
    await staff.screenshot({ path: `${OUT}/applications-${name}-${width}-staff-error.png`, fullPage: true }).catch(() => {})
    throw error
  } finally {
    await api.dispose()
    await otherApi.dispose()
    await browser.close()
  }
}

try {
  const runs = (process.env.RUNS ?? "chromium:360,chromium:768,chromium:1280,firefox:1280").split(",")
  for (const run_ of runs) {
    const [browserName, width] = run_.split(":")
    await run(browserName === "firefox" ? firefox : chromium, browserName, Number(width))
  }
} finally {
  // Never leave QA applicants or their files behind, including on failure.
  for (const email of created) {
    const api = await request.newContext({ baseURL: BASE })
    try {
      const response = await api.post("/api/applicant/login", { data: { email, password: PASSWORD } })
      if (response.ok()) assert.equal((await api.delete("/api/applicant/me")).status(), 204)
    } finally {
      await api.dispose()
    }
  }
}
const failed = results.filter((item) => !item.ok)
console.log(`\n${results.length - failed.length}/${results.length} application checks passed`)
process.exitCode = failed.length ? 1 : 0
