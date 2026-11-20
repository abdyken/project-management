import { Link } from "react-router-dom"
import type { Program } from "@/api/types"
import { CompareToggle } from "@/components/compare/CompareToggle"
import { useI18n } from "@/i18n"
import { cn } from "@/lib/utils"

// Three fixed lines on every card: the full title (never cut), degree · language · code,
// and the deciding fact (local deadline). An unpublished deadline is said in words, muted.
export function ProgramCard({ program }: { program: Program }) {
  const { t, degree, languages, deadline, programTitle } = useI18n()
  const title = programTitle(program)
  const published = Boolean(program.deadline_local)

  return (
    <article
      className="group relative flex h-full min-w-0 flex-col border border-border bg-card p-5 transition-[border-color,translate] duration-200 ease-out hover:-translate-y-1 hover:border-primary motion-reduce:hover:translate-y-0 sm:p-6"
    >
      <h2 className="min-w-0 text-[1.375rem] leading-[1.18] font-medium sm:text-[1.5rem]">
        <Link to={`/programs/${program.program_id}`} className="after:absolute after:inset-0 group-hover:text-primary">
          {title}
        </Link>
      </h2>
      <p className="mt-3 mb-5 truncate text-[0.9375rem] text-muted-foreground">
        {degree(program.degree_level)} · {languages(program.language)} · <span className="tabular">{program.program_id}</span>
      </p>
      <div className="mt-auto flex flex-wrap items-center justify-between gap-x-4 gap-y-3 border-t border-border pt-4">
        <p className={cn("tabular text-[0.9375rem]", published ? "font-semibold" : "text-muted-foreground")}>
          {t("card.localDeadline", { value: deadline(program.deadline_local) })}
        </p>
        <CompareToggle programId={program.program_id} title={title} className="shrink-0" />
      </div>
    </article>
  )
}
