import { useQuery } from "@tanstack/react-query"
import { ArrowRight, ArrowUpRight, Search as SearchIcon } from "lucide-react"
import { useState, type FormEvent, type ReactNode } from "react"
import { Link, useSearchParams } from "react-router-dom"
import type { ApplicationStatus } from "@/api/applications"
import { getFunding, searchFaq } from "@/api/guidance"
import { allProgramsQuery } from "@/api/programs"
import type { DegreeLevel } from "@/api/types"
import { useApplicationsT } from "@/applications/i18n"
import { StatusBadge } from "@/components/applications/StatusBadge"
import { ApplyAction } from "@/components/common/ApplyAction"
import { ConnectionError } from "@/components/common/ConnectionError"
import { GuidanceShell } from "@/components/guidance/GuidanceShell"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useGuidanceT } from "@/guidance/i18n"
import { useI18n } from "@/i18n"
import { useInfoT, type InfoKey } from "@/info/i18n"
import { LEVELS, levelDeadlines, type LevelDeadlines } from "@/lib/catalogue"
import { ADMISSIONS_PHONE, ADMISSIONS_WEBSITE } from "@/lib/constants"
import { deadlineStatus } from "@/lib/dates"
import { useChatStore } from "@/store/chat"

// Information pages after Purdue's admissions site (how to apply, deadlines, status, contact).
// Every date and count comes from the live catalogue; nothing here is typed in by hand.

const MAP_URL = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent("SDU University, Kaskelen")}`
const SPLIT = "grid grid-cols-1 gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.6fr)] lg:gap-16"

type Route = {
  id: string
  title: InfoKey
  text: InfoKey
  level: DegreeLevel
  dates: { label: InfoKey; value: (levels: LevelDeadlines) => string | null }[]
}

const ROUTES: Route[] = [
  {
    id: "bachelor-local",
    title: "apply.route.bachelorLocal",
    text: "apply.route.bachelorLocal.text",
    level: "bachelor",
    dates: [{ label: "apply.local", value: (levels) => levels.bachelor.local }],
  },
  {
    id: "bachelor-international",
    title: "apply.route.bachelorIntl",
    text: "apply.route.bachelorIntl.text",
    level: "bachelor",
    dates: [{ label: "apply.international", value: (levels) => levels.bachelor.international }],
  },
  {
    id: "master",
    title: "apply.route.master",
    text: "apply.route.master.text",
    level: "master",
    dates: [
      { label: "apply.local", value: (levels) => levels.master.local },
      { label: "apply.international", value: (levels) => levels.master.international },
    ],
  },
  {
    id: "phd",
    title: "apply.route.phd",
    text: "apply.route.phd.text",
    level: "phd",
    dates: [
      { label: "apply.local", value: (levels) => levels.phd.local },
      { label: "apply.international", value: (levels) => levels.phd.international },
    ],
  },
]

const STEPS: { title: InfoKey; text: InfoKey; to?: string }[] = [
  { title: "apply.step1", text: "apply.step1.text", to: "/account/register" },
  { title: "apply.step2", text: "apply.step2.text", to: "/programs" },
  { title: "apply.step3", text: "apply.step3.text" },
  { title: "apply.step4", text: "apply.step4.text", to: "/account/applications" },
  { title: "apply.step5", text: "apply.step5.text", to: "/application-status" },
  { title: "apply.step6", text: "apply.step6.text", to: "/contact" },
]

function useLevels() {
  const catalogue = useQuery(allProgramsQuery)
  return catalogue.data ? levelDeadlines(catalogue.data.programs) : null
}

// The catalogue request itself, for pages that must say when it failed instead of waiting forever.
function useCatalogueState() {
  const catalogue = useQuery(allProgramsQuery)
  return { failed: catalogue.isError, retrying: catalogue.isFetching, retry: () => void catalogue.refetch() }
}

function SectionTitle({ id, children }: { id?: string; children: ReactNode }) {
  return (
    <h2 id={id} className="text-[clamp(1.75rem,2.6vw,2.25rem)] leading-[1.12] font-medium">
      {children}
    </h2>
  )
}

export function ApplyPage() {
  const t = useInfoT()
  const { t: appT, deadlineWithStatus } = useI18n()
  const levels = useLevels()
  const catalogue = useCatalogueState()

  return (
    <GuidanceShell title={t("apply.title")} lead={t("apply.lead")} tools={false}>
      {catalogue.failed ? (
        <div className="mb-8">
          <ConnectionError message={appT("programs.unavailable")} retrying={catalogue.retrying} onRetry={catalogue.retry} />
        </div>
      ) : null}
      <nav aria-label={t("apply.jump")} className="flex flex-wrap gap-x-8 gap-y-3 border-b border-border pb-6">
        {ROUTES.map((route) => (
          <a key={route.id} href={`#${route.id}`} className="font-semibold text-primary underline decoration-primary/30 underline-offset-4 hover:decoration-primary">
            {t(route.title)}
          </a>
        ))}
      </nav>

      <section aria-labelledby="steps-title" className={`mt-14 ${SPLIT}`}>
        <div>
          <SectionTitle id="steps-title">{t("apply.stepsTitle")}</SectionTitle>
          <p className="mt-5 max-w-[46ch] text-muted-foreground">{t("apply.official")}</p>
        </div>
        <ol className="border-t-2 border-ink">
          {STEPS.map((step, index) => {
            const body = (
              <>
                <span className="tabular font-display text-3xl leading-none font-bold text-primary">{index + 1}</span>
                <span className="min-w-0">
                  <span className="block text-lg font-semibold">{t(step.title)}</span>
                  <span className="mt-1 block text-muted-foreground">{t(step.text)}</span>
                </span>
                {step.to ? <ArrowRight className="mt-1 size-5 shrink-0 text-primary transition-transform duration-200 group-hover:translate-x-[3px]" aria-hidden="true" /> : <span />}
              </>
            )
            const layout = "grid grid-cols-[2.5rem_minmax(0,1fr)_1.25rem] items-start gap-4 py-5"
            return (
              <li key={step.title} className="border-b border-border">
                {step.to ? (
                  <Link to={step.to} className={`group ${layout} transition-colors hover:bg-secondary/60 sm:-mx-2 sm:px-2`}>
                    {body}
                  </Link>
                ) : (
                  <div className={`${layout} sm:-mx-2 sm:px-2`}>{body}</div>
                )}
              </li>
            )
          })}
        </ol>
      </section>

      {ROUTES.map((route) => (
        <section key={route.id} id={route.id} aria-labelledby={`${route.id}-title`} className={`mt-16 scroll-mt-8 border-t-2 border-ink pt-10 ${SPLIT}`}>
          <div>
            <SectionTitle id={`${route.id}-title`}>{t(route.title)}</SectionTitle>
            <p className="mt-4 max-w-[46ch] text-muted-foreground">{t(route.text)}</p>
          </div>
          <div>
            <dl className="divide-y divide-border border-y border-border">
              {route.dates.map((date) => (
                <div key={date.label} className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 py-4">
                  <dt className="text-muted-foreground">
                    {t("apply.deadline")} · {t(date.label)}
                  </dt>
                  <dd className="tabular text-lg font-semibold">{levels ? deadlineWithStatus(date.value(levels)) : "…"}</dd>
                </div>
              ))}
            </dl>
            <div className="mt-6 flex flex-wrap items-center gap-x-8 gap-y-4">
              <ApplyAction label={t("apply.applyNow")} />
              <Link
                to={`/programs?degree_level=${route.level}`}
                className="group inline-flex items-center gap-2 font-semibold text-primary"
              >
                {t("apply.programs", { count: levels ? levels[route.level].count : "…" })}
                <ArrowRight className="size-4 transition-transform duration-200 group-hover:translate-x-[3px]" aria-hidden="true" />
              </Link>
            </div>
          </div>
        </section>
      ))}
    </GuidanceShell>
  )
}

export function DeadlinesPage() {
  const t = useInfoT()
  const { t: appT, language, deadline } = useI18n()
  const levels = useLevels()
  const catalogue = useCatalogueState()
  const lower = (text: string) => text.toLocaleLowerCase(language)
  const rows = ROUTES.flatMap((route) =>
    route.dates.map((date) => ({
      key: `${route.id}-${date.label}`,
      route: route.id,
      label: route.level === "bachelor" ? t(route.title) : `${t(route.title)}, ${lower(t(date.label))}`,
      value: levels ? date.value(levels) : null,
    })),
  )

  return (
    <GuidanceShell title={t("deadlines.title")} lead={t("deadlines.lead")} tools={false}>
      <div className={SPLIT}>
        <aside aria-labelledby="notes-title" className="order-2 lg:order-1">
          <h2 id="notes-title" className="text-[clamp(1.5rem,2vw,1.875rem)] leading-[1.15] font-medium">
            {t("deadlines.notesTitle")}
          </h2>
          <ul className="mt-5 divide-y divide-border border-y border-border text-muted-foreground">
            {(["deadlines.note1", "deadlines.note2", "deadlines.note3", "deadlines.note4"] as const).map((note) => (
              <li key={note} className="py-3">
                {t(note)}
              </li>
            ))}
          </ul>
        </aside>
        <div className="order-1 lg:order-2">
          {catalogue.failed ? (
            <div className="mb-6">
              <ConnectionError message={appT("programs.unavailable")} retrying={catalogue.retrying} onRetry={catalogue.retry} />
            </div>
          ) : null}
          {levels && levels.bachelor.local && deadlineStatus(levels.bachelor.local) === "closed" && deadlineStatus(levels.bachelor.international) !== "upcoming" ? (
            <p className="mb-6 font-semibold">{appT("home.dates.cycleClosed")}</p>
          ) : null}
          <table className="w-full table-fixed text-left">
            <caption className="sr-only">{t("deadlines.title")}</caption>
            <colgroup>
              <col className="w-[37%]" />
              <col className="w-[27%]" />
              <col className="w-[36%]" />
            </colgroup>
            <thead className="border-y-2 border-ink text-sm text-muted-foreground">
              <tr>
                <th scope="col" className="py-3 pr-4 font-semibold">{t("deadlines.route")}</th>
                <th scope="col" className="py-3 pr-4 font-semibold">{t("deadlines.date")}</th>
                <th scope="col" className="py-3 text-right font-semibold">{t("deadlines.status")}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const status = levels ? deadlineStatus(row.value) : null
                return (
                  <tr key={row.key} className="border-b border-border align-top">
                    <th scope="row" className="py-4 pr-4 font-semibold">
                      <a href={`/apply#${row.route}`} className="underline decoration-primary/30 underline-offset-4 hover:text-primary hover:decoration-primary">
                        {row.label}
                      </a>
                    </th>
                    <td className="tabular py-4 pr-4">{levels ? (row.value ? deadline(row.value) : "—") : "…"}</td>
                    <td className="py-4 text-right">
                      {status === "upcoming" ? (
                        <Badge tone="field">{t("deadlines.upcoming")}</Badge>
                      ) : status === "closed" ? (
                        <span className="label text-foreground">{t("deadlines.closed")}</span>
                      ) : status === "unpublished" ? (
                        <span className="text-sm text-muted-foreground">{t("deadlines.unpublished")}</span>
                      ) : null}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          <div className="mt-8">
            <ApplyAction label={t("apply.applyNow")} />
          </div>
        </div>
      </div>
    </GuidanceShell>
  )
}

const STATUSES: ApplicationStatus[] = ["draft", "submitted", "in_review", "needs_changes", "accepted", "rejected"]

export function StatusGuidePage() {
  const t = useInfoT()
  const applicationsT = useApplicationsT()

  return (
    <GuidanceShell title={t("status.title")} lead={t("status.lead")} tools={false}>
      <div className={SPLIT}>
        <div>
          <p className="max-w-[46ch] text-muted-foreground">{t("status.note")}</p>
          <Button asChild variant="outline" className="mt-6">
            <Link to="/account/applications">
              {t("status.open")}
              <ArrowRight aria-hidden="true" />
            </Link>
          </Button>
        </div>
        <dl className="border-t-2 border-ink">
          {STATUSES.map((status) => (
            <div key={status} className="grid grid-cols-1 gap-3 border-b border-border py-5 sm:grid-cols-[12rem_minmax(0,1fr)] sm:gap-6">
              <dt>
                <StatusBadge status={status} />
              </dt>
              <dd>
                <span className="sr-only">{t("status.next")}: </span>
                {applicationsT(`help.${status}`)}
              </dd>
            </div>
          ))}
        </dl>
      </div>
    </GuidanceShell>
  )
}

export function ContactPage() {
  const t = useInfoT()
  const { t: appT, language } = useI18n()
  const guidanceT = useGuidanceT()
  const setChatOpen = useChatStore((state) => state.setOpen)
  const email = appT("footer.email")

  return (
    <GuidanceShell title={t("contact.title")} lead={t("contact.lead")} tools={false}>
      <div className={SPLIT}>
        <section aria-labelledby="office-title">
          <h2 id="office-title" className="font-heading text-xl font-medium">
            {t("contact.office")}
          </h2>
          <address className="mt-4 not-italic">
            <span className="block font-heading text-[clamp(1.5rem,2vw,1.875rem)] leading-[1.15] font-medium">{appT("contact.name")}</span>
            <span className="mt-3 block max-w-[32ch] text-lg">{appT("contact.address")}</span>
          </address>
          <a href={MAP_URL} target="_blank" rel="noreferrer" className="mt-5 inline-flex items-center gap-2 font-semibold text-primary underline decoration-primary/30 underline-offset-4 hover:decoration-primary">
            {t("contact.map")}
            <ArrowUpRight className="size-4" aria-hidden="true" />
          </a>
        </section>
        <div className="space-y-12">
          <section aria-labelledby="write-title">
            <h2 id="write-title" className="font-heading text-xl font-medium">
              {t("contact.write")}
            </h2>
            <ul className="mt-4 border-t-2 border-ink">
              <ContactRow href={`tel:${ADMISSIONS_PHONE.replace(/\s/g, "")}`} tabular>
                {ADMISSIONS_PHONE}
              </ContactRow>
              <ContactRow href={`mailto:${email}`}>{email}</ContactRow>
              <ContactRow href={ADMISSIONS_WEBSITE[language]} external>
                {t("contact.official")}
              </ContactRow>
            </ul>
          </section>
          <section aria-labelledby="online-title">
            <h2 id="online-title" className="font-heading text-xl font-medium">
              {t("contact.online")}
            </h2>
            <ul className="mt-4 border-t-2 border-ink">
              <li className="border-b border-border">
                <Link to="/account/requests" className="group grid grid-cols-[minmax(0,1fr)_1.25rem] items-start gap-4 py-5 transition-colors hover:bg-secondary/60 sm:-mx-2 sm:px-2">
                  <span>
                    <span className="block text-lg font-semibold">{guidanceT("requests")}</span>
                    <span className="mt-1 block text-muted-foreground">{t("contact.questions.text")}</span>
                  </span>
                  <ArrowRight className="mt-1 size-5 text-primary transition-transform duration-200 group-hover:translate-x-[3px]" aria-hidden="true" />
                </Link>
              </li>
              <li className="border-b border-border">
                <button
                  type="button"
                  onClick={() => setChatOpen(true)}
                  className="group grid w-full grid-cols-[minmax(0,1fr)_1.25rem] items-start gap-4 py-5 text-left transition-colors hover:bg-secondary/60 sm:-mx-2 sm:px-2"
                >
                  <span>
                    <span className="block text-lg font-semibold">{t("contact.assistant")}</span>
                    <span className="mt-1 block text-muted-foreground">{t("contact.assistant.text")}</span>
                  </span>
                  <ArrowRight className="mt-1 size-5 text-primary transition-transform duration-200 group-hover:translate-x-[3px]" aria-hidden="true" />
                </button>
              </li>
            </ul>
          </section>
        </div>
      </div>
    </GuidanceShell>
  )
}

function ContactRow({ href, children, tabular, external }: { href: string; children: ReactNode; tabular?: boolean; external?: boolean }) {
  return (
    <li className="border-b border-border">
      <a
        href={href}
        {...(external ? { target: "_blank", rel: "noreferrer" } : {})}
        className={`group flex items-center justify-between gap-4 py-4 text-lg font-semibold transition-colors hover:bg-secondary/60 hover:text-primary sm:-mx-2 sm:px-2${tabular ? " tabular" : ""}`}
      >
        {children}
        {external ? (
          <ArrowUpRight className="size-5 shrink-0 text-primary" aria-hidden="true" />
        ) : (
          <ArrowRight className="size-5 shrink-0 text-primary transition-transform duration-200 group-hover:translate-x-[3px]" aria-hidden="true" />
        )}
      </a>
    </li>
  )
}

// Site search (Purdue's header search): programs from the catalogue, published FAQ answers as
// written by the admissions office, and the pages of this site, grouped.
export function SearchPage() {
  const t = useInfoT()
  const { t: appT, language, degree, programTitle } = useI18n()
  const guidanceT = useGuidanceT()
  const setChatOpen = useChatStore((state) => state.setOpen)
  const setDraft = useChatStore((state) => state.setDraft)
  const [params, setParams] = useSearchParams()
  const q = (params.get("q") ?? "").trim()
  const [draft, setDraftQuery] = useState(q)
  const ready = q.length >= 2
  const catalogue = useQuery(allProgramsQuery)
  const answers = useQuery({
    queryKey: ["faq-search", q, language],
    queryFn: ({ signal }) => searchFaq(q, language, signal),
    enabled: ready,
  })

  const needle = q.toLocaleLowerCase(language)
  const matches = (text: string | null | undefined) => Boolean(text && text.toLocaleLowerCase(language).includes(needle))
  const programs = ready
    ? (catalogue.data?.programs ?? []).filter(
        (program) => matches(program.program_id) || matches(program.title) || matches(program.title_ru) || matches(program.title_kk),
      )
    : []
  const pages = [
    { to: "/apply", title: t("apply.title"), text: t("apply.lead") },
    { to: "/deadlines", title: t("deadlines.title"), text: t("deadlines.lead") },
    { to: "/application-status", title: t("status.title"), text: t("status.lead") },
    { to: "/cost-and-aid", title: t("costaid.title"), text: t("costaid.lead") },
    { to: "/contact", title: t("contact.title"), text: t("contact.lead") },
    { to: "/eligibility", title: guidanceT("eligibility"), text: guidanceT("eligibilityText") },
    { to: "/recommendations", title: guidanceT("recommendations"), text: guidanceT("recommendationsText") },
    { to: "/cost-calculator", title: guidanceT("cost"), text: guidanceT("costText") },
    { to: "/funding", title: guidanceT("funding"), text: guidanceT("fundingText") },
    { to: "/account/requests", title: guidanceT("requests"), text: guidanceT("requestsText") },
    { to: "/compare", title: appT("compare.title"), text: appT("compare.lead") },
  ].filter((page) => ready && (matches(page.title) || matches(page.text)))
  const hits = answers.data?.results ?? []
  const nothing = ready && !catalogue.isPending && !answers.isPending && !programs.length && !pages.length && !hits.length

  return (
    <GuidanceShell title={t("search.title")} lead={t("search.lead")} tools={false}>
      <form
        role="search"
        className="flex max-w-2xl gap-2"
        onSubmit={(event: FormEvent) => {
          event.preventDefault()
          setParams(draft.trim() ? { q: draft.trim() } : {})
        }}
      >
        <label htmlFor="site-search" className="sr-only">
          {t("search.label")}
        </label>
        <Input id="site-search" type="search" autoFocus value={draft} maxLength={200} onChange={(event) => setDraftQuery(event.target.value)} className="h-12 text-base" />
        <Button type="submit" variant="ochre" className="h-12 px-6">
          <SearchIcon aria-hidden="true" />
          {t("search.submit")}
        </Button>
      </form>
      {q && !ready ? <p className="mt-4 text-sm text-muted-foreground">{t("search.hint")}</p> : null}

      {ready ? (
        <div className="mt-12 space-y-14" aria-live="polite">
          {nothing ? (
            <div className="border-t-2 border-ink pt-6">
              <p className="max-w-[60ch] text-lg">{t("search.none", { q })}</p>
              <Button
                variant="outline"
                className="mt-5"
                onClick={() => {
                  setDraft(q)
                  setChatOpen(true)
                }}
              >
                {t("search.ask")}
              </Button>
            </div>
          ) : null}

          {programs.length ? (
            <section aria-labelledby="search-programs">
              <SectionTitle id="search-programs">
                {t("search.programs")} <span className="label tabular align-middle text-muted-foreground">{programs.length}</span>
              </SectionTitle>
              <ul className="mt-5 border-t-2 border-ink">
                {programs.slice(0, 8).map((program) => (
                  <li key={program.program_id} className="border-b border-border">
                    <Link to={`/programs/${program.program_id}`} className="group grid grid-cols-[minmax(0,1fr)_1.25rem] items-center gap-4 py-4 transition-colors hover:bg-secondary/60 sm:-mx-2 sm:px-2">
                      <span className="min-w-0">
                        <span className="block font-heading text-xl font-medium group-hover:text-primary">{programTitle(program)}</span>
                        <span className="tabular mt-1 block text-sm text-muted-foreground">
                          {degree(program.degree_level)} · {program.program_id}
                        </span>
                      </span>
                      <ArrowRight className="size-5 text-primary transition-transform duration-200 group-hover:translate-x-[3px]" aria-hidden="true" />
                    </Link>
                  </li>
                ))}
              </ul>
              {programs.length > 8 ? (
                <Link to={`/programs?q=${encodeURIComponent(q)}`} className="mt-4 inline-flex items-center gap-2 font-semibold text-primary">
                  {t("search.allPrograms")}
                  <ArrowRight className="size-4" aria-hidden="true" />
                </Link>
              ) : null}
            </section>
          ) : null}

          {answers.isError ? <p className="text-muted-foreground">{t("search.answersError")}</p> : null}
          {hits.length ? (
            <section aria-labelledby="search-answers">
              <SectionTitle id="search-answers">{t("search.answers")}</SectionTitle>
              <ul className="mt-5 border-t-2 border-ink">
                {hits.map((hit) => (
                  <li key={hit.faq_id} className="border-b border-border py-5">
                    <h3 className="text-lg font-semibold">{hit.question}</h3>
                    <p className="mt-2 line-clamp-4 max-w-[75ch] whitespace-pre-line text-muted-foreground">{hit.answer}</p>
                    <a href={hit.source_link} target="_blank" rel="noreferrer" className="mt-2 inline-flex items-center gap-1 text-sm font-semibold text-primary underline decoration-primary/30 underline-offset-4">
                      {t("search.source")}
                      <ArrowUpRight className="size-3.5" aria-hidden="true" />
                    </a>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {pages.length ? (
            <section aria-labelledby="search-pages">
              <SectionTitle id="search-pages">{t("search.pages")}</SectionTitle>
              <ul className="mt-5 border-t-2 border-ink">
                {pages.map((page) => (
                  <li key={page.to} className="border-b border-border">
                    <Link to={page.to} className="group grid grid-cols-[minmax(0,1fr)_1.25rem] items-start gap-4 py-4 transition-colors hover:bg-secondary/60 sm:-mx-2 sm:px-2">
                      <span className="min-w-0">
                        <span className="block text-lg font-semibold group-hover:text-primary">{page.title}</span>
                        <span className="mt-1 block text-muted-foreground">{page.text}</span>
                      </span>
                      <ArrowRight className="mt-1 size-5 text-primary transition-transform duration-200 group-hover:translate-x-[3px]" aria-hidden="true" />
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}
        </div>
      ) : null}
    </GuidanceShell>
  )
}

// Cost and aid in one place (Purdue's cost-financial-aid page): tuition per credit by level
// from the catalogue, then the grants and discounts the admissions office has answered about.
export function CostAidPage() {
  const t = useInfoT()
  const { t: appT, language, degree, deadline } = useI18n()
  const catalogue = useQuery(allProgramsQuery)
  const funding = useQuery({
    queryKey: ["funding", language, "", ""],
    queryFn: ({ signal }) => getFunding(language, undefined, undefined, signal),
  })
  const numbers = new Intl.NumberFormat(language === "en" ? "en-GB" : "ru-RU")
  const range = (values: (number | null)[], unit: string) => {
    const known = values.filter((value): value is number => value !== null)
    if (!known.length) return null
    const low = Math.min(...known)
    const high = Math.max(...known)
    return low === high ? `${numbers.format(low)} ${unit}` : appT("format.range", { min: numbers.format(low), max: `${numbers.format(high)} ${unit}` })
  }
  const programs = catalogue.data?.programs ?? []

  return (
    <GuidanceShell title={t("costaid.title")} lead={t("costaid.lead")} tools={false}>
      <section aria-labelledby="costs-title" className={SPLIT}>
        <div>
          <SectionTitle id="costs-title">{t("costaid.costsTitle")}</SectionTitle>
          <Button asChild variant="outline" className="mt-6">
            <Link to="/cost-calculator">
              {t("costaid.calculator")}
              <ArrowRight aria-hidden="true" />
            </Link>
          </Button>
        </div>
        <table className="block w-full text-left sm:table sm:table-fixed">
          <caption className="sr-only">{t("costaid.costsTitle")}</caption>
          <thead className="block border-y-2 border-ink text-sm text-muted-foreground sm:table-header-group">
            {/* Below sm each level heads its own row and the two figures sit side by side under it. */}
            <tr className="grid grid-cols-2 gap-x-4 sm:table-row">
              <th scope="col" className="hidden w-[30%] py-3 pr-4 font-semibold sm:table-cell">{t("costaid.level")}</th>
              <th scope="col" className="py-3 pr-4 font-semibold">{t("costaid.local")}</th>
              <th scope="col" className="py-3 font-semibold">{t("costaid.international")}</th>
            </tr>
          </thead>
          <tbody className="block sm:table-row-group">
            {LEVELS.map((level) => {
              const items = programs.filter((program) => program.degree_level === level)
              return (
                <tr key={level} className="grid grid-cols-2 gap-x-4 border-b border-border align-baseline sm:table-row">
                  <th scope="row" className="col-span-2 pt-4 font-heading text-xl font-medium sm:py-4 sm:pr-4">{degree(level)}</th>
                  <td className="tabular pt-1 pb-4 font-semibold sm:py-4 sm:pr-4 sm:text-lg">{catalogue.data ? (range(items.map((p) => p.tuition_per_ects_kzt), "₸") ?? appT("format.notPublishedYet")) : "…"}</td>
                  <td className="tabular pt-1 pb-4 font-semibold sm:py-4 sm:text-lg">{catalogue.data ? (range(items.map((p) => p.tuition_per_ects_usd), "USD") ?? appT("format.notPublishedYet")) : "…"}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </section>

      <section aria-labelledby="aid-title" className={`mt-16 border-t-2 border-ink pt-10 ${SPLIT}`}>
        <div>
          <SectionTitle id="aid-title">{t("costaid.aidTitle")}</SectionTitle>
          <p className="mt-4 max-w-[46ch] text-muted-foreground">{t("costaid.aidLead")}</p>
          <Link to="/funding" className="group mt-6 inline-flex items-center gap-2 font-semibold text-primary">
            {t("costaid.allAid")}
            <ArrowRight className="size-4 transition-transform duration-200 group-hover:translate-x-[3px]" aria-hidden="true" />
          </Link>
        </div>
        <ul className="border-t-2 border-ink">
          {(funding.data?.items ?? []).slice(0, 6).map((item) => (
            <li key={item.faq_id} className="border-b border-border py-5">
              <h3 className="text-lg font-semibold">{item.title}</h3>
              <p className="mt-1 line-clamp-3 text-muted-foreground">{item.text}</p>
              <p className="mt-2 text-sm text-muted-foreground">{t("costaid.checked", { date: deadline(item.last_checked) })}</p>
            </li>
          ))}
        </ul>
      </section>
    </GuidanceShell>
  )
}
