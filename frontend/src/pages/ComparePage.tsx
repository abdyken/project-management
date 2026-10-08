import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { X } from "lucide-react"
import { useEffect } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { isNotFound } from "@/api/errors"
import { comparePrograms } from "@/api/programs"
import type { ComparedProgram } from "@/api/types"
import { ConnectionError } from "@/components/common/ConnectionError"
import { Button } from "@/components/ui/button"
import { useI18n, type I18n } from "@/i18n"
import type { MessageKey } from "@/i18n/messages"
import { MAX_COMPARED, useCompareStore } from "@/store/compare"

const labelClass = "text-[11px] tracking-[0.14em] text-muted-foreground uppercase"

type Row = { label: MessageKey; value: (program: ComparedProgram, i18n: I18n) => string }

function documents(count: number, i18n: I18n) {
  return count === 0 ? i18n.t("format.notPublished") : i18n.tn("compare.documents", count)
}

const ROWS: Row[] = [
  { label: "compare.row.degree", value: (program, i18n) => `${i18n.degree(program.degree_level)} · ${program.program_id}` },
  { label: "compare.row.school", value: (program) => program.faculty },
  { label: "compare.row.language", value: (program, i18n) => i18n.languages(program.language) },
  { label: "compare.row.tuitionLocal", value: (program, i18n) => i18n.tuitionKzt(program.tuition_per_ects_kzt) },
  { label: "compare.row.tuitionInternational", value: (program, i18n) => i18n.tuitionUsd(program.tuition_per_ects_usd) },
  { label: "compare.row.deadlineLocal", value: (program, i18n) => i18n.deadline(program.deadline_local) },
  { label: "compare.row.deadlineInternational", value: (program, i18n) => i18n.deadline(program.deadline_international) },
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
    <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
      <Link to="/programs" className="text-sm text-muted-foreground hover:text-foreground">
        {t("detail.backToPrograms")}
      </Link>
      <p className={`mt-6 ${labelClass}`}>{t("compare.kicker")}</p>
      <h1 className="mt-3 text-4xl font-semibold tracking-tight sm:text-5xl">{t("compare.title")}</h1>
      <p className="mt-4 max-w-xl text-sm leading-relaxed text-muted-foreground">
        {t("compare.lead", { max: MAX_COMPARED })}
      </p>

      <div className="mt-10">
        {ids.length < 2 ? (
          <div className="border border-border bg-card p-6">
            <p className="text-2xl font-semibold tracking-tight">{t("compare.pickTitle")}</p>
            <p className="mt-2 text-sm text-muted-foreground">
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
            <div role="alert" className="border border-border bg-card p-6">
              <p className="text-2xl font-semibold tracking-tight">{t("detail.notFound")}</p>
              <p className="mt-2 text-sm text-muted-foreground">
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
  const { t, programTitle } = useI18n()
  return (
    <div className="flex items-start justify-between gap-2">
      <Link to={`/programs/${program.program_id}`} className="font-semibold leading-snug hover:text-primary">
        {programTitle(program)}
      </Link>
      <button
        type="button"
        aria-label={t("compare.removeAria", { title: programTitle(program) })}
        onClick={() => onRemove(program.program_id)}
        className="shrink-0 rounded p-1 text-muted-foreground hover:bg-secondary hover:text-foreground"
      >
        <X className="size-4" />
      </button>
    </div>
  )
}

function Comparison({ programs, onRemove }: { programs: ComparedProgram[]; onRemove: (id: string) => void }) {
  const i18n = useI18n()
  const { t } = i18n
  return (
    <>
      <table className="hidden w-full table-fixed border-collapse text-sm sm:table">
        <caption className="sr-only">{t("compare.caption")}</caption>
        <thead>
          <tr className="border-b border-border">
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
            <tr key={row.label} className="border-b border-border">
              <th scope="row" className={`py-3 pr-4 text-left align-top font-normal ${labelClass}`}>
                {t(row.label)}
              </th>
              {programs.map((program) => (
                <td key={program.program_id} className="py-3 pr-4 align-top break-words">
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
          <section key={row.label} aria-label={t(row.label)}>
            <h2 className={labelClass}>{t(row.label)}</h2>
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
    </>
  )
}
