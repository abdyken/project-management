import { Link } from "react-router-dom"
import type { Program } from "@/api/types"
import { CompareToggle } from "@/components/compare/CompareToggle"
import { useI18n } from "@/i18n"

export function ProgramCard({ program }: { program: Program }) {
  const { t, degree, languages, deadline, tuitionKzt } = useI18n()
  return (
    <article className="group relative border border-border bg-card p-5 transition-colors hover:border-primary/40">
      <div className="flex items-start justify-between gap-3">
        <p className="text-[11px] tracking-[0.16em] text-muted-foreground uppercase">
          {degree(program.degree_level)} · {languages(program.language)}
        </p>
        <CompareToggle programId={program.program_id} title={program.title} className="-mt-1 -mr-1 shrink-0" />
      </div>
      <h2 className="mt-2 text-2xl font-semibold leading-tight tracking-tight group-hover:text-primary">
        <Link to={`/programs/${program.program_id}`} className="after:absolute after:inset-0">
          {program.title}
        </Link>
      </h2>
      <p className="mt-3 text-sm text-muted-foreground">{program.faculty}</p>
      <div className="mt-6 flex flex-wrap items-end justify-between gap-x-4 gap-y-1 text-xs text-muted-foreground">
        <span>{t("card.localDeadline", { value: deadline(program.deadline_local) })}</span>
        <span className="text-right">{t("card.localTuition", { value: tuitionKzt(program.tuition_per_ects_kzt) })}</span>
      </div>
    </article>
  )
}
