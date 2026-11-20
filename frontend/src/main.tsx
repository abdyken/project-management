import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import App from "./App.tsx"
import "@fontsource/golos-text/400.css"
import "@fontsource/golos-text/500.css"
import "@fontsource/golos-text/600.css"
import "@fontsource/golos-text/700.css"
import "@fontsource/fira-sans-extra-condensed/600.css"
import "@fontsource/fira-sans-extra-condensed/700.css"
import "@fontsource/fira-sans-extra-condensed/800.css"
import "./index.css"

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
