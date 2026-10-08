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

async function run(browserType, name, width) {
  const browser = await browserType.launch()
  const page = await browser.newPage({ viewport: { width, height: 820 } })
  try {
    await page.goto(`${BASE}/programs`)
    const compare = page.getByRole("button", { name: /to comparison$/ })
    await compare.first().waitFor()
    for (const title of ["Information Systems", "Computer Science", "Management"]) {
      await page.getByRole("button", { name: `Add ${title} to comparison` }).first().click()
    }
    const disabled = await page.getByRole("button", { name: "Add Applied Law to comparison" }).isDisabled()
    record(name, width, "17.2 a fourth program cannot be added", disabled)

    const bar = page.getByRole("region", { name: "Program comparison" })
    record(name, width, "17.2 compare bar shows 3/3", (await bar.innerText()).includes("3/3"))
    await bar.getByRole("link", { name: "Compare" }).click()
    await page.waitForURL(/\/compare\?ids=/)
    await page.locator('text="Tuition, local" >> visible=true').first().waitFor()

    const wide = width >= 640
    if (wide) {
      const columns = await page.locator("table thead th").count()
      record(name, width, "17.2 three programs side by side", columns === 4, `${columns - 1} columns`)
    } else {
      const sections = await page.locator("section[aria-label]").count()
      record(name, width, "17.2 stacked by field on phones", sections === 9, `${sections} fields`)
    }
    const text = await page.locator("main").innerText()
    record(name, width, "17.2 empty values say Not published", text.includes("Not published"))
    record(name, width, "17.2 fee from the catalogue", text.includes("33,000 KZT per ECTS credit"))
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1)
    record(name, width, "layout no horizontal overflow", overflow)
    await page.screenshot({ path: `${OUT}/compare-${name}-${width}.png`, fullPage: true })

    await page.reload()
    await page.locator('text="Tuition, local" >> visible=true').first().waitFor()
    await page.locator('button[aria-label="Remove Management from comparison"] >> visible=true').click()
    await page.waitForURL((url) => !url.search.includes("7M04115"))
    const afterRemove = await page.locator("main").innerText()
    record(name, width, "17.2 remove keeps the other two", !afterRemove.includes("Management") && afterRemove.includes("Computer Science"))

    await page.locator('button[aria-label="Remove Computer Science from comparison"] >> visible=true').click()
    await page.getByText("Pick two or three programs").waitFor()
    record(name, width, "17.2 empty state below two programs", true)

    await page.goto(`${BASE}/compare?ids=6B06101,0X00000`)
    await page.getByText("Program not found").waitFor()
    record(name, width, "17.2 unknown program in a link", true)
  } catch (error) {
    record(name, width, "run", false, String(error).split("\n")[0])
    await page.screenshot({ path: `${OUT}/compare-${name}-${width}-error.png` }).catch(() => {})
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
process.exit(failed.length ? 1 : 0)
