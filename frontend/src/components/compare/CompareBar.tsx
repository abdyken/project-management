import { X } from "lucide-react"
import { Link, useLocation } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { useI18n } from "@/i18n"
import { MAX_COMPARED, useCompareStore } from "@/store/compare"

export function CompareBar() {
  const { t } = useI18n()
  const ids = useCompareStore((state) => state.ids)
  const clear = useCompareStore((state) => state.clear)
  const location = useLocation()
  if (ids.length === 0 || location.pathname === "/compare") return null

  return (
    <div
      role="region"
      aria-label={t("compare.bar")}
      className="fixed bottom-4 left-4 z-40 flex max-w-[calc(100vw-6.5rem)] items-center gap-2 border border-border bg-background py-2 pr-2 pl-4 shadow-lg"
    >
      <p className="text-sm">
        {ids.length}/{MAX_COMPARED} <span className="hidden sm:inline">{t("compare.programsSelected")}</span>
      </p>
      {ids.length >= 2 ? (
        <Button asChild size="sm">
          <Link to={`/compare?ids=${ids.join(",")}`}>{t("compare.add")}</Link>
        </Button>
      ) : (
        <span className="text-xs text-muted-foreground">{t("compare.addOneMore")}</span>
      )}
      <button
        type="button"
        aria-label={t("compare.clear")}
        onClick={clear}
        className="rounded p-1 text-muted-foreground hover:bg-secondary hover:text-foreground"
      >
        <X className="size-4" />
      </button>
    </div>
  )
}
