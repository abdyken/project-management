import { Link } from "react-router-dom"
import type { DegreeLevel, Program } from "@/api/types"
import { CompareToggle } from "@/components/compare/CompareToggle"
import { useI18n } from "@/i18n"
import { cn } from "@/lib/utils"

const DEGREE_EDGE: Record<DegreeLevel, string> = {
  bachelor: "bg-field",
  master: "bg-glacier",
  phd: "bg-ochre",
}

// Three fixed lines on every tile: title (at most two lines), degree · language · code, and one
// deciding fact (the local deadline, or the tuition when the deadline is not published).
// The degree colour is the tile's top edge; an unpublished deadline makes an outline tile.
export function ProgramCard({ program }: { program: Program }) {
  const { t, degree, languages, deadline, tuitionKzt, programTitle } = useI18n()
  const title = programTitle(program)
  const published = Boolean(program.deadline_local)

  return (
    <article
      className={cn(
        "group relative flex h-full min-w-0 flex-col border-2 p-5 pt-6 transition-colors duration-200 sm:p-6 sm:pt-7",
        published ? "border-transparent bg-card hover:border-primary" : "border-dashed border-input bg-transparent hover:border-primary",
      )}
    >
      <span aria-hidden="true" className={cn("absolute inset-x-0 -top-0.5 h-1.5", DEGREE_EDGE[program.degree_level])} />
      <div className="flex items-start justify-between gap-4">
        <h2 className="line-clamp-2 min-h-[2em] min-w-0 text-[1.75rem] leading-[1] font-extrabold uppercase" title={title}>
          <Link to={`/programs/${program.program_id}`} className="after:absolute after:inset-0 group-hover:text-primary">
            {title}
          </Link>
        </h2>
        <CompareToggle programId={program.program_id} title={title} className="shrink-0" />
      </div>
      <p className="mt-3 truncate text-[0.9375rem] text-muted-foreground">
        {degree(program.degree_level)} · {languages(program.language)} · <span className="tabular">{program.program_id}</span>
      </p>
      <p className="tabular mt-auto border-t border-border pt-4 text-[0.9375rem] font-semibold">
        {published
          ? t("card.localDeadline", { value: deadline(program.deadline_local) })
          : t("card.localTuition", { value: tuitionKzt(program.tuition_per_ects_kzt) })}
      </p>
    </article>
  )
}
