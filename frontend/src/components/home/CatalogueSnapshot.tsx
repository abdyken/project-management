import { useQuery } from "@tanstack/react-query"
import { MapPin } from "lucide-react"
import { Link } from "react-router-dom"
import { allProgramsQuery, programLanguages } from "@/api/programs"
import type { Program } from "@/api/types"
import { ADMISSIONS_CONTACT } from "@/lib/constants"
import { formatDeadline } from "@/lib/utils"

function nextDeadline(programs: Program[]) {
  const today = new Date().toISOString().slice(0, 10)
  const upcoming = programs
    .flatMap((program) => [program.deadline_local, program.deadline_international])
    .filter((deadline): deadline is string => deadline !== null && deadline >= today)
    .sort()
  return upcoming[0] ?? null
}

function Stat({ value, label }: { value: number; label: string }) {
  return (
    <div className="flex flex-col-reverse">
      <dt className="mt-1 text-xs text-muted-foreground">{label}</dt>
      <dd className="text-4xl font-semibold tracking-tight">{value}</dd>
    </div>
  )
}

export function CatalogueSnapshot() {
  const { data, isError } = useQuery(allProgramsQuery)
  const programs = data?.programs ?? []
  const deadline = nextDeadline(programs)

  return (
    <aside className="border border-border bg-card p-6 sm:p-8" aria-label="Catalogue at a glance">
      <p className="text-[11px] tracking-[0.12em] text-muted-foreground uppercase">Catalogue at a glance</p>
      {data ? (
        <>
          <dl className="mt-6 grid grid-cols-3 gap-4">
            <Stat value={data.total} label="programs" />
            <Stat value={new Set(programs.map((program) => program.faculty)).size} label="schools" />
            <Stat value={new Set(programs.flatMap(programLanguages)).size} label="languages" />
          </dl>
          {deadline ? (
            <p className="mt-6 border-t border-border pt-5 text-sm">
              Next application deadline
              <span className="mt-1 block text-lg font-semibold">{formatDeadline(deadline)}</span>
            </p>
          ) : null}
          <Link to="/programs" className="mt-5 inline-block text-sm underline underline-offset-4">
            Browse all programs
          </Link>
        </>
      ) : isError ? (
        <p className="mt-6 text-sm text-muted-foreground">
          The catalogue is unavailable right now.{" "}
          <Link to="/programs" className="underline underline-offset-4">
            Open the programs page
          </Link>{" "}
          to try again.
        </p>
      ) : (
        <div className="mt-6 h-24 animate-pulse bg-secondary/60" aria-hidden />
      )}
      <p className="mt-6 flex gap-2 border-t border-border pt-5 text-sm text-muted-foreground">
        <MapPin className="mt-0.5 size-4 shrink-0 text-gold" aria-hidden />
        <span>
          {ADMISSIONS_CONTACT.name}
          <br />
          {ADMISSIONS_CONTACT.address}
        </span>
      </p>
    </aside>
  )
}
