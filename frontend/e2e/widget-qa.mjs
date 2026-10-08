import { chromium, firefox } from "playwright"
import fs from "node:fs"

const BASE = process.env.BASE_URL ?? "http://localhost:5173"
const OUT = process.env.OUT ?? "e2e/shots"
fs.mkdirSync(OUT, { recursive: true })

const results = []
function record(browser, width, check, ok, detail = "") {
  results.push({ browser, width, check, ok, detail })
  console.log(`${ok ? "PASS" : "FAIL"} ${browser} ${width}px ${check}${detail ? ` - ${detail}` : ""}`)
}

async function lastAssistantText(page) {
  const log = page.getByRole("log", { name: "Conversation" })
  const articles = log.locator("article")
  const count = await articles.count()
  return count ? (await articles.nth(count - 1).innerText()) : ""
}

async function messageCount(page) {
  return page.locator('[role="log"] article').count()
}

async function waitIdle(page, before) {
  await page.waitForFunction((before) => {
    const articles = document.querySelectorAll('[role="log"] article')
    if (articles.length < before + 2) return false
    const last = articles[articles.length - 1]
    const text = last.innerText
    return Boolean(last.querySelector('button[aria-label="Helpful"]')) || text.includes("This answer was interrupted.") || text.includes("Resend")
  }, before, { timeout: 25000 })
  await page.waitForTimeout(300)
}

async function ask(page, question) {
  const before = await messageCount(page)
  const input = page.getByRole("textbox", { name: "Your question" })
  await input.fill(question)
  await page.getByRole("button", { name: "Send" }).click()
  await waitIdle(page, before)
  return lastAssistantText(page)
}

async function noOverflow(page) {
  return page.evaluate(() => {
    const doc = document.documentElement.scrollWidth <= window.innerWidth + 1
    const log = document.querySelector('[role="log"]')
    const panel = log ? log.scrollWidth <= log.clientWidth + 1 : true
    return doc && panel
  })
}

async function run(browserType, name, width) {
  const browser = await browserType.launch()
  const context = await browser.newContext({ viewport: { width, height: width < 640 ? 760 : 820 } })
  const page = await context.newPage()
  try {
    await page.goto(BASE)
    await page.getByRole("button", { name: "Open admissions chat" }).click()
    const log = page.getByRole("log", { name: "Conversation" })
    await log.waitFor()

    const starters = log.locator("button")
    await starters.first().waitFor({ timeout: 10000 })
    record(name, width, "14.4 four starter questions", (await starters.count()) === 4, `${await starters.count()} chips`)
    record(name, width, "14.3 personal data note", await page.getByText("Do not enter personal data").isVisible())

    const starter = await starters.first().innerText()
    await starters.first().click()
    await waitIdle(page, 0)
    const sourceLinks = log.locator('article a[href^="https://sdu.edu.kz"]')
    record(name, width, "14.4 starter answered with a source", (await sourceLinks.count()) >= 1, starter)
    const followUps = log.locator(":scope > div button")
    const followUpCount = await followUps.count()
    record(name, width, "14.4 up to 3 follow-up chips", followUpCount > 0 && followUpCount <= 3, `${followUpCount} chips`)

    const local = await ask(page, "Which documents do I need for 6B06102 as a local applicant?")
    const checklistItems = await log.locator("article").last().locator("li").count()
    record(name, width, "14.3 checklist renders as a list", checklistItems > 3, `${checklistItems} items: ${local.slice(0, 80)}`)
    const international = await ask(page, "and as an international applicant?")
    record(
      name,
      width,
      "11.2 follow-up keeps the program",
      local.includes("local applicant") && international.includes("6B06102") && international.includes("international applicant"),
    )

    const compare = await ask(page, "Compare 6B06101 and 6B06102")
    record(name, width, "12 comparison side by side", compare.includes("Comparison of") && (await log.locator("article").last().locator("li").count()) >= 4, compare.slice(0, 100))

    await page.getByRole("button", { name: "Not helpful" }).last().click()
    await page.getByRole("button", { name: "Outdated" }).click()
    await page.waitForTimeout(500)
    const pressed = await page.getByRole("button", { name: "Not helpful" }).last().getAttribute("aria-pressed")
    const disabled = await page.getByRole("button", { name: "Helpful", exact: true }).last().isDisabled()
    record(name, width, "13.2 one rating with reason", pressed === "true" && disabled, `pressed=${pressed} disabled=${disabled} ${(await lastAssistantText(page)).slice(-120)}`)

    record(name, width, "layout no horizontal overflow", await noOverflow(page))
    await page.screenshot({ path: `${OUT}/${name}-${width}-chat.png` })

    await page.goto(`${BASE}/programs`)
    if (!(await page.getByRole("log", { name: "Conversation" }).isVisible().catch(() => false))) {
      await page.getByRole("button", { name: "Open admissions chat" }).click()
    }
    await page.getByRole("log", { name: "Conversation" }).waitFor()
    const kept = await page.getByRole("button", { name: "Not helpful" }).last().getAttribute("aria-pressed")
    record(name, width, "13.2 rating survives navigation", kept === "true")

    await page.getByRole("button", { name: "New conversation" }).click()
    await page.waitForTimeout(300)
    const cleared = (await page.getByRole("log", { name: "Conversation" }).locator("article").count()) === 0
    const after = await ask(page, "and for international?")
    record(name, width, "11.4 new conversation forgets the program", cleared && !after.includes("6B06102"))

    await page.route("**/api/assistant/ask/stream", async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 1500))
      await route.continue()
    })
    const input = page.getByRole("textbox", { name: "Your question" })
    await input.fill("Which documents do I need for 6B06101 as an international applicant?")
    await page.getByRole("button", { name: "Send" }).click()
    await page.waitForTimeout(300)
    if (width < 640) await page.keyboard.press("Escape")
    else await page.getByRole("button", { name: "Close chat" }).click()
    await page.waitForTimeout(2500)
    await page.unroute("**/api/assistant/ask/stream")
    await page.getByRole("button", { name: "Open admissions chat" }).click()
    await page.getByRole("log", { name: "Conversation" }).waitFor()
    const last = await lastAssistantText(page)
    const interrupted = last.includes("This answer was interrupted.")
    const complete = last.includes("Required documents for")
    record(name, width, "14.2 closing mid-answer leaves no broken message", interrupted || complete, interrupted ? "interrupted + resend" : "complete")
    if (interrupted) {
      const before = (await messageCount(page)) - 2
      await page.getByRole("button", { name: "Resend" }).click()
      await waitIdle(page, before)
      record(name, width, "14.2 resend completes the answer", (await lastAssistantText(page)).includes("Required documents for"))
    }
    await page.screenshot({ path: `${OUT}/${name}-${width}-resend.png` })
  } catch (error) {
    record(name, width, "run", false, String(error).split("\n")[0])
    await page.screenshot({ path: `${OUT}/${name}-${width}-error.png` }).catch(() => {})
  } finally {
    await browser.close()
  }
}

for (const [type, name] of [
  [chromium, "chromium"],
  [firefox, "firefox"],
]) {
  for (const width of (process.env.WIDTHS ?? "360,768,1280").split(",").map(Number)) await run(type, name, width)
}

const failed = results.filter((r) => !r.ok)
console.log(`\n${results.length - failed.length}/${results.length} checks passed`)
fs.writeFileSync(`${OUT}/results.json`, JSON.stringify(results, null, 1))
process.exit(failed.length ? 1 : 0)
