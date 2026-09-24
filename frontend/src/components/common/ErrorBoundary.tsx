import { Component, type ReactNode } from "react"
import { Button } from "@/components/ui/button"

type ErrorBoundaryProps = { children: ReactNode }
type ErrorBoundaryState = { failed: boolean }

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { failed: false }

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { failed: true }
  }

  render() {
    if (!this.state.failed) return this.props.children
    return (
      <div role="alert" className="mx-auto max-w-5xl px-4 py-16">
        <p className="text-3xl font-semibold tracking-tight">Something went wrong</p>
        <p className="mt-2 text-sm text-muted-foreground">
          This page could not be displayed. Reload it, or contact the admissions office if it keeps happening.
        </p>
        <Button className="mt-5" onClick={() => window.location.reload()}>
          Reload page
        </Button>
      </div>
    )
  }
}
