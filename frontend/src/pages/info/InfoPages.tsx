import { useQuery } from "@tanstack/react-query"
import { ArrowRight, ArrowUpRight } from "lucide-react"
import type { ReactNode } from "react"
import { Link } from "react-router-dom"
import type { ApplicationStatus } from "@/api/applications"
import { allProgramsQuery } from "@/api/programs"
import type { DegreeLevel } from "@/api/types"
import { useApplicationsT } from "@/applications/i18n"
import { StatusBadge } from "@/components/applications/StatusBadge"
import { ApplyAction } from "@/components/common/ApplyAction"
import { GuidanceShell } from "@/components/guidance/GuidanceShell"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useGuidanceT } from "@/guidance/i18n"
import { useI18n } from "@/i18n"
import { useInfoT, type InfoKey } from "@/info/i18n"
import { levelDeadlines, type LevelDeadlines } from "@/lib/catalogue"
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

function SectionTitle({ id, children }: { id?: string; children: ReactNode }) {
  return (
    <h2 id={id} className="text-[clamp(1.75rem,2.6vw,2.25rem)] leading-[1.12] font-medium">
      {children}
    </h2>
  )
}

export function ApplyPage() {
  const t = useInfoT()
  const { deadlineWithStatus } = useI18n()
  const levels = useLevels()

  return (
    <GuidanceShell title={t("apply.title")} lead={t("apply.lead")} tools={false}>
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
  const { language, deadline } = useI18n()
  const levels = useLevels()
  const lower = (text: string) => text.toLocaleLowerCase(language)
  const rows = ROUTES.flatMap((route) =>
    route.dates.map((date) => ({
      key: `${route.id}-${date.label}`,
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
          <ul className="mt-5 space-y-3 text-muted-foreground">
            {(["deadlines.note1", "deadlines.note2", "deadlines.note3", "deadlines.note4"] as const).map((note) => (
              <li key={note} className="border-l-2 border-primary pl-4">
                {t(note)}
              </li>
            ))}
          </ul>
        </aside>
        <div className="order-1 lg:order-2">
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
                    <th scope="row" className="py-4 pr-4 font-semibold">{row.label}</th>
                    <td className="tabular py-4 pr-4">{levels ? (row.value ? deadline(row.value) : "—") : "…"}</td>
                    <td className="py-4 text-right">
                      {status === "upcoming" ? (
                        <Badge tone="field">{t("deadlines.upcoming")}</Badge>
                      ) : status === "closed" ? (
                        <Badge tone="neutral">{t("deadlines.closed")}</Badge>
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
          <h2 id="office-title" className="label text-primary">
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
            <h2 id="write-title" className="label text-primary">
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
            <h2 id="online-title" className="label text-primary">
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
