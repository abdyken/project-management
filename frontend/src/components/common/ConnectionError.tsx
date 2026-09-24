import { Button } from "@/components/ui/button"

type ConnectionErrorProps = {
  message: string
  retrying: boolean
  onRetry: () => void
}

export function ConnectionError({ message, retrying, onRetry }: ConnectionErrorProps) {
  return (
    <div role="alert" className="border border-border bg-card p-6">
      <p className="text-2xl font-semibold tracking-tight">Connection error</p>
      <p className="mt-2 text-sm text-muted-foreground">{message}</p>
      <Button className="mt-5" onClick={onRetry} disabled={retrying}>
        {retrying ? "Trying again…" : "Try again"}
      </Button>
    </div>
  )
}
