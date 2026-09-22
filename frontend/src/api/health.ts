import { request } from "@/api/client"
import type { HealthResponse } from "@/api/types"

export function getHealth() {
  return request<HealthResponse>("/api/health")
}
