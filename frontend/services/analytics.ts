export interface GroupCount {
  key: string;
  count: number;
}

export interface DailyCount {
  date: string;
  count: number;
}

export interface WorkflowStats {
  total_executions: number;
  successful_executions: number;
  success_rate: number;
}

export interface DashboardMetrics {
  total_tickets: number;
  open_tickets: number;
  closed_tickets: number;
  tickets_today: number;
  tickets_this_week: number;
  tickets_this_month: number;
  avg_resolution_seconds: number | null;
  avg_first_response_seconds: number | null;
  avg_reply_seconds: number | null;
  ai_analyses_performed: number;
  workflow_stats: WorkflowStats;
}

export interface ChartsBundle {
  tickets_by_priority: GroupCount[];
  tickets_by_status: GroupCount[];
  tickets_by_source: GroupCount[];
  tickets_by_team: GroupCount[];
  tickets_by_agent: GroupCount[];
  sentiment_distribution: GroupCount[];
  daily_tickets: DailyCount[];
}

export interface AnalyticsFilterParams {
  range?: "today" | "7d" | "30d";
  date_from?: string;
  date_to?: string;
  team_id?: string;
  agent_id?: string;
  priority?: string;
  status?: string;
  source?: string;
}

const API_BASE_URL = `${process.env.NEXT_PUBLIC_API_URL ?? ""}/api/v1`;

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed with status ${res.status}`);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

function toQueryString(params: Record<string, string | undefined>): string {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") qs.set(k, v);
  });
  const s = qs.toString();
  return s ? `?${s}` : "";
}

export const analyticsApi = {
  dashboard: (params: AnalyticsFilterParams = {}) =>
    request<DashboardMetrics>(`/analytics/dashboard${toQueryString(params as Record<string, string>)}`),

  charts: (params: AnalyticsFilterParams = {}) =>
    request<ChartsBundle>(`/analytics/charts${toQueryString(params as Record<string, string>)}`),

  exportUrl: (format: "csv" | "json", params: AnalyticsFilterParams = {}) =>
    `${API_BASE_URL}/analytics/export${toQueryString({ ...params, format } as Record<string, string>)}`,
};