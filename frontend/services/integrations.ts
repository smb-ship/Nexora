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

export interface IncomingWebhookKey {
  id: string;
  name: string;
  is_active: boolean;
  created_at: string;
  last_used_at: string | null;
}

export interface IncomingWebhookKeyCreated extends IncomingWebhookKey {
  plaintext_key: string;
}

export function listWebhookKeys(): Promise<IncomingWebhookKey[]> {
  return request<IncomingWebhookKey[]>("/integrations/webhook-keys");
}

export function createWebhookKey(name: string): Promise<IncomingWebhookKeyCreated> {
  return request<IncomingWebhookKeyCreated>("/integrations/webhook-keys", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export function revokeWebhookKey(id: string): Promise<void> {
  return request<void>(`/integrations/webhook-keys/${id}`, { method: "DELETE" });
}