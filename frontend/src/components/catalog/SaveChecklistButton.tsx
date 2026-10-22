import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Link, useNavigate } from "react-router-dom"
import { isApiError } from "@/api/errors"
import { saveProgram } from "@/api/applicant"
import type { ApplicantType } from "@/api/types"
import { useApplicantT } from "@/applicant/i18n"
import { SAVED_PROGRAMS_KEY } from "@/applicant/session"
import { Button } from "@/components/ui/button"

export function SaveChecklistButton({
  programId,
  applicantType,
}: {
  programId: string
  applicantType: ApplicantType
}) {
  const t = useApplicantT()
  const navigate = useNavigate()
  const cache = useQueryClient()
  const save = useMutation({
    mutationFn: () => saveProgram(programId, applicantType),
    onSuccess: () => {
      void cache.invalidateQueries({ queryKey: SAVED_PROGRAMS_KEY })
      navigate("/account")
    },
    onError: (error) => {
      if (isApiError(error) && error.status === 401)
        navigate(
          `/account/login?next=${encodeURIComponent(`/programs/${programId}?applicant=${applicantType}`)}`,
        )
    },
  })
  return (
    <div>
      <Button variant="outline" onClick={() => save.mutate()} disabled={save.isPending}>
        {save.isPending ? t("working") : t("save")}
      </Button>
      {save.isError && !(isApiError(save.error) && save.error.status === 401) && (
        <p role="alert" className="mt-2 text-sm text-destructive">
          {isApiError(save.error) && save.error.code === "ACCOUNTS_UNAVAILABLE"
            ? t("unavailable")
            : t("error")}{" "}
          <Link className="underline" to="/account">
            {t("account")}
          </Link>
        </p>
      )}
    </div>
  )
}
