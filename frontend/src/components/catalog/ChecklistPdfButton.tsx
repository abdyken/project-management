import { useMutation } from "@tanstack/react-query"
import { downloadChecklist } from "@/api/applicant"
import { useApplicantT } from "@/applicant/i18n"
import { Button } from "@/components/ui/button"

export function ChecklistPdfButton({ path }: { path: string }) {
  const t = useApplicantT()
  const download = useMutation({ mutationFn: () => downloadChecklist(path) })
  return (
    <div>
      <Button variant="outline" disabled={download.isPending} onClick={() => download.mutate()}>
        {download.isPending ? t("working") : t("pdf")}
      </Button>
      {download.isError && (
        <p role="alert" className="mt-2 text-sm text-destructive">
          {t("error")}
        </p>
      )}
    </div>
  )
}
