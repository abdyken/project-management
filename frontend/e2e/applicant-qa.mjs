import assert from "node:assert/strict"
import fs from "node:fs"
import { chromium, firefox, request } from "playwright"

// Use a disposable local database and Mailpit. This script creates one test account,
// changes only its own saved checklists and preferences, and deletes it on completion.
const BASE = process.env.BASE_URL ?? "http://localhost:5173"
const MAIL = process.env.MAILPIT_URL ?? "http://localhost:8025"
const OUT = process.env.OUT ?? "e2e/shots"
const EMAIL = `sprint5-${Date.now()}@example.com`
const PASSWORD = "Sprint5-local-test-only"
fs.mkdirSync(OUT, { recursive: true })
const results = []
let created = false

function record(browser, width, check, ok = true) {
  results.push({ browser, width, check, ok })
  console.log(`${ok ? "PASS" : "FAIL"} ${browser} ${width}px ${check}`)
  assert.ok(ok, check)
}

async function verificationLink() {
  for (let attempt = 0; attempt < 30; attempt++) {
    const response = await fetch(`${MAIL}/api/v1/messages`)
    const inbox = await response.json()
    const message = inbox.messages.find((item) => item.To.some((to) => to.Address === EMAIL))
    if (message) {
      const details = await (await fetch(`${MAIL}/api/v1/message/${message.ID}`)).json()
      return details.Text.match(/https?:\/\/[^\s]+\/account\/verify#token=[A-Za-z0-9_-]+/)[0]
    }
    await new Promise((resolve) => setTimeout(resolve, 200))
  }
  throw new Error("Verification message did not reach Mailpit")
}

async function login(page) {
  await page.goto(`${BASE}/account/login`)
  await page.getByLabel("E-mail", { exact: true }).fill(EMAIL)
  await page.getByLabel("Password", { exact: true }).fill(PASSWORD)
  await page.getByRole("button", { name: "Log in", exact: true }).click()
  await page.waitForURL(/\/account$/)
  await page.getByRole("heading", { name: "My account", exact: true }).waitFor()
}

async function run(type, name, width) {
  const browser = await type.launch()
  const context = await browser.newContext({
    viewport: { width, height: 850 },
    locale: "en-US",
    acceptDownloads: true,
  })
  const page = await context.newPage()
  const pageErrors = []
  page.on("pageerror", (error) => pageErrors.push(error.message))
  try {
    await page.goto(`${BASE}/account`)
    await page.waitForURL(/\/account\/login/)
    record(name, width, "US23 anonymous account page redirects to login")
    if (!created) {
      await page.getByRole("link", { name: "Create account", exact: true }).click()
      await page.getByLabel("E-mail", { exact: true }).fill(EMAIL)
      await page.getByLabel("Password", { exact: true }).fill(PASSWORD)
      await page.getByRole("button", { name: "Create account", exact: true }).click()
      await page.getByRole("status").filter({ hasText: "Check your e-mail" }).waitFor()
      record(name, width, "US23 registration sends a real SMTP verification message")
      const link = await verificationLink()
      await page.goto(link)
      await page.getByRole("button", { name: "Verify e-mail", exact: true }).click()
      await page.waitForURL(/\/account$/)
      created = true
      record(name, width, "US23 verification opens the account")
    } else {
      await login(page)
      record(name, width, "US23 verified account logs in")
    }
    const cookie = (await context.cookies()).find((item) => item.name === "applicant_session")
    record(
      name,
      width,
      "US23 isolated HttpOnly Secure session",
      Boolean(
        cookie?.httpOnly && cookie.secure && cookie.path === "/api/applicant" && cookie.sameSite === "Strict",
      ),
    )

    await page.goto(`${BASE}/programs/6B06102`)
    await page.getByRole("button", { name: "Save checklist", exact: true }).click()
    await page.waitForURL(/\/account$/)
    const local = page.locator("article").filter({ hasText: "6B06102 · Local" })
    await local.waitFor()
    record(name, width, "US24 save local checklist from program page")
    const first = local.getByRole("checkbox").first()
    await Promise.all([
      page.waitForResponse(
        (response) =>
          response.url().includes("/documents/") && response.request().method() === "PUT" && response.ok(),
      ),
      first.check(),
    ])
    await page.waitForFunction(
      () => document.querySelector('article input[type="checkbox"]')?.checked === true,
    )
    await page.reload()
    await local.getByRole("checkbox").first().waitFor()
    record(
      name,
      width,
      "US25 prepared document survives reload",
      await local.getByRole("checkbox").first().isChecked(),
    )
    const downloadPromise = page.waitForEvent("download")
    await local.getByRole("button", { name: "Download PDF", exact: true }).click()
    const download = await downloadPromise
    record(
      name,
      width,
      "US26 personal PDF downloads",
      (await download.failure()) === null && download.suggestedFilename().endsWith(".pdf"),
    )

    await page.goto(`${BASE}/programs/6B06102?applicant=international`)
    await page.getByRole("button", { name: "Save checklist", exact: true }).click()
    await page.waitForURL(/\/account$/)
    const international = page.locator("article").filter({ hasText: "6B06102 · International" })
    await international.waitFor()
    record(name, width, "US24 applicant types are separate", (await page.locator("article").count()) === 2)
    record(
      name,
      width,
      "US25 international progress starts unchecked",
      !(await international.getByRole("checkbox").first().isChecked()),
    )

    await page.getByLabel("E-mail me deadline reminders", { exact: true }).check()
    await page.getByLabel("E-mail language", { exact: true }).selectOption("kk")
    await page.getByRole("button", { name: "Save preferences", exact: true }).click()
    await page.getByRole("status").filter({ hasText: "Preferences saved." }).waitFor()
    await page.reload()
    await page.getByLabel("E-mail me deadline reminders", { exact: true }).waitFor()
    record(
      name,
      width,
      "US7 opt-in and email language survive reload",
      (await page.getByLabel("E-mail me deadline reminders", { exact: true }).isChecked()) &&
        (await page.getByLabel("E-mail language", { exact: true }).inputValue()) === "kk",
    )
    await page.getByLabel("E-mail me deadline reminders", { exact: true }).uncheck()
    await page.getByRole("button", { name: "Save preferences", exact: true }).click()
    await page.getByRole("status").filter({ hasText: "Preferences saved." }).waitFor()
    record(name, width, "US7 reminders can be disabled")

    for (const [language, button, heading] of [
      ["kk", "Қазақша", "Менің аккаунтым"],
      ["ru", "Русский", "Мой аккаунт"],
      ["en", "English", "My account"],
    ]) {
      await page.getByRole("button", { name: button, exact: true }).click()
      await page.getByRole("heading", { name: heading, exact: true }).waitFor()
      const fits = await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)
      record(name, width, `US23–26 ${language} labels and responsive layout`, fits)
      await page.screenshot({ path: `${OUT}/applicant-${name}-${width}-${language}.png`, fullPage: true })
    }

    await Promise.all([
      page.waitForResponse(
        (response) =>
          response.url().includes("/documents/") && response.request().method() === "PUT" && response.ok(),
      ),
      local.getByRole("checkbox").first().uncheck(),
    ])
    await international.getByRole("button", { name: "Remove from saved", exact: true }).click()
    await international.waitFor({ state: "detached" })
    await local.getByRole("button", { name: "Remove from saved", exact: true }).click()
    await local.waitFor({ state: "detached" })
    await page.getByText("You have no saved programs yet.", { exact: true }).waitFor()
    record(name, width, "US24 removal leaves an empty saved list")
    // Put an account page in history; public program pages are valid destinations after logout.
    await page.goto(`${BASE}/account?history=qa`)
    await page.getByRole("heading", { name: "My account", exact: true }).waitFor()
    await page.getByRole("button", { name: "Log out", exact: true }).click()
    await page.waitForURL(/\/account\/login/)
    await page.goBack()
    await page.waitForURL(/\/account\/login/)
    record(
      name,
      width,
      "US23 browser back after logout exposes no account data",
      !(await page.getByText(EMAIL, { exact: true }).count()),
    )
    record(name, width, "US23 no frontend runtime errors", pageErrors.length === 0)
  } catch (error) {
    results.push({ browser: name, width, check: String(error), ok: false })
    console.error(error)
    await page
      .screenshot({ path: `${OUT}/applicant-${name}-${width}-error.png`, fullPage: true })
      .catch(() => {})
    throw error
  } finally {
    await browser.close()
  }
}

try {
  for (const [type, name] of [
    [chromium, "chromium"],
    [firefox, "firefox"],
  ]) {
    for (const width of (process.env.WIDTHS ?? "360,768,1280").split(",").map(Number))
      await run(type, name, width)
  }
} finally {
  // Never leave a QA applicant or its reminders behind, including on failure.
  const api = await request.newContext({ baseURL: BASE })
  try {
    const response = await api.post("/api/applicant/login", { data: { email: EMAIL, password: PASSWORD } })
    if (response.ok()) assert.equal((await api.delete("/api/applicant/me")).status(), 204)
  } finally {
    await api.dispose()
  }
}
const failed = results.filter((item) => !item.ok)
console.log(`\n${results.length - failed.length}/${results.length} applicant checks passed`)
process.exitCode = failed.length ? 1 : 0
