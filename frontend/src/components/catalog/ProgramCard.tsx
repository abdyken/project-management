import { Link } from "react-router-dom"
import type { Program } from "@/api/types"
import { CompareToggle } from "@/components/compare/CompareToggle"
import { useI18n } from "@/i18n"
import { deadlineStatus } from "@/lib/dates"
import { cn } from "@/lib/utils"

// A ruled row in the finder: the full title (never cut), then degree · language · code and the
// deciding fact (local deadline) on one quiet line. A passed or unpublished deadline is said in
// words, muted. `hideDeadline` when the list states the shared deadline once above the group.
// Compare is a quiet text toggle; the whole row is the link to the program.
export function ProgramCard({ program, headingLevel = 2, hideDeadline = false }: { program: Program; headingLevel?: 2 | 3; hideDeadline?: boolean }) {
  const Heading = headingLevel === 3 ? "h3" : "h2"
  const { t, degree, languages, deadlineWithStatus, programTitle } = useI18n()
  const title = programTitle(program)
  const open = deadlineStatus(program.deadline_local) === "upcoming"

  return (
    <article className="group relative flex min-w-0 items-center gap-4 border-b border-border py-4 transition-colors duration-200 hover:bg-secondary/60 sm:-mx-2 sm:px-2">
      <div className="min-w-0 flex-1">
        <Heading className="min-w-0 font-heading text-[1.25rem] leading-[1.2] font-medium sm:text-[1.375rem]">
          <Link to={`/programs/${program.program_id}`} className="after:absolute after:inset-0 group-hover:text-primary">
            {title}
          </Link>
        </Heading>
        <p className="mt-1 text-[0.9375rem] text-muted-foreground">
          {degree(program.degree_level)} · {program.language ? `${languages(program.language)} · ` : null}
          <span className="tabular">{program.program_id}</span>
          {hideDeadline ? null : (
            <>
              {" · "}
              <span className={cn("tabular", open && "font-semibold text-foreground")}>
                {t("card.localDeadline", { value: deadlineWithStatus(program.deadline_local) })}
              </span>
            </>
          )}
        </p>
      </div>
      <CompareToggle programId={program.program_id} title={title} quiet className="shrink-0" />
    </article>
  )
}
