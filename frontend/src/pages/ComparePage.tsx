import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { X } from "lucide-react"
import { useEffect } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { isNotFound } from "@/api/errors"
import { comparePrograms } from "@/api/programs"
import type { ComparedProgram } from "@/api/types"
import { ConnectionError } from "@/components/common/ConnectionError"
import { Button } from "@/components/ui/button"
import { DEGREE_LABELS } from "@/lib/constants"
import { formatDeadline, formatTuitionInternational, formatTuitionLocal } from "@/lib/utils"
import { MAX_COMPARED, useCompareStore } from "@/store/compare"

const labelClass = "text-[11px] tracking-[0.14em] text-muted-foreground uppercase"

function documents(count: number) {
  if (count === 0) return "Not published"
  return count === 1 ? "1 document" : `${count} documents`
}

const ROWS: { label: string; value: (program: ComparedProgram) => string }[] = [
  { label: "Degree", value: (program) => `${DEGREE_LABELS[program.degree_level]} · ${program.program_id}` },
  { label: "School", value: (program) => program.faculty },
  { label: "Language", value: (program) => program.language },
  { label: "Tuition, local", value: (program) => formatTuitionLocal(program.tuition_per_ects_kzt) },
  { label: "Tuition, international", value: (program) => formatTuitionInternational(program.tuition_per_ects_usd) },
  { label: "Deadline, local", value: (program) => formatDeadline(program.deadline_local) },
  { label: "Deadline, international", value: (program) => formatDeadline(program.deadline_international) },
  { label: "Documents, local", value: (program) => documents(program.documents_local) },
  { label: "Documents, international", value: (program) => documents(program.documents_international) },
]

function readIds(params: URLSearchParams) {
  const raw = params.get("ids")
  if (raw === null) return null
  return [...new Set(raw.split(",").map((id) => id.trim()).filter(Boolean))].slice(0, MAX_COMPARED)
}

export function ComparePage() {
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
        ← Programs
      </Link>
      <p className={`mt-6 ${labelClass}`}>Comparison</p>
      <h1 className="mt-3 text-4xl font-semibold tracking-tight sm:text-5xl">Compare programs</h1>
      <p className="mt-4 max-w-xl text-sm leading-relaxed text-muted-foreground">
        Up to {MAX_COMPARED} programs side by side, from the admissions catalogue. Confirm fees and deadlines with the
        Admissions Office before you apply.
      </p>

      <div className="mt-10">
        {ids.length < 2 ? (
          <div className="border border-border bg-card p-6">
            <p className="text-2xl font-semibold tracking-tight">Pick two or three programs</p>
            <p className="mt-2 text-sm text-muted-foreground">
              {ids.length === 1
                ? "One program is selected. Add another one with Compare in the catalogue."
                : "Use Compare on the programs you are interested in."}
            </p>
            <Button asChild className="mt-5">
              <Link to="/programs">Open the catalogue</Link>
            </Button>
          </div>
        ) : null}

        {ids.length >= 2 && shown.length < 2 && query.isFetching ? <p className="text-sm text-muted-foreground">Loading programs…</p> : null}

        {ids.length >= 2 && query.isError ? (
          isNotFound(query.error) ? (
            <div role="alert" className="border border-border bg-card p-6">
              <p className="text-2xl font-semibold tracking-tight">Program not found</p>
              <p className="mt-2 text-sm text-muted-foreground">
                One of the selected programs is no longer in the catalogue.
              </p>
              <Button className="mt-5" onClick={clearAll}>
                Start a new comparison
              </Button>
            </div>
          ) : (
            <ConnectionError
              message="The comparison could not be loaded."
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
  return (
    <div className="flex items-start justify-between gap-2">
      <Link to={`/programs/${program.program_id}`} className="font-semibold leading-snug hover:text-primary">
        {program.title}
      </Link>
      <button
        type="button"
        aria-label={`Remove ${program.title} from comparison`}
        onClick={() => onRemove(program.program_id)}
        className="shrink-0 rounded p-1 text-muted-foreground hover:bg-secondary hover:text-foreground"
      >
        <X className="size-4" />
      </button>
    </div>
  )
}

function Comparison({ programs, onRemove }: { programs: ComparedProgram[]; onRemove: (id: string) => void }) {
  return (
    <>
      <table className="hidden w-full table-fixed border-collapse text-sm sm:table">
        <caption className="sr-only">Programs compared side by side</caption>
        <thead>
          <tr className="border-b border-border">
            <th scope="col" className="w-44 py-3 pr-4 text-left">
              <span className="sr-only">Field</span>
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
                {row.label}
              </th>
              {programs.map((program) => (
                <td key={program.program_id} className="py-3 pr-4 align-top break-words">
                  {row.value(program)}
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
          <section key={row.label} aria-label={row.label}>
            <h2 className={labelClass}>{row.label}</h2>
            <dl className="mt-2 space-y-1.5 text-sm">
              {programs.map((program) => (
                <div key={program.program_id} className="grid grid-cols-[minmax(0,2fr)_minmax(0,3fr)] gap-3">
                  <dt className="text-muted-foreground break-words">{program.title}</dt>
                  <dd className="break-words">{row.value(program)}</dd>
                </div>
              ))}
            </dl>
          </section>
        ))}
      </div>
    </>
  )
}
