import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import type { ComponentProps } from "react"
import { cn } from "@/lib/utils"

// Square mosaic buttons. "ochre" is the one primary action per view (Apply, Search);
// "default" is the turquoise working button; "outline", "ghost" and "link" step down.
// A trailing lucide ArrowRight inside any button slides 3px on hover.
const buttonVariants = cva(
  [
    "group/button inline-flex shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-none font-semibold",
    "transition-[background-color,color,border-color,transform] duration-200 ease-out active:translate-y-px",
    "disabled:pointer-events-none disabled:opacity-45 outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
    "[&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4",
    "[&_svg.lucide-arrow-right]:transition-transform [&_svg.lucide-arrow-right]:duration-200 hover:[&_svg.lucide-arrow-right]:translate-x-[3px]",
  ].join(" "),
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-field-deep",
        ochre: "bg-ochre text-ink hover:bg-ochre-hover",
        gold: "bg-ochre text-ink hover:bg-ochre-hover",
        outline: "border-2 border-primary bg-transparent text-primary hover:bg-primary hover:text-primary-foreground",
        ghost: "text-foreground hover:bg-secondary",
        link: "h-auto px-0 text-primary underline decoration-2 underline-offset-4 hover:decoration-ochre",
        onField: "border-2 border-field-foreground bg-transparent text-field-foreground hover:bg-field-foreground hover:text-field",
      },
      size: {
        default: "h-11 px-5 text-[0.9375rem]",
        sm: "h-9 px-3 text-sm",
        lg: "min-h-12 whitespace-normal px-6 py-2 text-left font-display text-lg leading-tight font-bold tracking-[0.04em] uppercase",
        icon: "size-11",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
)

// ComponentProps includes `ref` (React 19 passes it as a prop).
type ButtonProps = ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean
  }

function Button({ className, variant, size, asChild = false, ...props }: ButtonProps) {
  const Comp = asChild ? Slot : "button"
  return <Comp className={cn(buttonVariants({ variant, size, className }))} {...props} />
}

export { Button }
