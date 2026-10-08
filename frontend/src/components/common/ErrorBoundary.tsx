import { Component, type ReactNode } from "react"
import { Button } from "@/components/ui/button"
import { useI18n } from "@/i18n"

type ErrorBoundaryProps = { children: ReactNode }
type ErrorBoundaryState = { failed: boolean }

function PageError() {
  const { t } = useI18n()
  return (
    <div role="alert" className="mx-auto max-w-5xl px-4 py-16">
      <p className="text-3xl font-semibold tracking-tight">{t("error.pageTitle")}</p>
      <p className="mt-2 text-sm text-muted-foreground">{t("error.pageText")}</p>
      <Button className="mt-5" onClick={() => window.location.reload()}>
        {t("error.reload")}
      </Button>
    </div>
  )
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { failed: false }

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { failed: true }
  }

  render() {
    return this.state.failed ? <PageError /> : this.props.children
  }
}
