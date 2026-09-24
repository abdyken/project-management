import { useEffect, useState } from "react"

export function viewportSize() {
  return { width: document.documentElement.clientWidth, height: document.documentElement.clientHeight }
}

export function useWindowSize() {
  const [size, setSize] = useState(viewportSize)

  useEffect(() => {
    const onResize = () => setSize(viewportSize())
    window.addEventListener("resize", onResize)
    return () => window.removeEventListener("resize", onResize)
  }, [])

  return size
}
