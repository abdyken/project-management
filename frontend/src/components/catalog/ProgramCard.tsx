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

// Three fixed lines on every tile: the full title (never cut), degree · language · code, and one
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
      <h2 className="min-w-0 text-[1.5rem] leading-[1] font-extrabold uppercase sm:text-[1.75rem]">
        <Link to={`/programs/${program.program_id}`} className="after:absolute after:inset-0 group-hover:text-primary">
          {title}
        </Link>
      </h2>
      <p className="mt-3 mb-5 truncate text-[0.9375rem] text-muted-foreground">
        {degree(program.degree_level)} · {languages(program.language)} · <span className="tabular">{program.program_id}</span>
      </p>
      <div className="mt-auto flex flex-wrap items-center justify-between gap-x-4 gap-y-3 border-t border-border pt-4">
        <p className="tabular text-[0.9375rem] font-semibold">
          {published
            ? t("card.localDeadline", { value: deadline(program.deadline_local) })
            : t("card.localTuition", { value: tuitionKzt(program.tuition_per_ects_kzt) })}
        </p>
        <CompareToggle programId={program.program_id} title={title} className="shrink-0" />
      </div>
    </article>
  )
}
