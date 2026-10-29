import assert from "node:assert/strict"
import fs from "node:fs"
import { execFileSync } from "node:child_process"
import { chromium, firefox, request } from "playwright"

// Run ONLY against a disposable local stack, with a QA staff account. Creates and
// deletes its own applicant; its synthetic programme is archived in finally.
const BASE = process.env.BASE_URL ?? "http://localhost:5173"
const MAIL = process.env.MAILPIT_URL ?? "http://localhost:8025"
const OUT = process.env.OUT ?? "e2e/shots"
const EMAIL = process.env.STAFF_EMAIL
const PASSWORD = process.env.STAFF_PASSWORD
const APPLICANT_EMAIL = `sprint6-${Date.now()}@example.test`
const APPLICANT_PASSWORD = "Sprint6-browser-local-only"
const applicantsCreated = new Set()
assert(
  EMAIL && PASSWORD,
  "Set STAFF_EMAIL and STAFF_PASSWORD for disposable QA",
)
fs.mkdirSync(OUT, { recursive: true })
const results = []
const record = (browser, width, check) => {
  results.push({ browser, width, check, ok: true })
  console.log(`PASS ${browser} ${width}px ${check}`)
}

async function verification(email) {
  for (let i = 0; i < 40; i++) {
    const inbox = await (await fetch(`${MAIL}/api/v1/messages`)).json()
    const message = inbox.messages.find((m) =>
      m.To.some((to) => to.Address === email),
    )
    if (message) {
      const detail = await (
        await fetch(`${MAIL}/api/v1/message/${message.ID}`)
      ).json()
      return detail.Text.match(/#token=([A-Za-z0-9_-]+)/)[1]
    }
    await new Promise((resolve) => setTimeout(resolve, 200))
  }
  throw new Error("No verification message")
}

async function run(type, name, width) {
  const browser = await type.launch()
  const context = await browser.newContext({
    viewport: { width, height: 900 },
    locale: "en-US",
  })
  const page = await context.newPage()
  const errors = []
  page.on("pageerror", (e) => errors.push(e.message))
  const email = `${name}-${APPLICANT_EMAIL}`
  const program = `QA6${Date.now()}`
  let synthetic = null
  const post = (path, data) => context.request.post(`${BASE}${path}`, { data })
  try {
    await page.goto(`${BASE}/admissions`)
    await page
      .getByRole("heading", { name: "Plan your admission", exact: true })
      .waitFor()
    assert(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth + 1,
      ),
    )
    record(name, width, "Guidance hub fits the viewport")

    await page.goto(`${BASE}/eligibility?program=6B06102`)
    await page.getByLabel("UNT total (0–140)", { exact: true }).fill("49")
    await page.getByRole("button", { name: "Check", exact: true }).click()
    await page
      .getByRole("heading", {
        name: "A checked requirement is not met",
        exact: true,
      })
      .waitFor()
    await page.getByLabel("UNT total (0–140)", { exact: true }).fill("50")
    await page
      .getByLabel("Accepted SDU English exam / B1 certificate")
      .selectOption("true")
    await page.getByRole("button", { name: "Check", exact: true }).click()
    await page
      .getByRole("heading", { name: "More information is needed", exact: true })
      .waitFor()
    record(
      name,
      width,
      "US27 threshold boundary and incomplete coverage are distinct",
    )
    await page.screenshot({
      path: `${OUT}/guidance-eligibility-${name}-${width}.png`,
      fullPage: true,
    })

    await page.goto(`${BASE}/cost-calculator?program=6B06102`)
    await page.getByLabel("Professional courses · ECTS credits").fill("20")
    await page
      .getByLabel("Multidisciplinary courses (MDE) · ECTS credits")
      .fill("10")
    await page.getByRole("button", { name: "Calculate", exact: true }).click()
    await page
      .getByRole("heading", {
        name: "Estimated amount: 850,000 KZT",
        exact: true,
      })
      .waitFor()
    record(
      name,
      width,
      "US28 professional and MDE rates match hand calculation",
    )
    await page.screenshot({
      path: `${OUT}/guidance-cost-${name}-${width}.png`,
      fullPage: true,
    })

    await page.goto(`${BASE}/recommendations`)
    await page.getByLabel("Computing and technology", { exact: true }).check()
    await page
      .getByRole("button", { name: "Find my programmes", exact: true })
      .click()
    await page.locator("article").first().waitFor()
    assert((await page.locator("article").count()) <= 3)
    await page
      .getByRole("link", { name: "Compare these programmes", exact: true })
      .click()
    await page.waitForURL(/\/compare\?ids=/)
    record(name, width, "US5 recommendations link to the existing comparison")

    await page.goto(`${BASE}/funding`)
    await page.locator("article").first().waitFor()
    assert(
      (await page
        .getByRole("link", { name: "Official source", exact: true })
        .count()) > 0,
    )
    record(name, width, "US29 funding items expose official sources")

    for (const [lang, heading, switchName] of [
      ["ru", "Гранты и скидки", "Русский"],
      ["kk", "Гранттар мен жеңілдіктер", "Қазақша"],
    ]) {
      await page.getByRole("button", { name: switchName, exact: true }).click()
      await page.getByRole("heading", { name: heading, exact: true }).waitFor()
      const localized =
        lang === "ru"
          ? [
              ["/eligibility", "Проверка требований"],
              ["/recommendations", "Подобрать программы"],
              ["/cost-calculator", "Калькулятор стоимости"],
              ["/account/requests", "Обращения в приёмную комиссию"],
            ]
          : [
              ["/eligibility", "Талаптарды тексеру"],
              ["/recommendations", "Бағдарламаларды таңдау"],
              ["/cost-calculator", "Оқу ақысын есептеу"],
              ["/account/requests", "Қабылдау комиссиясына сұрақтар"],
            ]
      for (const [path, title] of localized) {
        await page.goto(`${BASE}${path}`)
        await page.getByRole("heading", { name: title, exact: true }).waitFor()
        assert(
          await page.evaluate(
            () => document.documentElement.scrollWidth <= innerWidth + 1,
          ),
        )
      }
      await page.goto(`${BASE}/funding`)
      assert(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth + 1,
        ),
      )
      record(name, width, `Public guidance labels and layout in ${lang}`)
    }
    await page.getByRole("button", { name: "English", exact: true }).click()

    if (!applicantsCreated.has(email)) {
      assert.equal(
        (
          await post("/api/applicant/register", {
            email,
            password: APPLICANT_PASSWORD,
            language: "en",
          })
        ).status(),
        202,
      )
      applicantsCreated.add(email)
      assert.equal(
        (
          await post("/api/applicant/verify", {
            token: await verification(email),
          })
        ).status(),
        200,
      )
    } else {
      assert.equal(
        (
          await post("/api/applicant/login", {
            email,
            password: APPLICANT_PASSWORD,
          })
        ).status(),
        200,
      )
    }
    await page.goto(`${BASE}/account/requests`)
    await page
      .getByLabel("Your question", { exact: true })
      .fill(`QA question ${name} ${width}`)
    const creation = page.waitForResponse(
      (r) =>
        r.url().endsWith("/api/applicant/requests") &&
        r.request().method() === "POST",
    )
    await page
      .getByRole("button", { name: "Send to admissions", exact: true })
      .click()
    assert.equal((await creation).status(), 201)
    await page
      .locator("article")
      .filter({ hasText: `QA question ${name} ${width}` })
      .waitFor()
    record(
      name,
      width,
      "US30 verified applicant submits and sees a private question",
    )

    assert.equal(
      (
        await post("/api/staff/login", { email: EMAIL, password: PASSWORD })
      ).status(),
      200,
    )
    await page.goto(`${BASE}/staff/requests`)
    const card = page
      .locator("article")
      .filter({ hasText: `QA question ${name} ${width}` })
    await card
      .getByLabel("Answer", { exact: true })
      .fill("QA answer from the admissions office")
    await card
      .getByRole("button", { name: "Send to admissions", exact: true })
      .click()
    await card.waitFor({ state: "detached" })
    await page.goto(`${BASE}/account/requests`)
    await page
      .locator("article")
      .filter({ hasText: `QA question ${name} ${width}` })
      .getByText("QA answer from the admissions office", { exact: true })
      .waitFor()
    record(
      name,
      width,
      "US30 staff answer appears in the correct applicant account",
    )
    if (process.env.QA_RUN_NOTIFICATIONS === "true") {
      assert(
        process.env.DATABASE_URL && process.env.SMTP_HOST,
        "Notification QA requires the disposable DATABASE_URL and SMTP_HOST",
      )
      execFileSync(
        process.env.QA_PYTHON ?? "../backend/.venv/bin/python",
        ["../backend/scripts/send_request_notifications.py"],
        { env: process.env },
      )
      const mail = await (await fetch(`${MAIL}/api/v1/messages`)).json()
      assert(
        mail.messages.some(
          (m) =>
            m.To.some((to) => to.Address === email) &&
            m.Subject.includes("answered"),
        ),
      )
      record(name, width, "US30 notification reaches real local SMTP")
    }

    synthetic = {
      program_id: program,
      title: "QA synthetic programme",
      title_ru: null,
      title_kk: null,
      faculty: "QA",
      degree_level: "bachelor",
      language: "English",
      tuition_per_ects_kzt: 1000,
      tuition_per_ects_usd: 10,
      deadline_local: null,
      deadline_international: null,
      source_url: "https://sdu.edu.kz/",
      is_active: true,
    }
    assert.equal((await post("/api/staff/programs", synthetic)).status(), 201)
    await page.goto(`${BASE}/staff/programs/${program}`)
    await page
      .getByRole("heading", {
        name: "Admission rules and tariffs",
        exact: true,
      })
      .waitFor()
    const guidanceForm = page.locator("form").filter({
      has: page.getByRole("heading", {
        name: "Admission rules and tariffs",
        exact: true,
      }),
    })
    await guidanceForm
      .getByLabel("Published programme ECTS", { exact: true })
      .fill("240")
    // Fill the source opened by the deliberate credit-count change.
    await guidanceForm
      .locator("fieldset")
      .filter({
        has: page.locator("legend", { hasText: "Published programme ECTS" }),
      })
      .locator("summary")
      .click()
    await guidanceForm
      .getByLabel("Supporting quote", { exact: true })
      .fill("Synthetic QA fixture only: 240 credits")
    await guidanceForm
      .getByRole("button", { name: "Save", exact: true })
      .click()
    await guidanceForm.getByRole("status").waitFor()
    await page.reload()
    assert.equal(
      await page
        .getByLabel("Published programme ECTS", { exact: true })
        .inputValue(),
      "240",
    )
    record(
      name,
      width,
      "Staff guidance form saves and reloads a synthetic programme",
    )
    await page.screenshot({
      path: `${OUT}/guidance-staff-${name}-${width}.png`,
      fullPage: true,
    })
    assert.deepEqual(errors, [])
    record(name, width, "No browser runtime errors")
  } catch (error) {
    results.push({ browser: name, width, check: String(error), ok: false })
    await page
      .screenshot({
        path: `${OUT}/guidance-error-${name}-${width}.png`,
        fullPage: true,
      })
      .catch(() => {})
    throw error
  } finally {
    if (synthetic)
      await context.request.put(`${BASE}/api/staff/programs/${program}`, {
        data: { ...synthetic, is_active: false },
      })
    await context.close()
    await browser.close()
  }
}

try {
  for (const [type, name] of [
    [chromium, "chromium"],
    [firefox, "firefox"],
  ])
    for (const width of [360, 768, 1280]) await run(type, name, width)
} finally {
  for (const email of applicantsCreated) {
    const api = await request.newContext({ baseURL: BASE })
    await api.post("/api/applicant/login", {
      data: { email, password: APPLICANT_PASSWORD },
    })
    await api.delete("/api/applicant/me")
    await api.dispose()
  }
  fs.writeFileSync(
    `${OUT}/guidance-results.json`,
    JSON.stringify(results, null, 2),
  )
}
console.log(
  `${results.length}/${results.length} guidance browser checks passed`,
)
