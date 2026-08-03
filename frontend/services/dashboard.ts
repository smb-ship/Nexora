import { analyticsApi, type DashboardMetrics, type ChartsBundle } from "./analytics";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed with status ${res.status}`);
  }
  return res.json();
}

export interface DashboardCounts {
  live_chat_conversations: number;
  knowledge_articles_published: number;
  automation_workflows_active: number;
  automation_workflows_total: number;
}

export interface RecentTicket {
  id: string;
  subject: string;
  status: string;
  priority: string;
  requester_name: string;
  assigned_to_name: string | null;
  created_at: string;
}

export interface RecentEvent {
  event_id: string;
  event_type: string;
  created_at: string;
  data: Record<string, unknown>;
}

export interface DashboardSummary {
  metrics: DashboardMetrics;
  charts: ChartsBundle;
  counts: DashboardCounts;
  recent_tickets: RecentTicket[];
  recent_events: RecentEvent[];
}

// Re-exported so dashboard/page.tsx has one import source rather than
// pulling from both services/analytics.ts and services/dashboard.ts.
export { analyticsApi };

export function getDashboardSummary(): Promise<DashboardSummary> {
  return request<DashboardSummary>("/analytics/dashboard-summary");
}