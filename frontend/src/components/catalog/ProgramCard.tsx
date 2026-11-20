import { Link } from "react-router-dom"
import type { DegreeLevel, Program } from "@/api/types"
import { CompareToggle } from "@/components/compare/CompareToggle"
import { useI18n } from "@/i18n"
import { cn } from "@/lib/utils"

const DEGREE_TILE: Record<DegreeLevel, string> = {
  bachelor: "bg-field",
  master: "bg-glacier",
  phd: "bg-ochre",
}

// Three fixed lines on every tile: title, degree · language · code, one hard fact.
// A programme whose deadline is not published is an outline tile, not a solid one.
export function ProgramCard({ program }: { program: Program }) {
  const { t, degree, languages, deadline, tuitionKzt, programTitle } = useI18n()
  const title = programTitle(program)
  const published = Boolean(program.deadline_local)

  return (
    <article
      className={cn(
        "group relative flex min-w-0 flex-col border-2 p-5 transition-colors duration-200 sm:p-6",
        published ? "border-transparent bg-card hover:border-primary" : "border-dashed border-input bg-transparent hover:border-primary",
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <h2 className="min-w-0 text-[1.75rem] leading-[0.95] font-extrabold uppercase">
          <Link to={`/programs/${program.program_id}`} className="after:absolute after:inset-0 group-hover:text-primary">
            {title}
          </Link>
        </h2>
        <CompareToggle programId={program.program_id} title={title} className="shrink-0" />
      </div>
      <p className="mt-3 flex items-center gap-2 text-[0.9375rem] text-muted-foreground">
        <span aria-hidden="true" className={cn("size-2.5 shrink-0", DEGREE_TILE[program.degree_level])} />
        <span>
          {degree(program.degree_level)} · {languages(program.language)} · <span className="tabular">{program.program_id}</span>
        </span>
      </p>
      <p className="tabular mt-auto flex flex-col gap-1 border-t border-border pt-4 text-[0.9375rem] sm:flex-row sm:flex-wrap sm:justify-between sm:gap-x-4">
        <span className={cn(published ? "font-semibold" : "font-medium text-terracotta")}>
          {t("card.localDeadline", { value: deadline(program.deadline_local) })}
        </span>
        <span className="text-muted-foreground">{t("card.localTuition", { value: tuitionKzt(program.tuition_per_ects_kzt) })}</span>
      </p>
    </article>
  )
}
