import { Link } from "react-router-dom"
import type { Program } from "@/api/types"
import { CompareToggle } from "@/components/compare/CompareToggle"
import { useI18n } from "@/i18n"
import { deadlineStatus } from "@/lib/dates"
import { cn } from "@/lib/utils"

// Three fixed lines on every card: the full title (never cut), degree · language · code,
// and the deciding fact (local deadline). A passed or unpublished deadline is said in words, muted.
// `hideDeadline` when the list states the shared deadline once above the group.
export function ProgramCard({ program, headingLevel = 2, hideDeadline = false }: { program: Program; headingLevel?: 2 | 3; hideDeadline?: boolean }) {
  const Heading = headingLevel === 3 ? "h3" : "h2"
  const { t, degree, languages, deadlineWithStatus, programTitle } = useI18n()
  const title = programTitle(program)
  const open = deadlineStatus(program.deadline_local) === "upcoming"

  return (
    <article
      className="group relative flex h-full min-w-0 flex-col border border-border bg-card p-5 transition-[border-color,translate] duration-200 ease-out hover:-translate-y-1 hover:border-primary motion-reduce:hover:translate-y-0 sm:p-6"
    >
      <Heading className="min-w-0 font-heading text-[1.375rem] leading-[1.18] font-medium sm:text-[1.5rem]">
        <Link to={`/programs/${program.program_id}`} className="after:absolute after:inset-0 group-hover:text-primary">
          {title}
        </Link>
      </Heading>
      <p className="mt-3 mb-5 truncate text-[0.9375rem] text-muted-foreground">
        {degree(program.degree_level)} · {program.language ? `${languages(program.language)} · ` : null}
        <span className="tabular">{program.program_id}</span>
      </p>
      <div className={cn("mt-auto flex flex-wrap items-center gap-x-4 gap-y-3 border-t border-border pt-4", hideDeadline ? "justify-end" : "justify-between")}>
        {hideDeadline ? null : (
          <p className={cn("tabular text-[0.9375rem]", open ? "font-semibold" : "text-muted-foreground")}>
            {t("card.localDeadline", { value: deadlineWithStatus(program.deadline_local) })}
          </p>
        )}
        <CompareToggle programId={program.program_id} title={title} className="shrink-0" />
      </div>
    </article>
  )
}
