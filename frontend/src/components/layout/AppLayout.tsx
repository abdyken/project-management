import { Outlet } from "react-router-dom"
import { ChatWidget } from "@/components/chat/ChatWidget"
import { SiteFooter } from "@/components/layout/SiteFooter"
import { SiteHeader } from "@/components/layout/SiteHeader"

export function AppLayout() {
  return (
    <div className="flex min-h-dvh flex-col">
      <SiteHeader />
      <main className="flex-1 min-h-[60vh]">
        <Outlet />
      </main>
      <SiteFooter />
      <ChatWidget />
    </div>
  )
}
