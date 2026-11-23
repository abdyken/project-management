import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { X, ArrowLeft } from "lucide-react"
import { useEffect } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { isNotFound } from "@/api/errors"
import { comparePrograms } from "@/api/programs"
import type { ComparedProgram } from "@/api/types"
import { ConnectionError } from "@/components/common/ConnectionError"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { ApplyAction } from "@/components/common/ApplyAction"
import { useI18n, type I18n } from "@/i18n"
import type { MessageKey } from "@/i18n/messages"
import { MAX_COMPARED, useCompareStore } from "@/store/compare"
import { RidgeHorizon } from "@/components/mosaic/RidgeHorizon"

const labelClass = "text-sm font-semibold text-muted-foreground"

type Row = { label: MessageKey; value: (program: ComparedProgram, i18n: I18n) => string }

function documents(count: number, i18n: I18n) {
  return count === 0 ? i18n.t("format.notPublished") : i18n.tn("compare.documents", count)
}

const ROWS: Row[] = [
  { label: "compare.row.school", value: (program, i18n) => i18n.schoolName(program.faculty) },
  { label: "compare.row.language", value: (program, i18n) => i18n.languages(program.language) },
  { label: "compare.row.tuitionLocal", value: (program, i18n) => i18n.tuitionKzt(program.tuition_per_ects_kzt) },
  { label: "compare.row.tuitionInternational", value: (program, i18n) => i18n.tuitionUsd(program.tuition_per_ects_usd) },
  { label: "compare.row.deadlineLocal", value: (program, i18n) => i18n.deadlineWithStatus(program.deadline_local) },
  { label: "compare.row.deadlineInternational", value: (program, i18n) => i18n.deadlineWithStatus(program.deadline_international) },
  { label: "compare.row.documentsLocal", value: (program, i18n) => documents(program.documents_local, i18n) },
  {
    label: "compare.row.documentsInternational",
    value: (program, i18n) => documents(program.documents_international, i18n),
  },
]

function missingId(error: unknown, ids: string[]) {
  const match = error instanceof Error ? /Program not found: (\S+)/.exec(error.message) : null
  return match && ids.includes(match[1]) ? match[1] : null
}

function readIds(params: URLSearchParams) {
  const raw = params.get("ids")
  if (raw === null) return null
  return [...new Set(raw.split(",").map((id) => id.trim()).filter(Boolean))].slice(0, MAX_COMPARED)
}

export function ComparePage() {
  const { t } = useI18n()
  const [searchParams, setSearchParams] = useSearchParams()
  const storedIds = useCompareStore((state) => state.ids)
  const remove = useCompareStore((state) => state.remove)
  const clear = useCompareStore((state) => state.clear)
  const urlIds = readIds(searchParams)
  const ids = urlIds ?? storedIds

  useEffect(() => {
    if (urlIds === null) return
    const current = useCompareStore.getState().ids
    if (current.join(",") !== urlIds.join(",")) useCompareStore.setState({ ids: urlIds })
  }, [urlIds])

  const query = useQuery({
    queryKey: ["compare", ids],
    queryFn: () => comparePrograms(ids),
    enabled: ids.length >= 2,
    placeholderData: keepPreviousData,
  })
  const shown = query.data?.programs.filter((program) => ids.includes(program.program_id)) ?? []

  function removeProgram(id: string) {
    remove(id)
    const next = ids.filter((current) => current !== id)
    setSearchParams(next.length ? { ids: next.join(",") } : {}, { replace: true })
  }

  function clearAll() {
    clear()
    setSearchParams({}, { replace: true })
  }

  return (
    <div>
      {/* The same turquoise title band as the other inner pages. */}
      <section className="on-field relative bg-field">
        <div className="mx-auto max-w-[84rem] px-4 pt-8 pb-4 sm:px-6 lg:px-8">
          <Link to="/programs" className="inline-flex items-center gap-2 text-[0.9375rem] font-semibold text-field-muted underline decoration-field-foreground/40 underline-offset-4 hover:text-field-foreground">
            <ArrowLeft className="size-4" aria-hidden="true" />
            {t("detail.backToPrograms").replace(/^←\s*/, "")}
          </Link>
          <h1 className="mt-6 max-w-[20ch] text-[clamp(2.5rem,4.5vw,4rem)] leading-[1.06] font-medium">{t("compare.title")}</h1>
          <p className="mt-5 max-w-[60ch] text-lg text-field-muted">{t("compare.lead", { max: MAX_COMPARED })}</p>
        </div>
        <RidgeHorizon bearing={154} />
      </section>

      <div className="mx-auto max-w-[84rem] px-4 pt-12 pb-20 sm:px-6 sm:pt-16 sm:pb-24 lg:px-8">
        {ids.length < 2 ? (
          <div className="max-w-2xl border-t-2 border-ink pt-6">
            <h2 className="text-[1.75rem] leading-[1.15] font-medium">{t("compare.pickTitle")}</h2>
            <p className="mt-2 text-muted-foreground">
              {ids.length === 1 ? t("compare.oneSelected") : t("compare.noneSelected")}
            </p>
            <Button asChild className="mt-5">
              <Link to="/programs">{t("compare.openCatalogue")}</Link>
            </Button>
          </div>
        ) : null}

        {ids.length >= 2 && shown.length < 2 && query.isFetching ? <p className="text-sm text-muted-foreground">{t("programs.loading")}</p> : null}

        {ids.length >= 2 && query.isError ? (
          isNotFound(query.error) ? (
            <div role="alert" className="max-w-2xl border-t-2 border-ink pt-6">
              <h2 className="text-[1.75rem] leading-[1.15] font-medium">{t("detail.notFound")}</h2>
              <p className="mt-2 text-muted-foreground">
                {t("compare.notFoundText")}
              </p>
              <div className="mt-5 flex flex-wrap gap-2">
                {missingId(query.error, ids) ? (
                  <Button onClick={() => removeProgram(missingId(query.error, ids) as string)}>
                    {t("compare.removeMissing", { code: missingId(query.error, ids) as string })}
                  </Button>
                ) : null}
                <Button variant="outline" onClick={clearAll}>
                  {t("compare.restart")}
                </Button>
              </div>
            </div>
          ) : (
            <ConnectionError
              message={t("compare.loadError")}
              retrying={query.isFetching}
              onRetry={() => void query.refetch()}
            />
          )
        ) : null}

        {ids.length >= 2 && shown.length >= 2 ? <Comparison programs={shown} onRemove={removeProgram} /> : null}
      </div>
    </div>
  )
}

function ProgramHeading({ program, onRemove }: { program: ComparedProgram; onRemove: (id: string) => void }) {
  const { t, programTitle, degree } = useI18n()
  return (
    <div className="flex items-start justify-between gap-2">
      <Link to={`/programs/${program.program_id}`} className="leading-snug hover:text-primary">
        <span className="block font-heading text-lg font-medium">{programTitle(program)}</span>
        <span className="tabular block text-sm text-muted-foreground">
          {degree(program.degree_level)} · {program.program_id}
        </span>
      </Link>
      <button
        type="button"
        aria-label={t("compare.removeAria", { title: programTitle(program) })}
        onClick={() => onRemove(program.program_id)}
        className="shrink-0 p-1 text-muted-foreground hover:bg-secondary hover:text-foreground"
      >
        <X className="size-4" />
      </button>
    </div>
  )
}

function Comparison({ programs, onRemove }: { programs: ComparedProgram[]; onRemove: (id: string) => void }) {
  const i18n = useI18n()
  const { t } = i18n
  // Rows that are the same for every program are greyed, so the differences carry the weight.
  const same = (row: Row) => programs.length > 1 && new Set(programs.map((program) => row.value(program, i18n))).size === 1
  return (
    <>
      {programs.length > 1 ? (
        <p className="mb-4 text-muted-foreground">{t("compare.sameNote")}</p>
      ) : null}
      <table className="hidden w-full table-fixed border-collapse text-[0.9375rem] sm:table">
        <caption className="sr-only">{t("compare.caption")}</caption>
        <thead>
          <tr className="border-b-2 border-ink">
            <th scope="col" className="w-44 py-3 pr-4 text-left">
              <span className="sr-only">{t("compare.field")}</span>
            </th>
            {programs.map((program) => (
              <th key={program.program_id} scope="col" className="py-3 pr-4 text-left align-top text-base font-normal">
                <ProgramHeading program={program} onRemove={onRemove} />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {ROWS.map((row) => (
            <tr key={row.label} className={cn("border-b border-border", same(row) && "text-muted-foreground")}>
              <th scope="row" className={`py-3 pr-4 text-left align-top font-normal ${labelClass}`}>
                {t(row.label)}
                {same(row) ? <span className="sr-only"> ({t("compare.same")})</span> : null}
              </th>
              {programs.map((program) => (
                <td key={program.program_id} className={cn("py-3 pr-4 align-top break-words", !same(row) && "font-semibold text-foreground")}>
                  {row.value(program, i18n)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      <div className="space-y-6 sm:hidden">
        <ul className="space-y-3 border-b border-border pb-4">
          {programs.map((program) => (
            <li key={program.program_id}>
              <ProgramHeading program={program} onRemove={onRemove} />
            </li>
          ))}
        </ul>
        {ROWS.map((row) => (
          <section key={row.label} aria-label={t(row.label)} className={cn(same(row) && "text-muted-foreground")}>
            <h2 className={labelClass}>
              {t(row.label)}
              {same(row) ? <span className="sr-only"> ({t("compare.same")})</span> : null}
            </h2>
            <dl className="mt-2 space-y-1.5 text-sm">
              {programs.map((program) => (
                <div key={program.program_id} className="grid grid-cols-[minmax(0,2fr)_minmax(0,3fr)] gap-3">
                  <dt className="text-muted-foreground break-words">{i18n.programTitle(program)}</dt>
                  <dd className="break-words">{row.value(program, i18n)}</dd>
                </div>
              ))}
            </dl>
          </section>
        ))}
      </div>
      <div className="mt-8">
        <ApplyAction label={t("detail.apply")} />
      </div>
    </>
  )
}
