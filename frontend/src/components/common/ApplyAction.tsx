import { ArrowRight, ArrowUpRight } from "lucide-react"
import { Link } from "react-router-dom"
import { useFeatures } from "@/api/features"
import { Button } from "@/components/ui/button"

const OFFICIAL_APPLICATION_PORTAL = "https://admissions.sdu.edu.kz"

// The one ochre action: the online application when it is enabled, otherwise the official portal.
export function ApplyAction({ label, className }: { label: string; className?: string }) {
  const features = useFeatures()
  return features.data?.applications ? (
    <Button asChild variant="ochre" size="lg" className={className}>
      <Link to="/account/applications">
        {label}
        <ArrowRight aria-hidden="true" />
      </Link>
    </Button>
  ) : (
    <Button asChild variant="ochre" size="lg" className={className}>
      <a href={OFFICIAL_APPLICATION_PORTAL} target="_blank" rel="noreferrer">
        {label}
        <ArrowUpRight aria-hidden="true" />
      </a>
    </Button>
  )
}
