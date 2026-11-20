import { useQuery } from "@tanstack/react-query"
import { ArrowRight, Search } from "lucide-react"
import { useMemo, useState, type FormEvent } from "react"
import { Link, useNavigate } from "react-router-dom"
import { allProgramsQuery, programLanguages } from "@/api/programs"
import type { DegreeLevel, Program } from "@/api/types"
import { HeroGlobe } from "@/components/home/HeroGlobe"
import { MosaicTile } from "@/components/mosaic/MosaicTile"
import { mosaicRow, type Tile } from "@/components/mosaic/pattern"
import { Tesserae } from "@/components/mosaic/Tesserae"
import { Button } from "@/components/ui/button"
import { useGuidanceT } from "@/guidance/i18n"
import { useI18n, type Language } from "@/i18n"
import { cn } from "@/lib/utils"
import { useChatStore } from "@/store/chat"

const QUESTIONS = ["home.q1", "home.q2", "home.q3", "home.q4", "home.q5"] as const
const LEVELS: DegreeLevel[] = ["bachelor", "master", "phd"]
const NUMBER_LOCALE: Record<Language, string> = { en: "en-GB", ru: "ru-RU", kk: "ru-RU" }
const KK_MONTHS_SHORT = ["қаң", "ақп", "нау", "сәу", "мам", "мау", "шіл", "там", "қыр", "қаз", "қар", "жел"]

// The hero band's stepped edge rising into the photo: sparse on top, dense where it meets the field.
const HERO_EDGE: Tile[][] = [
  mosaicRow(1996, 70, 0.12, ["field", "glacier", "ochre"]),
  mosaicRow(64, 70, 0.4, ["field", "glacier", "ochre", "terracotta", "field"]),
  mosaicRow(2026, 70, 0.85, ["field", "field", "glacier", "deep", "ochre"]),
]

type Facts = {
  total: number
  schools: { name: string; count: number }[]
  byLevel: Record<DegreeLevel, { count: number; deadlineLocal: string | null; deadlineIntl: string | null; min: number | null; max: number | null }>
  english: number
}

function mode(values: (string | null)[]): string | null {
  const counts = new Map<string, number>()
  for (const value of values) if (value) counts.set(value, (counts.get(value) ?? 0) + 1)
  let best: string | null = null
  for (const [value, count] of counts) if (best === null || count > (counts.get(best) ?? 0)) best = value
  return best
}

function summarise(programs: Program[]): Facts {
  const schools = new Map<string, number>()
  for (const program of programs) schools.set(program.faculty, (schools.get(program.faculty) ?? 0) + 1)
  const byLevel = Object.fromEntries(
    LEVELS.map((level) => {
      const items = programs.filter((program) => program.degree_level === level)
      const fees = items.map((program) => program.tuition_per_ects_kzt).filter((fee): fee is number => fee !== null)
      return [
        level,
        {
          count: items.length,
          deadlineLocal: mode(items.map((program) => program.deadline_local)),
          deadlineIntl: mode(items.map((program) => program.deadline_international)),
          min: fees.length ? Math.min(...fees) : null,
          max: fees.length ? Math.max(...fees) : null,
        },
      ]
    }),
  ) as Facts["byLevel"]
  return {
    total: programs.length,
    schools: [...schools].map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count),
    byLevel,
    english: programs.filter((program) => programLanguages(program).includes("English")).length,
  }
}

export function HomePage() {
  const { t, language, degree } = useI18n()
  const guidanceT = useGuidanceT()
  const navigate = useNavigate()
  const setOpen = useChatStore((state) => state.setOpen)
  const setDraft = useChatStore((state) => state.setDraft)
  const programs = useQuery(allProgramsQuery)
  const facts = useMemo(() => (programs.data ? summarise(programs.data.programs) : null), [programs.data])
  const numbers = useMemo(() => new Intl.NumberFormat(NUMBER_LOCALE[language]), [language])
  const [query, setQuery] = useState("")

  function search(event: FormEvent) {
    event.preventDefault()
    const q = query.trim()
    navigate(q ? `/programs?q=${encodeURIComponent(q)}` : "/programs")
  }

  function ask(question: string) {
    setDraft(question)
    setOpen(true)
  }

  return (
    <div>
      {/* First viewport: the campus inside a mosaic frame, with a working search. */}
      <section aria-labelledby="home-title" className="relative bg-field">
        <picture>
          <img
            src="/images/sdu/campus-autumn-1920.webp"
            srcSet="/images/sdu/campus-autumn-640.webp 640w, /images/sdu/campus-autumn-1280.webp 1280w, /images/sdu/campus-autumn-1920.webp 1920w, /images/sdu/campus-autumn-2560.webp 2560w"
            sizes="100vw"
            alt={t("home.photoAlt")}
            width={2560}
            height={1440}
            fetchPriority="high"
            className="block h-[38svh] min-h-64 w-full object-cover object-[50%_40%] sm:h-[48svh] lg:h-[54svh] lg:max-h-[640px]"
          />
        </picture>
        <div className="on-field relative bg-field">
          <div className="absolute inset-x-0 bottom-full overflow-hidden" style={{ height: 96 }}>
            <Tesserae size={32} rows={HERO_EDGE} className="absolute bottom-0 left-0" />
          </div>
          <div className="mx-auto grid max-w-[84rem] gap-10 px-4 pt-8 pb-14 sm:px-6 grid-cols-1 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)] lg:items-start lg:gap-16 lg:px-8 lg:pt-10 lg:pb-20">
            <div>
              <h1
                id="home-title"
                className="max-w-[12ch] text-[clamp(3.25rem,8.2vw,6rem)] leading-[0.86] font-extrabold tracking-[-0.01em] uppercase"
              >
                {t("home.title")}
              </h1>
              <p className="tabular mt-6 min-h-7 text-lg text-field-muted sm:text-xl">
                {facts ? t("home.tally", { programs: numbers.format(facts.total), schools: numbers.format(facts.schools.length) }) : ""}
              </p>
            </div>

            <form
              role="search"
              onSubmit={search}
              className="relative mr-14 bg-card p-5 text-card-foreground sm:mr-0 sm:p-7 lg:-mt-36 lg:p-8"
            >
              <Tesserae
                size={16}
                className="absolute -top-4 right-0"
                rows={[[null, "ochre", "glacier"]]}
              />
              <label htmlFor="home-search" className="block font-display text-3xl font-extrabold uppercase sm:text-4xl">
                {t("home.search.label")}
              </label>
              <div className="relative mt-5">
                <Search className="pointer-events-none absolute top-1/2 left-4 size-5 -translate-y-1/2 text-primary" aria-hidden="true" />
                <input
                  id="home-search"
                  type="search"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder={t("home.search.placeholder")}
                  autoComplete="off"
                  className="h-14 w-full border-2 border-ink bg-card pr-4 pl-12 text-base outline-none placeholder:text-muted-foreground focus-visible:border-primary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
                />
              </div>
              <Button type="submit" variant="ochre" size="lg" className="mt-4 h-14 w-full justify-between">
                {facts ? t("home.search.submit", { count: numbers.format(facts.total) }) : t("filters.searchButton")}
                <ArrowRight className="size-5" aria-hidden="true" />
              </Button>
              <button
                type="button"
                onClick={() => setOpen(true)}
                className="mt-4 text-[0.9375rem] font-medium text-primary underline decoration-2 underline-offset-4 hover:decoration-ochre"
              >
                {t("home.askQuestion")}
              </button>
            </form>
          </div>
        </div>
      </section>

      {/* Paths by applicant type: a mosaic of unequal tiles, not a row of equal cards. */}
      <section aria-labelledby="paths-title" className="mx-auto max-w-[84rem] px-4 py-20 sm:px-6 lg:px-8 lg:py-28">
        <SectionHeading id="paths-title" title={t("home.paths.title")} lead={t("home.paths.lead")} />
        <div className="mt-10 grid gap-2 sm:grid-cols-2 lg:grid-cols-12 lg:grid-rows-[auto_auto]">
          <MosaicTile
            to="/programs?degree_level=bachelor"
            tone="field"
            title={t("home.path.bachelor.title")}
            text={t("home.path.bachelor.text")}
            fact={facts ? t("home.path.count", { count: numbers.format(facts.byLevel.bachelor.count) }) : null}
            className="sm:col-span-2 lg:col-span-6 lg:row-span-2 lg:min-h-[26rem]"
            large
          />
          <MosaicTile
            to="/programs?degree_level=master"
            tone="glacier"
            title={t("home.path.master.title")}
            text={t("home.path.master.text")}
            fact={facts ? t("home.path.count", { count: numbers.format(facts.byLevel.master.count) }) : null}
            className="lg:col-span-3"
          />
          <MosaicTile
            to="/programs?degree_level=phd"
            tone="ochre"
            title={t("home.path.phd.title")}
            text={t("home.path.phd.text")}
            fact={facts ? t("home.path.count", { count: numbers.format(facts.byLevel.phd.count) }) : null}
            className="lg:col-span-3"
          />
          <MosaicTile
            to="/eligibility"
            tone="terracotta"
            title={t("home.path.intl.title")}
            text={t("home.path.intl.text")}
            fact={guidanceT("eligibility")}
            className="sm:col-span-2 lg:col-span-6"
          />
        </div>
      </section>

      {/* Key dates as a board: published dates are solid tiles, unpublished ones outline tiles. */}
      <section aria-labelledby="dates-title" className="border-y-2 border-ink bg-card">
        <div className="mx-auto grid max-w-[84rem] gap-10 px-4 py-20 sm:px-6 grid-cols-1 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.6fr)] lg:gap-16 lg:px-8 lg:py-24">
          <div>
            <SectionHeading id="dates-title" title={t("home.dates.title")} />
            {facts ? (
              <p className="tabular mt-5 font-display text-2xl font-bold uppercase">
                {(() => {
                  const dates = [facts.byLevel.bachelor.deadlineLocal, facts.byLevel.bachelor.deadlineIntl, facts.byLevel.master.deadlineLocal, facts.byLevel.phd.deadlineLocal]
                  const published = dates.filter(Boolean).length
                  return t("home.dates.tally", { published: numbers.format(published), pending: numbers.format(dates.length - published) })
                })()}
              </p>
            ) : null}
            <p className="mt-4 max-w-[46ch] text-muted-foreground">{t("home.dates.note")}</p>
          </div>
          <ol className="divide-y divide-border border-y border-border">
            <DateRow date={facts?.byLevel.bachelor.deadlineLocal} language={language} label={t("home.dates.bachelorLocal")} notPublished={t("home.dates.notPublished")} />
            <DateRow date={facts?.byLevel.bachelor.deadlineIntl} language={language} label={t("home.dates.bachelorIntl")} notPublished={t("home.dates.notPublished")} />
            <DateRow date={facts?.byLevel.master.deadlineLocal} language={language} label={t("home.dates.master")} notPublished={t("home.dates.notPublished")} />
            <DateRow date={facts?.byLevel.phd.deadlineLocal} language={language} label={t("home.dates.phd")} notPublished={t("home.dates.notPublished")} />
          </ol>
        </div>
      </section>

      {/* Cost as a ledger on the deep field. */}
      <section aria-labelledby="cost-title" className="on-field bg-field-deep">
        <div className="mx-auto grid max-w-[84rem] gap-10 px-4 py-20 sm:px-6 grid-cols-1 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.6fr)] lg:gap-16 lg:px-8 lg:py-24">
          <div>
            <SectionHeading id="cost-title" title={t("home.cost.title")} onField />
            <p className="mt-5 max-w-[46ch] text-field-muted">{t("home.cost.lead")}</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Button asChild variant="ochre" size="lg">
                <Link to="/cost-calculator">
                  {guidanceT("cost")}
                  <ArrowRight aria-hidden="true" />
                </Link>
              </Button>
              <Button asChild variant="onField" size="lg">
                <Link to="/funding">{guidanceT("funding")}</Link>
              </Button>
            </div>
          </div>
          <dl className="divide-y divide-field-foreground/20 border-y border-field-foreground/20">
            {LEVELS.map((level) => {
              const row = facts?.byLevel[level]
              const range =
                row && row.min !== null && row.max !== null
                  ? row.min === row.max
                    ? `${numbers.format(row.min)} ₸`
                    : `${numbers.format(row.min)}–${numbers.format(row.max)} ₸`
                  : null
              return (
                <div key={level} className="grid gap-1 py-6 sm:grid-cols-[10rem_1fr] sm:items-baseline sm:gap-6">
                  <dt className="font-display text-2xl font-bold uppercase">{degree(level)}</dt>
                  <dd>
                    <span className="tabular block font-display text-[clamp(2.25rem,5vw,3.5rem)] leading-none font-extrabold">
                      {range ?? (facts ? t("home.dates.notPublished") : "…")}
                    </span>
                    <span className="mt-1 block text-field-muted">{t("home.cost.perCredit")}</span>
                  </dd>
                </div>
              )
            })}
          </dl>
        </div>
      </section>

      {/* Schools beside a real photo of SDU students. */}
      <section aria-labelledby="schools-title" className="mx-auto grid max-w-[84rem] gap-10 px-4 py-20 sm:px-6 lg:grid-cols-12 lg:gap-12 lg:px-8 lg:py-28">
        <figure className="relative self-start lg:col-span-5">
          <img
            src="/images/sdu/students-laptop-1280.webp"
            srcSet="/images/sdu/students-laptop-640.webp 640w, /images/sdu/students-laptop-1280.webp 1280w, /images/sdu/students-laptop-1920.webp 1920w"
            sizes="(min-width: 1024px) 40vw, 100vw"
            alt=""
            width={1920}
            height={1280}
            loading="lazy"
            className="aspect-[4/3] w-full object-cover"
          />
          <Tesserae size={24} className="absolute -right-3 -bottom-3" rows={[[null, "glacier"], ["ochre", "field"]]} />
        </figure>
        <div className="lg:col-span-7">
          <SectionHeading id="schools-title" title={t("home.schools.title")} />
          <ul className="mt-8 border-t-2 border-ink">
            {(facts?.schools ?? []).map((school) => (
              <li key={school.name} className="border-b border-border">
                <Link
                  to={`/programs?faculty=${encodeURIComponent(school.name)}`}
                  className="group flex items-center justify-between gap-6 py-5 transition-colors hover:bg-secondary/60 sm:px-2"
                >
                  <span className="text-lg font-semibold sm:text-xl" lang="en">
                    {school.name}
                  </span>
                  <span className="tabular flex shrink-0 items-center gap-3 font-display text-2xl font-bold text-primary">
                    {numbers.format(school.count)}
                    <ArrowRight className="size-5 transition-transform duration-200 group-hover:translate-x-[3px]" aria-hidden="true" />
                  </span>
                </Link>
              </li>
            ))}
          </ul>
          <Button asChild variant="link" className="mt-6 text-base">
            <Link to="/programs">{t("home.browse")}</Link>
          </Button>
        </div>
      </section>

      {/* International applicants, with Daniyar's globe. */}
      <section aria-labelledby="intl-title" className="on-field overflow-hidden bg-field">
        <div className="mx-auto grid max-w-[84rem] grid-cols-1 items-center gap-10 px-4 py-20 sm:px-6 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)] lg:px-8 lg:py-24">
          <div>
            <SectionHeading id="intl-title" title={t("home.intl.title")} onField />
            <p className="mt-5 max-w-[52ch] text-lg text-field-muted">
              {t("home.intl.text", { count: facts ? numbers.format(facts.english) : "…" })}
            </p>
            <Button asChild variant="ochre" size="lg" className="mt-8">
              <Link to="/programs?language=English">
                {t("home.intl.cta")}
                <ArrowRight aria-hidden="true" />
              </Link>
            </Button>
          </div>
          <HeroGlobe />
        </div>
      </section>

      {/* Ask the office: the usual questions open the chat with the question filled in. */}
      <section aria-labelledby="ask-title" className="mx-auto grid max-w-[84rem] gap-10 px-4 py-20 sm:px-6 grid-cols-1 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.6fr)] lg:gap-16 lg:px-8 lg:py-28">
        <div>
          <SectionHeading id="ask-title" title={t("home.ask.title")} />
          <p className="mt-5 max-w-[46ch] text-muted-foreground">{t("home.ask.lead")}</p>
          <Button className="mt-8" size="lg" onClick={() => setOpen(true)}>
            {t("home.askQuestion")}
          </Button>
        </div>
        <ul className="border-t-2 border-ink">
          {QUESTIONS.map((key) => (
            <li key={key} className="border-b border-border">
              <button
                type="button"
                onClick={() => ask(t(key))}
                className="group flex w-full items-center justify-between gap-6 py-5 text-left text-lg transition-colors hover:bg-secondary/60 sm:px-2"
              >
                {t(key)}
                <ArrowRight className="size-5 shrink-0 text-primary transition-transform duration-200 group-hover:translate-x-[3px]" aria-hidden="true" />
              </button>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}

function SectionHeading({ id, title, lead, onField }: { id: string; title: string; lead?: string; onField?: boolean }) {
  return (
    <div>
      <h2 id={id} className="max-w-[16ch] text-[clamp(2.5rem,5.5vw,4.25rem)] leading-[0.9] font-extrabold uppercase">
        {title}
      </h2>
      {lead ? <p className={cn("mt-5 max-w-[52ch] text-lg", onField ? "text-field-muted" : "text-muted-foreground")}>{lead}</p> : null}
    </div>
  )
}

function DateRow({ date, label, language, notPublished }: { date: string | null | undefined; label: string; language: Language; notPublished: string }) {
  const parsed = date ? /^(\d{4})-(\d{2})-(\d{2})/.exec(date) : null
  const value = parsed ? new Date(Date.UTC(Number(parsed[1]), Number(parsed[2]) - 1, Number(parsed[3]))) : null
  // Browsers lack short Kazakh month names ("M08"), so Kazakh uses its own abbreviations.
  const month = value
    ? language === "kk"
      ? KK_MONTHS_SHORT[value.getUTCMonth()]
      : new Intl.DateTimeFormat(language === "ru" ? "ru-RU" : "en-GB", { month: "short", timeZone: "UTC" }).format(value)
    : null

  return (
    <li className="grid grid-cols-[5.5rem_1fr] items-center gap-5 py-5 sm:grid-cols-[6.5rem_1fr]">
      <span
        className={cn(
          "grid aspect-square place-content-center text-center",
          value ? "on-field bg-field" : "border-2 border-dashed border-input text-muted-foreground",
        )}
      >
        {value ? (
          <>
            <span className="tabular font-display text-5xl leading-none font-extrabold">{value.getUTCDate()}</span>
            <span className="mt-1 font-display text-lg font-bold uppercase">{month?.replace(".", "")}</span>
          </>
        ) : (
          <span className="font-display text-4xl font-extrabold" aria-hidden="true">
            —
          </span>
        )}
      </span>
      <span>
        <span className="block text-lg font-semibold">{label}</span>
        <span className={cn("tabular mt-1 block", value ? "text-muted-foreground" : "font-medium text-terracotta")}>
          {value && parsed ? `${parsed[3]}.${parsed[2]}.${parsed[1]}` : notPublished}
        </span>
      </span>
    </li>
  )
}
