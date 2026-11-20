import { Suspense } from "react"
import { Outlet, useLocation } from "react-router-dom"
import { ChatWidget } from "@/components/chat/ChatWidget"
import { ErrorBoundary } from "@/components/common/ErrorBoundary"
import { PageLoading } from "@/components/common/PageLoading"
import { CompareBar } from "@/components/compare/CompareBar"
import { SiteFooter } from "@/components/layout/SiteFooter"
import { SiteHeader } from "@/components/layout/SiteHeader"

export function AppLayout() {
  const location = useLocation()

  return (
    <div className="flex min-h-dvh flex-col">
      <SiteHeader />
      <main id="main" tabIndex={-1} className="min-h-[60vh] flex-1 outline-none">
        <ErrorBoundary key={location.pathname}>
          <Suspense fallback={<PageLoading />}>
            <Outlet />
          </Suspense>
        </ErrorBoundary>
      </main>
      <SiteFooter />
      <CompareBar />
      <ChatWidget />
    </div>
  )
}
