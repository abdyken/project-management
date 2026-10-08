import { chromium, firefox } from "playwright"
import fs from "node:fs"

const BASE = process.env.BASE_URL ?? "http://localhost:5173"
const OUT = process.env.OUT ?? "e2e/shots"
fs.mkdirSync(OUT, { recursive: true })

const ENGLISH_LABELS = [
  "Study programs",
  "All schools",
  "All degrees",
  "programs found",
  "Local deadline",
  "Required documents",
  "Application deadline",
  "Official program page",
  "Compare programs",
  "Not published",
  "Write a question",
  "Do not enter personal data",
  "Browse programs",
  "Ask a question",
  "People also ask",
]

const EXPECTED = {
  kk: { script: /[әғқңөұүһі]/i, switch: "Қазақша", programs: "Білім беру бағдарламалары", chat: "Жеке деректерді енгізбеңіз", compare: "Бағдарламаларды салыстыру" },
  ru: { script: /[а-яё]{4,}/i, switch: "Русский", programs: "Образовательные программы", chat: "Не вводите персональные данные", compare: "Сравнение программ" },
}

const results = []
function record(browser, width, language, check, ok, detail = "") {
  results.push({ browser, width, language, check, ok, detail })
  console.log(`${ok ? "PASS" : "FAIL"} ${browser} ${width}px ${language} ${check}${detail ? ` - ${detail}` : ""}`)
}

async function visibleText(page) {
  return page.evaluate(() => {
    const hidden = [...document.body.querySelectorAll('[lang="en"]')].filter((element) => element.closest("[aria-pressed]") === null)
    const saved = hidden.map((element) => [element, element.style.display])
    for (const element of hidden) element.style.display = "none"
    const text = document.body.innerText
    for (const [element, display] of saved) element.style.display = display
    return text
  })
}

function leftovers(text) {
  return ENGLISH_LABELS.filter((label) => text.includes(label))
}

async function run(browserType, name, width, language) {
  const browser = await browserType.launch()
  const context = await browser.newContext({ viewport: { width, height: 820 }, locale: "en-US" })
  const page = await context.newPage()
  const expected = EXPECTED[language]
  try {
    await page.goto(BASE)
    await page.getByRole("button", { name: expected.switch }).click()
    record(name, width, language, "html lang follows the switch", (await page.getAttribute("html", "lang")) === language)
    const home = await visibleText(page)
    record(name, width, language, "home has no English labels", leftovers(home).length === 0, leftovers(home).join(", "))

    await page.goto(`${BASE}/programs`)
    await page.getByText(expected.programs).waitFor()
    await page.locator("article").first().waitFor()
    const catalogue = await visibleText(page)
    record(name, width, language, "choice survives navigation and reload", catalogue.includes(expected.programs))
    record(name, width, language, "catalogue has no English labels", leftovers(catalogue).length === 0, leftovers(catalogue).join(", "))
    record(name, width, language, "catalogue no horizontal overflow", await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1))
    await page.screenshot({ path: `${OUT}/language-${name}-${width}-${language}-programs.png` })

    await page.goto(`${BASE}/programs/7M06101`)
    await page.locator("h1").waitFor()
    await page.waitForTimeout(800)
    const detail = await visibleText(page)
    record(name, width, language, "program page has no English labels", leftovers(detail).length === 0, leftovers(detail).join(", "))

    await page.goto(`${BASE}/compare?ids=6B06101,7M06101`)
    await page.getByText(expected.compare).first().waitFor()
    await page.waitForTimeout(800)
    const compare = await visibleText(page)
    record(name, width, language, "compare page has no English labels", leftovers(compare).length === 0, leftovers(compare).join(", "))
    record(name, width, language, "compare no horizontal overflow", await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1))

    await page.reload()
    await page.locator("[aria-pressed='true'][lang]").first().waitFor()
    const pressed = await page.locator("[aria-pressed='true'][lang]").getAttribute("lang")
    record(name, width, language, "switch remembered after reload", pressed === language)

    await page.locator("button[aria-haspopup], button").filter({ has: page.locator("svg.lucide-message-circle") }).first().click()
    await page.getByText(expected.chat).waitFor()
    const chat = await visibleText(page)
    record(name, width, language, "chat has no English labels", leftovers(chat).length === 0, leftovers(chat).join(", "))

    const chips = page.locator('[role="log"] > div button')
    await chips.first().waitFor({ timeout: 10000 })
    const chip = await chips.first().innerText()
    record(name, width, language, "starter questions in the chosen language", expected.script.test(chip), chip)
    await chips.first().click()
    await page.waitForFunction(() => {
      const articles = document.querySelectorAll('[role="log"] article')
      return articles.length >= 2 && Boolean(articles[articles.length - 1].querySelector("button[aria-pressed]"))
    }, null, { timeout: 25000 })
    const articles = page.locator('[role="log"] article')
    const reply = await articles.nth((await articles.count()) - 1).innerText()
    record(name, width, language, "starter answered in the chosen language", expected.script.test(reply), reply.slice(0, 80))
    await page.screenshot({ path: `${OUT}/language-${name}-${width}-${language}-chat.png` })
  } catch (error) {
    record(name, width, language, "run", false, String(error).split("\n")[0])
    await page.screenshot({ path: `${OUT}/language-${name}-${width}-${language}-error.png` }).catch(() => {})
  } finally {
    await browser.close()
  }
}

for (const [type, name] of [
  [chromium, "chromium"],
  [firefox, "firefox"],
]) {
  for (const width of (process.env.WIDTHS ?? "360,768,1280").split(",").map(Number)) {
    for (const language of ["kk", "ru"]) await run(type, name, width, language)
  }
}

const failed = results.filter((r) => !r.ok)
console.log(`\n${results.length - failed.length}/${results.length} checks passed`)
process.exit(failed.length ? 1 : 0)
