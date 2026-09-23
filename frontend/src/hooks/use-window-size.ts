import { useEffect, useState } from "react"

function read() {
  return { width: window.innerWidth, height: window.innerHeight }
}

export function useWindowSize() {
  const [size, setSize] = useState(read)

  useEffect(() => {
    const onResize = () => setSize(read())
    window.addEventListener("resize", onResize)
    return () => window.removeEventListener("resize", onResize)
  }, [])

  return size
}
