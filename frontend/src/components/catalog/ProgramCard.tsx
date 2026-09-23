import { Link } from "react-router-dom"
import type { Program } from "@/api/types"
import { DEGREE_LABELS } from "@/lib/constants"
import { formatDeadline, formatTuition } from "@/lib/utils"

export function ProgramCard({ program }: { program: Program }) {
  return (
    <Link
      to={`/programs/${program.program_id}`}
      className="group block border border-border bg-card p-5 transition-colors hover:border-primary/40"
    >
      <p className="text-[11px] tracking-[0.16em] text-muted-foreground uppercase">
        {DEGREE_LABELS[program.degree_level]} · {program.language}
      </p>
      <h2 className="mt-2 text-2xl font-semibold leading-tight tracking-tight group-hover:text-primary">{program.title}</h2>
      <p className="mt-3 text-sm text-muted-foreground">{program.faculty}</p>
      <div className="mt-6 flex flex-wrap items-end justify-between gap-x-4 gap-y-1 text-xs text-muted-foreground">
        <span>Local deadline: {formatDeadline(program.deadline_local)}</span>
        <span className="text-right">{formatTuition(program.tuition_per_ects_kzt, program.tuition_per_ects_usd)}</span>
      </div>
    </Link>
  )
}
