import { Link } from "react-router-dom"
import type { Program } from "@/api/types"
import { DEGREE_LABELS, LANGUAGE_LABELS } from "@/lib/constants"

export function ProgramCard({ program }: { program: Program }) {
  return (
    <Link
      to={`/programs/${program.program_id}`}
      className="group block border border-border bg-card p-5 transition-colors hover:border-primary/40"
    >
      <p className="text-[11px] tracking-[0.16em] text-muted-foreground uppercase">
        {DEGREE_LABELS[program.degree_level]} · {LANGUAGE_LABELS[program.language]}
      </p>
      <h2 className="mt-2 font-serif text-2xl leading-tight group-hover:text-primary">{program.title}</h2>
      <p className="mt-3 text-sm text-muted-foreground">{program.faculty}</p>
      <div className="mt-6 flex items-end justify-between gap-4 text-xs text-muted-foreground">
        <span>Deadline {program.application_deadline}</span>
        <span className="text-right">{program.tuition_fee}</span>
      </div>
    </Link>
  )
}
