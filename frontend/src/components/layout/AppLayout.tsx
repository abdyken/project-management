import { Outlet, useLocation } from "react-router-dom"
import { ChatWidget } from "@/components/chat/ChatWidget"
import { ErrorBoundary } from "@/components/common/ErrorBoundary"
import { SiteFooter } from "@/components/layout/SiteFooter"
import { SiteHeader } from "@/components/layout/SiteHeader"

export function AppLayout() {
  const location = useLocation()

  return (
    <div className="flex min-h-dvh flex-col">
      <SiteHeader />
      <main className="flex-1 min-h-[60vh]">
        <ErrorBoundary key={location.pathname}>
          <Outlet />
        </ErrorBoundary>
      </main>
      <SiteFooter />
      <ChatWidget />
    </div>
  )
}
