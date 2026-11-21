import type { ComponentProps } from "react"
import { cn } from "@/lib/utils"

// One container for every page: the header's 84rem frame and gutters, so every page starts at
// the same left edge as the logo. The width only limits the content inside, left-aligned:
// text = reading column (forms, guides), content = default pages, wide = finders and tables.
const WIDTHS = {
  text: "[&>*]:max-w-3xl",
  content: "[&>*]:max-w-6xl",
  wide: "",
} as const

type PageShellProps = ComponentProps<"div"> & {
  width?: keyof typeof WIDTHS
  // false when the page draws its own full-bleed bands
  padded?: boolean
}

export function PageShell({ width = "content", padded = true, className, ...props }: PageShellProps) {
  return (
    <div
      className={cn("mx-auto w-full max-w-[84rem] px-4 sm:px-6 lg:px-8", WIDTHS[width], padded && "pt-10 pb-20 sm:pt-14 sm:pb-24", className)}
      {...props}
    />
  )
}
