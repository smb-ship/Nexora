const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

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

export interface CustomerListItem {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
  total_tickets: number;
  open_tickets: number;
  last_seen: string | null;
}

export interface PaginatedCustomers {
  items: CustomerListItem[];
  total: number;
  skip: number;
  limit: number;
}

export interface CustomerStats {
  lifetime_tickets: number;
  open_issues: number;
  resolution_rate: number | null;
  avg_response_seconds: number | null;
}

export interface CustomerDetail {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
  stats: CustomerStats;
}

export interface CustomerTicket {
  id: string;
  subject: string;
  status: string;
  priority: string;
  created_at: string;
}

export interface CustomerChatSummary {
  id: string;
  status: string;
  created_at: string;
  message_count: number;
}

export interface CustomerNote {
  id: string;
  body: string;
  author_id: string;
  author_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface TimelineItem {
  type: "ticket_created" | "chat_started" | "note_added" | "automation_triggered" | "event";
  timestamp: string;
  data: Record<string, unknown>;
}

export interface CustomerListParams {
  q?: string;
  status?: "active" | "inactive";
  has_open_tickets?: boolean;
  date_from?: string;
  date_to?: string;
  sort?: string;
  order?: "asc" | "desc";
  skip?: number;
  limit?: number;
}

export function listCustomers(params: CustomerListParams = {}): Promise<PaginatedCustomers> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") query.set(k, String(v));
  });
  const qs = query.toString();
  return request<PaginatedCustomers>(`/customers/${qs ? `?${qs}` : ""}`);
}

export function getCustomer(id: string): Promise<CustomerDetail> {
  return request<CustomerDetail>(`/customers/${id}`);
}

export function getCustomerTickets(id: string): Promise<CustomerTicket[]> {
  return request<CustomerTicket[]>(`/customers/${id}/tickets`);
}

export function getCustomerChats(id: string): Promise<CustomerChatSummary[]> {
  return request<CustomerChatSummary[]>(`/customers/${id}/chats`);
}

export function getCustomerTimeline(id: string): Promise<TimelineItem[]> {
  return request<TimelineItem[]>(`/customers/${id}/timeline`);
}

export function listCustomerNotes(id: string): Promise<CustomerNote[]> {
  return request<CustomerNote[]>(`/customers/${id}/notes`);
}

export function createCustomerNote(id: string, body: string): Promise<CustomerNote> {
  return request<CustomerNote>(`/customers/${id}/notes`, { method: "POST", body: JSON.stringify({ body }) });
}

export function updateCustomerNote(customerId: string, noteId: string, body: string): Promise<CustomerNote> {
  return request<CustomerNote>(`/customers/${customerId}/notes/${noteId}`, { method: "PATCH", body: JSON.stringify({ body }) });
}

export function deleteCustomerNote(customerId: string, noteId: string): Promise<void> {
  return request<void>(`/customers/${customerId}/notes/${noteId}`, { method: "DELETE" });
}