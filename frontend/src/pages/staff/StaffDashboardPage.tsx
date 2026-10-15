import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { type ReactNode, useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { type Analytics, getAnalytics } from "@/api/staff"
import { Button } from "@/components/ui/button"
import { useStaffT } from "@/staff/i18n"
import { selectClass } from "@/staff/styles"

// Validated with the dataviz palette checks on the card surface #fffcf7
// (lightness band, chroma, colour-blind separation, 3:1 contrast all pass).
const ANSWERED = "#2a78d6"
const UNANSWERED = "#eb6834"
const PERIODS = [7, 14, 30]
const PLOT_HEIGHT = 160

function Tile({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="rounded-md border border-border bg-card p-4">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
      {note && <p className="mt-0.5 text-xs text-muted-foreground">{note}</p>}
    </div>
  )
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-md border border-border bg-card p-4">
      <h2 className="text-sm font-medium">{title}</h2>
      <div className="mt-3">{children}</div>
    </section>
  )
}

function Legend() {
  const t = useStaffT()
  return (
    <div className="flex gap-4 text-xs text-muted-foreground">
      {[
        [ANSWERED, t("dash.answered")],
        [UNANSWERED, t("dash.unanswered")],
      ].map(([color, label]) => (
        <span key={label} className="flex items-center gap-1.5">
          <span className="inline-block size-2.5 rounded-sm" style={{ background: color }} />
          {label}
        </span>
      ))}
    </div>
  )
}

function PerDayChart({ data }: { data: Analytics["per_day"] }) {
  const t = useStaffT()
  const [active, setActive] = useState<number | null>(null)
  const max = Math.max(1, ...data.map((day) => day.questions))
  const ticks = [max, Math.round(max / 2), 0].filter((value, index, all) => all.indexOf(value) === index)

  return (
    <div>
      <Legend />
      <div className="mt-3 flex gap-2">
        <div className="relative w-6 shrink-0 text-right text-[10px] text-muted-foreground tabular-nums" style={{ height: PLOT_HEIGHT }}>
          {ticks.map((value) => (
            <span key={value} className="absolute right-0 -translate-y-1/2" style={{ top: PLOT_HEIGHT - (value / max) * PLOT_HEIGHT }}>
              {value}
            </span>
          ))}
        </div>
        <div className="relative flex-1">
          {ticks.map((value) => (
            <div
              key={value}
              className="absolute inset-x-0 border-t border-border/50"
              style={{ top: PLOT_HEIGHT - (value / max) * PLOT_HEIGHT }}
            />
          ))}
          <div className="relative flex items-end gap-0.5" style={{ height: PLOT_HEIGHT }}>
            {data.map((day, index) => {
              const unanswered = Math.min(day.unanswered, day.questions)
              const answered = day.questions - unanswered
              const label = `${day.date}: ${t("dash.questions")} ${day.questions}, ${t("dash.answered")} ${answered}, ${t("dash.unanswered")} ${unanswered}`
              return (
                <button
                  key={day.date}
                  type="button"
                  aria-label={label}
                  className="relative flex h-full flex-1 flex-col justify-end outline-none focus-visible:bg-muted/60 hover:bg-muted/40"
                  onMouseEnter={() => setActive(index)}
                  onMouseLeave={() => setActive(null)}
                  onFocus={() => setActive(index)}
                  onBlur={() => setActive(null)}
                >
                  {unanswered > 0 && (
                    <span
                      className="mx-auto block w-full max-w-6 rounded-t"
                      style={{ height: (unanswered / max) * PLOT_HEIGHT, background: UNANSWERED, marginBottom: answered > 0 ? 2 : 0 }}
                    />
                  )}
                  {answered > 0 && (
                    <span
                      className={`mx-auto block w-full max-w-6 ${unanswered > 0 ? "" : "rounded-t"}`}
                      style={{ height: (answered / max) * PLOT_HEIGHT, background: ANSWERED }}
                    />
                  )}
                  {active === index && (
                    <span
                      role="tooltip"
                      className="pointer-events-none absolute bottom-full left-1/2 z-10 mb-1 w-max -translate-x-1/2 rounded border border-border bg-card px-2 py-1 text-left text-xs shadow-sm"
                    >
                      <span className="block font-medium">{day.date}</span>
                      <span className="block">
                        {t("dash.answered")}: {answered}
                      </span>
                      <span className="block">
                        {t("dash.unanswered")}: {unanswered}
                      </span>
                    </span>
                  )}
                </button>
              )
            })}
          </div>
          <div className="mt-1 flex justify-between text-[10px] text-muted-foreground tabular-nums">
            <span>{data[0]?.date.slice(5)}</span>
            <span>{data[data.length - 1]?.date.slice(5)}</span>
          </div>
        </div>
      </div>
      <details className="mt-3 text-xs">
        <summary className="cursor-pointer text-muted-foreground">{t("dash.table")}</summary>
        <table className="mt-2 w-full text-left tabular-nums">
          <thead className="text-muted-foreground">
            <tr>
              <th className="font-normal">{t("dash.date")}</th>
              <th className="font-normal">{t("dash.questions")}</th>
              <th className="font-normal">{t("dash.unanswered")}</th>
            </tr>
          </thead>
          <tbody>
            {data.map((day) => (
              <tr key={day.date}>
                <td>{day.date}</td>
                <td>{day.questions}</td>
                <td>{day.unanswered}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </div>
  )
}

function Bars({ rows }: { rows: { label: string; value: number }[] }) {
  const t = useStaffT()
  const max = Math.max(1, ...rows.map((row) => row.value))
  if (rows.every((row) => row.value === 0)) return <p className="text-sm text-muted-foreground">{t("dash.none")}</p>
  return (
    <ul className="space-y-2 text-sm">
      {rows.map((row) => (
        <li key={row.label} className="grid grid-cols-[6rem_1fr_2.5rem] items-center gap-2">
          <span className="truncate">{row.label}</span>
          <span className="h-2.5 rounded-r bg-muted">
            <span className="block h-full rounded-r" style={{ width: `${(row.value / max) * 100}%`, background: ANSWERED }} />
          </span>
          <span className="text-right tabular-nums">{row.value}</span>
        </li>
      ))}
    </ul>
  )
}

export function StaffDashboardPage() {
  const t = useStaffT()
  const [params, setParams] = useSearchParams()
  const days = PERIODS.find((value) => String(value) === params.get("days")) ?? 7

  const report = useQuery({
    queryKey: ["staff", "analytics", days],
    queryFn: ({ signal }) => getAnalytics(days, signal),
    placeholderData: keepPreviousData,
  })

  const header = (
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{t("dash.title")}</h1>
        <p className="mt-1 max-w-2xl text-sm text-muted-foreground">{t("dash.lead")}</p>
      </div>
      <select
        aria-label={t("inbox.period")}
        className={selectClass}
        value={days}
        onChange={(event) => setParams({ days: event.target.value }, { replace: true })}
      >
        {PERIODS.map((value) => (
          <option key={value} value={value}>
            {t("inbox.days", { days: value })}
          </option>
        ))}
      </select>
    </div>
  )

  if (report.isPending) return <>{header}<p className="mt-6 text-sm text-muted-foreground">{t("common.loading")}</p></>
  if (report.isError) {
    return (
      <>
        {header}
        <div className="mt-6 text-sm">
          <p>{t("common.error")}</p>
          <Button variant="outline" size="sm" className="mt-3" onClick={() => report.refetch()}>
            {t("common.retry")}
          </Button>
        </div>
      </>
    )
  }

  const data = report.data
  const answered = Math.max(0, data.questions - data.unanswered)
  const share = (value: number) => (data.questions ? `${Math.round((value / data.questions) * 100)}%` : "—")

  return (
    <div>
      {header}
      <div className="mt-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Tile label={t("dash.questions")} value={String(data.questions)} note={`${t("dash.sessions")}: ${data.sessions}`} />
        <Tile label={t("dash.answered")} value={share(answered)} note={String(answered)} />
        <Tile label={t("dash.unanswered")} value={share(data.unanswered)} note={String(data.unanswered)} />
        <Tile label={t("dash.ratings")} value={`👍 ${data.ratings.up} · 👎 ${data.ratings.down}`} />
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Section title={t("dash.perDay")}>
          <PerDayChart data={data.per_day} />
        </Section>
        <Section title={t("dash.topQuestions")}>
          {data.top_questions.length === 0 ? (
            <p className="text-sm text-muted-foreground">{t("dash.none")}</p>
          ) : (
            <ol className="space-y-1.5 text-sm">
              {data.top_questions.map((row) => (
                <li key={row.question} className="flex justify-between gap-3">
                  <span className="min-w-0 break-words">{row.question}</span>
                  <span className="shrink-0 tabular-nums text-muted-foreground">{row.count}</span>
                </li>
              ))}
            </ol>
          )}
        </Section>
        <Section title={t("dash.topSources")}>
          {data.top_sources.length === 0 ? (
            <p className="text-sm text-muted-foreground">{t("dash.none")}</p>
          ) : (
            <ol className="space-y-1.5 text-sm">
              {data.top_sources.map((row) => (
                <li key={row.faq_id} className="flex justify-between gap-3">
                  <Link to={`/staff/faq/${row.faq_id}`} className="min-w-0 break-words hover:underline">
                    <span className="text-muted-foreground">{row.faq_id}</span> {row.question}
                  </Link>
                  <span className="shrink-0 tabular-nums text-muted-foreground">{row.count}</span>
                </li>
              ))}
            </ol>
          )}
        </Section>
        <div className="grid gap-4">
          <Section title={t("dash.languages")}>
            <Bars rows={(["kk", "ru", "en"] as const).map((language) => ({ label: language.toUpperCase(), value: data.languages[language] ?? 0 }))} />
          </Section>
          <Section title={t("dash.reasons")}>
            <Bars
              rows={Object.entries(data.down_reasons).map(([reason, value]) => ({
                label: reason === "none" ? t("dash.reason.none") : reason,
                value,
              }))}
            />
          </Section>
        </div>
      </div>
    </div>
  )
}
