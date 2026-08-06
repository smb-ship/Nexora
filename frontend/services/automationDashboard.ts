const API_BASE = `${process.env.NEXT_PUBLIC_API_URL ?? ""}/api/v1`;

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Request failed (${res.status}): ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export interface ConnectedService {
  id: string;
  name: string;
  integration_type: string;
  target_url: string;
  is_active: boolean;
  event_types: string[];
  success_count: number;
  failed_count: number;
  last_delivery_at: string | null;
}

export interface EventFeedItem {
  event_id: string;
  event_type: string;
  data: Record<string, unknown>;
  created_at: string;
}

export interface AutomationDashboard {
  connected_services: ConnectedService[];
  pending_retries: number;
  deliveries_last_24h: number;
  failures_last_24h: number;
  recent_events: EventFeedItem[];
}

export function getAutomationDashboard(): Promise<AutomationDashboard> {
  return request<AutomationDashboard>("/automation-dashboard/");
}

export interface OutgoingWebhook {
  id: string;
  name: string;
  target_url: string;
  event_types: string[];
  integration_type: string;
  is_active: boolean;
  signing_secret: string;
  created_at: string;
  updated_at: string;
}

export function listWebhooks(): Promise<OutgoingWebhook[]> {
  return request<OutgoingWebhook[]>("/webhooks/");
}

export function createWebhook(payload: {
  name: string;
  target_url: string;
  event_types: string[];
  integration_type?: string;
}): Promise<OutgoingWebhook> {
  return request<OutgoingWebhook>("/webhooks/", { method: "POST", body: JSON.stringify(payload) });
}

export function updateWebhook(
  id: string,
  payload: Partial<{
    name: string;
    target_url: string;
    event_types: string[];
    integration_type: string;
    is_active: boolean;
  }>
): Promise<OutgoingWebhook> {
  return request<OutgoingWebhook>(`/webhooks/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteWebhook(id: string): Promise<void> {
  return request<void>(`/webhooks/${id}`, { method: "DELETE" });
}

export function processRetries(): Promise<{ retried: number }> {
  return request<{ retried: number }>("/webhooks/process-retries", { method: "POST" });
}

export interface WebhookDeliveryLog {
  id: string;
  webhook_id: string;
  event_type: string;
  event_id: string;
  status: "pending" | "success" | "failed" | "retrying";
  attempt_count: number;
  response_status_code: number | null;
  error_message: string | null;
  created_at: string;
  delivered_at: string | null;
  next_retry_at: string | null;
}

export function getDeliveries(webhookId: string): Promise<WebhookDeliveryLog[]> {
  return request<WebhookDeliveryLog[]>(`/webhooks/${webhookId}/deliveries`);
}