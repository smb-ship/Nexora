// NOTE: this fetch wrapper is a reasonable default (cookie-based JWT via
// credentials: "include"), not copied from an existing service file — I
// didn't have one to match against. Adjust API_BASE_URL / the request()
// helper if your other services do this differently.
import type { WorkflowRule, WorkflowRuleInput, WorkflowExecutionLog } from "@/types/workflow";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

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

export const workflowsService = {
  list: (isActive?: boolean) => {
    const query = isActive !== undefined ? `?is_active=${isActive}` : "";
    return request<WorkflowRule[]>(`/workflows/${query}`);
  },
  get: (id: string) => request<WorkflowRule>(`/workflows/${id}`),
  create: (payload: WorkflowRuleInput) =>
    request<WorkflowRule>("/workflows/", { method: "POST", body: JSON.stringify(payload) }),
  update: (id: string, payload: Partial<WorkflowRuleInput>) =>
    request<WorkflowRule>(`/workflows/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  toggle: (id: string) => request<WorkflowRule>(`/workflows/${id}/toggle`, { method: "POST" }),
  remove: (id: string) => request<void>(`/workflows/${id}`, { method: "DELETE" }),
  logs: (id: string) => request<WorkflowExecutionLog[]>(`/workflows/${id}/logs`),
  processIdle: () => request<{ tickets_checked: number }>("/workflows/process-idle", { method: "POST" }),
};