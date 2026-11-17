import { Navigate, Route, Routes } from "react-router-dom"
import { StaffLayout } from "@/components/staff/StaffLayout"
import { StaffRequestsPage } from "@/pages/guidance/RequestsPage"
import { StaffDashboardPage } from "@/pages/staff/StaffDashboardPage"
import { StaffFaqEditPage } from "@/pages/staff/StaffFaqEditPage"
import { StaffFaqListPage } from "@/pages/staff/StaffFaqListPage"
import { StaffHomePage } from "@/pages/staff/StaffHomePage"
import { StaffInboxPage } from "@/pages/staff/StaffInboxPage"
import { StaffLoginPage } from "@/pages/staff/StaffLoginPage"
import { StaffProgramEditPage } from "@/pages/staff/StaffProgramEditPage"
import { StaffProgramsPage } from "@/pages/staff/StaffProgramsPage"

export default function StaffArea() {
  return (
    <Routes>
      <Route path="login" element={<StaffLoginPage />} />
      <Route element={<StaffLayout />}>
        <Route path="requests" element={<StaffRequestsPage />} />
        <Route index element={<StaffHomePage />} />
        <Route path="faq" element={<StaffFaqListPage />} />
        <Route path="faq/new" element={<StaffFaqEditPage />} />
        <Route path="faq/:faqId" element={<StaffFaqEditPage />} />
        <Route path="inbox" element={<StaffInboxPage />} />
        <Route path="programs" element={<StaffProgramsPage />} />
        <Route path="programs/new" element={<StaffProgramEditPage />} />
        <Route path="programs/:programId" element={<StaffProgramEditPage />} />
        <Route path="dashboard" element={<StaffDashboardPage />} />
        <Route path="*" element={<Navigate to="/staff" replace />} />
      </Route>
    </Routes>
  )
}
