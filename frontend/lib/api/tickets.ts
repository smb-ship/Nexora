import { apiFetch } from "@/lib/api/client";
import type {
  Ticket,
  TicketDetail,
  TicketCreateInput,
  TicketUpdateInput,
  TicketCommentCreateInput,
  TicketComment,
  TicketListFilters,
  InboxCounts,
} from "@/types/ticket";

export async function listTickets(filters: TicketListFilters = {}): Promise<Ticket[]> {
  const params = new URLSearchParams();
  if (filters.view) params.set("view", filters.view);
  if (filters.status) params.set("status", filters.status);
  if (filters.priority) params.set("priority", filters.priority);
  if (filters.assigned_to) params.set("assigned_to", filters.assigned_to);
  if (filters.search) params.set("search", filters.search);
  if (filters.unread !== undefined) params.set("unread", String(filters.unread));
  if (filters.archived !== undefined) params.set("archived", String(filters.archived));
  if (filters.skip !== undefined) params.set("skip", String(filters.skip));
  if (filters.limit !== undefined) params.set("limit", String(filters.limit));

  const qs = params.toString();
  return apiFetch<Ticket[]>(`/tickets/${qs ? `?${qs}` : ""}`);
}

export async function getTicket(id: string): Promise<TicketDetail> {
  return apiFetch<TicketDetail>(`/tickets/${id}`);
}

export async function createTicket(payload: TicketCreateInput): Promise<Ticket> {
  return apiFetch<Ticket>("/tickets/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateTicket(id: string, payload: TicketUpdateInput): Promise<Ticket> {
  return apiFetch<Ticket>(`/tickets/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteTicket(id: string): Promise<void> {
  await apiFetch<void>(`/tickets/${id}`, { method: "DELETE" });
}

export async function addTicketComment(id: string, payload: TicketCommentCreateInput): Promise<TicketComment> {
  return apiFetch<TicketComment>(`/tickets/${id}/comments`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function markTicketRead(id: string): Promise<void> {
  await apiFetch<void>(`/tickets/${id}/read`, { method: "POST" });
}

export async function getInboxCounts(): Promise<InboxCounts> {
  return apiFetch<InboxCounts>("/tickets/inbox/counts");
}