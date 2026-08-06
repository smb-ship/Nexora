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

export interface ChatMessage {
  id: string;
  sender_type: "visitor" | "agent" | "system";
  body: string;
  created_at: string;
}

export interface ChatConversation {
  id: string;
  status: "open" | "closed" | "converted";
  assigned_to: string | null;
  ticket_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChatConversationDetail extends ChatConversation {
  messages: ChatMessage[];
}

export interface ChatWidgetSettings {
  public_key: string;
  is_active: boolean;
  welcome_message: string;
}

export function getWidgetSettings(): Promise<ChatWidgetSettings> {
  return request<ChatWidgetSettings>("/chat/widget-settings");
}

export function listConversations(status?: string): Promise<ChatConversation[]> {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return request<ChatConversation[]>(`/chat/conversations${query}`);
}

export function getConversation(id: string): Promise<ChatConversationDetail> {
  return request<ChatConversationDetail>(`/chat/conversations/${id}`);
}

export function sendAgentReply(id: string, body: string): Promise<ChatMessage> {
  return request<ChatMessage>(`/chat/conversations/${id}/messages`, {
    method: "POST",
    body: JSON.stringify({ body }),
  });
}

export function convertToTicket(id: string): Promise<{ ticket_id: string }> {
  return request<{ ticket_id: string }>(`/chat/conversations/${id}/convert-to-ticket`, {
    method: "POST",
  });
}